"""Table of every diagnostic run, checked against the exact sweep W(V).

The sweep uses that, for V2-G, the generator fills the cheapest hours: W(V) is exact at every V
and does not depend on the strike (notes/misc/checks_2026-11-16/README.md).

Usage: uv run python scripts/summarize_diagnostics.py [ROOT]      (default: multirun/binary_diag)

Columns
  settings  overrides that differ from the base settings of scripts/run_binary_diagnostics.sh
  st        Gurobi status: 2 optimal, 9 time limit, 11 interrupted
  V, W      what the run returned (W = w_G + w_L)
  sw        'ok' if the exact W at the run's V equals W (model and sweep agree at that point)
  V*, W*    best V on the run's own grid (integers in [volume_lower, volume_upper] for binary)
  loss      (W* - W) / W*
  bound     'ok' if Gurobi's best bound is at least the true optimum. 'WRONG' if it is below:
            Gurobi discarded a region that holds a better solution, so its proof is invalid.
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
from omegaconf import OmegaConf

from ppa_vot.data_ops import DataLoader

# overrides not shown: the same in every run
HIDE = {
    "simulations.data.scenarios",
    "simulations.data.weeks",
    "simulations.model.binary_expansion.do",
    "simulations.model.contract.guess.do",
    "simulations.solver.MIPGap",
    "simulations.solver.TimeLimit",
}
# overrides not shown when at the base value
BASE = {
    "simulations.solver.NumericFocus": "0",
    "simulations.solver.FeasibilityTol": "1e-6",
    "simulations.solver.OptimalityTol": "1e-6",
    "simulations.solver.Cuts": "-1",
    "simulations.solver.Presolve": "-1",
    "simulations.model.contract.volume_lower": "0",
    "simulations.model.contract.volume_upper": "600",
}


def label(overrides):
    out = []
    for o in overrides:
        k, v = o.split("=", 1)
        if k == "simulations.model.binary_expansion.do" and v.lower() == "false":
            out.append("bilinear")
        elif k not in HIDE and BASE.get(k) != v:
            out.append(f"{k.split('.')[-1]}={v}")
    return " ".join(out)


def load_cfg(run):
    cfg = OmegaConf.load(run / ".hydra/config.yaml")
    cfg.paths.data = str(Path.cwd() / "data")
    contract = cfg.simulations.model.contract
    if "guess" not in contract:  # runs saved before the guess option
        contract.guess = {"do": False, "strike": None, "volume": None}
    return cfg


def sweep(cfg):
    d = DataLoader(cfg=cfg)
    lam, PG, PL = d.sc_prices, d.sc_p_G, d.sc_p_L  # (h, t, w)
    qf, qc, H = d.quota_lower, d.quota_upper, d.n_H
    s = np.sort(lam, axis=0)  # cheapest hours first, per (t, w)
    cs = np.vstack([np.zeros((1,) + s.shape[1:]), np.cumsum(s, axis=0)])
    spotG = (lam * PG).sum(axis=(0, 1))
    spotL = (lam * PL).sum(axis=(0, 1))

    def W(V):
        E = V - H * qf
        n = int(np.floor(E / (qc - qf) + 1e-12))
        r = E - n * (qc - qf)
        cost = qf * cs[H] + (qc - qf) * cs[n] + (r * s[min(n, H - 1)] if n < H else 0)
        lq = cost.sum(axis=0)
        return (
            d.mean_cvar(spotG - lq, d.alpha_G, d.beta_G)
            + d.mean_cvar(-spotL + lq, d.alpha_L, d.beta_L)
            - d.d_G
            - d.d_L
        )

    lo = max(H * qf, d.volume_lower)
    if d.binary:
        grid = np.arange(np.ceil(lo / d.delta_V) * d.delta_V, d.volume_upper + 1e-9, d.delta_V)
    else:
        grid = np.arange(np.ceil(lo * 100) / 100, d.volume_upper + 1e-9, 0.01)
    Wg = np.array([W(v) for v in grid])
    return W, grid[Wg.argmax()], Wg.max(), d.tau_G


def main(root):
    root = Path(root)
    head = (
        f"{'run':40s} {'settings':58s} {'st':>3s} {'V':>7s} {'W':>9s} {'sw':>3s} "
        f"{'V*':>7s} {'W*':>9s} {'loss':>7s} {'bound':>6s} {'gap':>8s} {'time':>7s} {'work':>6s}"
    )
    print(head)
    print("-" * len(head))
    for run in sorted(p.parent for p in root.rglob(".hydra") if "_incomplete" not in p.parts):
        name = str(run.relative_to(root))
        lab = label(OmegaConf.load(run / ".hydra/overrides.yaml"))
        sc_file = run / "scalars.json"
        if not sc_file.exists():
            print(f"{name:40s} {lab:58s} no result (running, or stopped before a solution)")
            continue
        sc = json.loads(sc_file.read_text())
        cfg = load_cfg(run)
        W, Vs, Ws, tau = sweep(cfg)
        V, Wr = sc["V"], sc["w_G"] + sc["w_L"]
        # best objective value on the grid, in the units of the run's objective
        if cfg.simulations.model.NBS.objective == "nbs":
            best = tau * np.log(tau * Ws) + (1 - tau) * np.log((1 - tau) * Ws)
        else:
            best = Ws
        bound = sc.get("bound")
        bound_ok = "-" if bound is None else ("ok" if bound >= best - 1e-7 * abs(best) else "WRONG")
        sw_ok = "ok" if abs(W(V) - Wr) < 1e-2 else "NO"
        m = re.findall(r"runtime ([\d.]+) s, work ([\d.]+) units", (run / "main.log").read_text())
        rt, wk = (float(m[-1][0]), float(m[-1][1])) if m else (np.nan, np.nan)
        print(
            f"{name:40s} {lab:58s} {sc.get('status', '?'):>3} {V:7.2f} {Wr:9.2f} {sw_ok:>3s} "
            f"{Vs:7.2f} {Ws:9.2f} {100 * (Ws - Wr) / Ws:6.3f}% {bound_ok:>6s} "
            f"{sc.get('gap', 0):8.1e} {rt:6.0f}s {wk:6.0f}"
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "multirun/binary_diag")
