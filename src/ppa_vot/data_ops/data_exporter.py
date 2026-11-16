import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import gurobipy as gp
import numpy as np
from omegaconf import DictConfig

log = logging.getLogger(__name__)


@dataclass
class DataExporter:
    """Save the solution of every variable in model.v to the Hydra run folder.

    scalars.json  scalar variables, S = aux_sv / V, solver status, objective, runtime
    arrays.npz    array variables with their model shape, e.g. q [h, t, omega]
                  (load with: res = np.load("arrays.npz"); res["q"])
    """

    cfg: DictConfig = field(repr=False)
    model: object = field(repr=False)  # BilevelModel after solve()

    def __post_init__(self):
        self.out_dir = Path(self.cfg.paths.run)
        self.export()

    def export(self):
        m = self.model.m
        if m.SolCount == 0:
            log.warning("No solution found (Gurobi status %d): nothing exported", m.Status)
            return
        if m.Status != gp.GRB.OPTIMAL:  # e.g. time limit: export the best solution found
            log.warning("Gurobi status %d: exporting the best solution found", m.Status)

        scalars, arrays = {}, {}
        for name, var in vars(self.model.v).items():
            value = var.X  # float for addVar, ndarray for addMVar
            if isinstance(value, np.ndarray):
                arrays[name] = value
            else:
                scalars[name] = value

        V = scalars["V"]
        scalars["S"] = scalars["aux_sv"] / V if V > 1e-9 else float("nan")  # strike from z = S V
        # exact NBS split: w_G = tau_G W. u_G moves one-for-one with n_T * aux_sv (mean-CVaR is
        # translation equivariant), so the payment is shifted to reach it. With objective 'joint'
        # this IS the strike (the solver's split is arbitrary); with 'nbs' it removes the gap noise.
        data = self.model.data
        W = scalars["w_G"] + scalars["w_L"]
        aux_sv_nbs = scalars["aux_sv"] + (data.tau_G * W - scalars["w_G"]) / data.n_T
        scalars["S_nbs"] = aux_sv_nbs / V if V > 1e-9 else float("nan")
        if data.objective == "joint":
            scalars["S_solver"] = scalars["S"]
            scalars["S"] = scalars["S_nbs"]
            scalars["w_G"], scalars["w_L"] = data.tau_G * W, (1 - data.tau_G) * W
        if not data.strike_lower <= scalars["S_nbs"] <= data.strike_upper:
            log.warning(
                "NBS strike %.3f outside the strike bounds: the split is not exact",
                scalars["S_nbs"],
            )
        scalars.update(status=m.Status, objective=m.ObjVal, runtime=m.Runtime)
        try:
            scalars.update(bound=m.ObjBound, gap=m.MIPGap)  # only for models solved by branching
        except (gp.GurobiError, AttributeError):  # plain LP: no bound or gap
            pass

        with open(self.out_dir / "scalars.json", "w") as f:
            json.dump(scalars, f, indent=2)
        np.savez(self.out_dir / "arrays.npz", **arrays)
        log.info("Exported %d scalars and %d arrays to %s", len(scalars), len(arrays), self.out_dir)
