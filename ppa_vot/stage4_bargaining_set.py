"""Stage 4: the bargaining set with and without risk aversion.

Reproduces notes/why-cvar-and-mdp.md, Stages 3 and 4. Sweeps the contracted
volume M and the strike price lambda, computes each party's utility from the
scenario profits, and plots the achievable gains (u^S - d^S, u^B - d^B).

Risk neutral: every contract lands on the line x + y = 0, so the only
              individually rational point is the origin. No contract.
With CVaR:    the set is a triangle of area, the Pareto frontier is
              x + y = 300 at the perfect hedge M = P, and Nash picks (150, 150).

A denotes the risk aversion weight (A = 0 is risk neutral, A = 1 is pure CVaR).
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

FIGDIR = Path(__file__).resolve().parents[1] / "notes" / "figures"

# Scenario data of Stage 3: one hour, two equiprobable price outcomes.
LAMBDA_DA = np.array([20.0, 80.0])
PROBS = np.array([0.5, 0.5])
P = 10.0  # seller production, MWh
D = 10.0  # buyer demand, MWh
BETA = 0.5  # CVaR confidence level


def cvar(profit, probs, beta):
    """CVaR_beta of a profit vector: the mean of the worst (1 - beta) probability mass.

    Larger is better, because the argument is a profit rather than a loss.
    """
    order = np.argsort(profit)
    p, w = np.asarray(profit)[order], np.asarray(probs)[order]
    tail = 1.0 - beta
    mass_before = np.cumsum(w) - w
    take = np.minimum(w, np.clip(tail - mass_before, 0.0, None))
    return float(p @ take / tail)


def utility(profit, probs, A, beta=BETA):
    """u = (1 - A) E[profit] + A CVaR_beta(profit)."""
    return (1.0 - A) * float(np.asarray(probs) @ profit) + A * cvar(profit, probs, beta)


def profits(M, lam):
    """Scenario profits of seller and buyer for volume M at strike price lam."""
    phi_S = lam * M + LAMBDA_DA * (P - M)
    phi_B = -lam * M + LAMBDA_DA * (M - D)
    return phi_S, phi_B


def disagreement(A_S, A_B):
    """Utilities of the no contract outcome, M = 0."""
    return (
        utility(LAMBDA_DA * P, PROBS, A_S),
        utility(-LAMBDA_DA * D, PROBS, A_B),
    )


def gains(M, lam, A_S, A_B, d=None):
    """(x, y) = (u^S - d^S, u^B - d^B) for one contract."""
    d_S, d_B = disagreement(A_S, A_B) if d is None else d
    phi_S, phi_B = profits(M, lam)
    return utility(phi_S, PROBS, A_S) - d_S, utility(phi_B, PROBS, A_B) - d_B


def sweep(A_S, A_B, n_M=41, n_lam=121, M_max=20.0, lam_range=(0.0, 120.0)):
    """All achievable (x, y) over a grid of contracted volume and strike price."""
    d = disagreement(A_S, A_B)
    pts = [
        gains(M, lam, A_S, A_B, d)
        for M in np.linspace(0.0, M_max, n_M)
        for lam in np.linspace(*lam_range, n_lam)
    ]
    return np.array(pts)


def panel(ax, A_S, A_B, title):
    xy = sweep(A_S, A_B)
    x, y = xy[:, 0], xy[:, 1]

    # The bargaining set: achievable and individually rational for both parties.
    ir = (x >= -1e-9) & (y >= -1e-9)
    W_max = (x + y).max()

    if ir.sum() > 1 and W_max > 1e-9:
        ax.scatter(x[ir], y[ir], s=6, color="tab:blue", alpha=0.25, label="bargaining set")
        # Pareto frontier: the outermost line x + y = W_max.
        ax.plot(
            [0, W_max], [W_max, 0], color="tab:blue", lw=2, label=rf"frontier $x+y={W_max:.0f}$"
        )
        # Nash product contours, tangent to the frontier at the solution.
        gx, gy = np.meshgrid(np.linspace(1, W_max, 200), np.linspace(1, W_max, 200))
        ax.contour(
            gx,
            gy,
            gx * gy,
            levels=[(W_max / 2) ** 2 * f for f in (0.25, 0.5, 0.8)],
            colors="tab:orange",
            linewidths=0.8,
            alpha=0.7,
        )
        nash = xy[ir][np.argmax(x[ir] * y[ir])]
        ax.scatter(
            *nash,
            color="tab:red",
            zorder=6,
            s=70,
            marker="*",
            label=f"Nash ({nash[0]:.0f}, {nash[1]:.0f})",
        )
    else:
        ax.plot([-300, 300], [300, -300], color="tab:blue", lw=2, label=r"frontier $x+y=0$")
        ax.scatter(
            [0],
            [0],
            color="tab:red",
            zorder=6,
            s=70,
            marker="*",
            label="only IR point: no contract",
        )

    ax.axhline(0, color="0.6", lw=0.8)
    ax.axvline(0, color="0.6", lw=0.8)
    ax.scatter([0], [0], color="black", zorder=5, s=30, label="disagreement point")
    ax.set_xlabel(r"seller gain  $x = u^S - d^S$  [EUR]")
    ax.set_ylabel(r"buyer gain  $y = u^B - d^B$  [EUR]")
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    ax.set_xlim(-120, 340)
    ax.set_ylim(-120, 340)
    return W_max


def report(A_S, A_B):
    """Print the numbers the notes quote by hand."""
    d_S, d_B = disagreement(A_S, A_B)
    print(f"\nA_S = {A_S}, A_B = {A_B}:  d^S = {d_S:.1f}, d^B = {d_B:.1f}")
    print(f"{'M':>5} {'lambda':>7} {'x':>8} {'y':>8} {'W':>8}")
    for M, lam in [(0, 50), (5, 50), (10, 35), (10, 50), (10, 65), (15, 50), (20, 50)]:
        x, y = gains(M, lam, A_S, A_B)
        print(f"{M:>5} {lam:>7} {x:>8.1f} {y:>8.1f} {x + y:>8.1f}")


def risk_aversion_figure():
    """How the frontier, the surplus and the strike price depend on risk aversion.

    Verifies the closed forms  W = 300 (A_S + A_B)  and  lambda* = 50 + 15 (A_B - A_S).
    """
    _, axes = plt.subplots(1, 3, figsize=(16, 5))

    # (a) the frontier moves outward, parallel, as risk aversion rises.
    for A in (0.0, 0.25, 0.5, 1.0):
        W = 600.0 * A  # = 300 (A_S + A_B) with A_S = A_B = A
        axes[0].plot([0, W], [W, 0], lw=2, label=f"$A_S=A_B={A}$,  $W={W:.0f}$")
    axes[0].scatter([0], [0], color="black", zorder=5, label="disagreement point")
    axes[0].set_xlabel("seller gain $x$ [EUR]")
    axes[0].set_ylabel("buyer gain $y$ [EUR]")
    axes[0].set_title("(a) frontier translates outward, slope stays $-1$")
    axes[0].set_aspect("equal")

    # (b) the surplus is linear in risk aversion, slope dW/dA_i = 300.
    grid = np.linspace(0, 1, 101)
    for A_B in (0.0, 0.25, 0.5, 1.0):
        W = np.array([sum(gains(10.0, 50.0, a, A_B)) for a in grid])
        axes[1].plot(grid, W, lw=2, label=f"$A_B = {A_B}$")
    axes[1].set_xlabel("$A_S$")
    axes[1].set_ylabel("joint surplus $W$ [EUR]")
    axes[1].set_title(r"(b) $W = 300(A_S + A_B)$,  $\partial W/\partial A_i = 300$")

    # (c) the Nash strike price tilts away from the more risk averse party.
    for A_S in (0.0, 0.5, 1.0):
        lam = 50.0 + 15.0 * (grid - A_S)
        axes[2].plot(grid, lam, lw=2, label=f"$A_S = {A_S}$")
    axes[2].axhline(50, color="0.6", lw=0.8, ls="--")
    axes[2].annotate(r"$\mathbb{E}[\lambda^{DA}] = 50$", (0.02, 50.6), fontsize=9)
    axes[2].set_xlabel("$A_B$")
    axes[2].set_ylabel(r"Nash strike $\lambda^\star$ [EUR/MWh]")
    axes[2].set_title(r"(c) $\lambda^\star = 50 + 15(A_B - A_S)$")

    for ax in axes:
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    plt.tight_layout()

    out = FIGDIR / "stage_4_risk_aversion.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"saved {out}")


def main():
    for A_S, A_B in [(0.0, 0.0), (0.5, 0.5), (0.0, 0.5)]:
        report(A_S, A_B)

    FIGDIR.mkdir(parents=True, exist_ok=True)

    _, axes = plt.subplots(1, 2, figsize=(13, 6.5))
    panel(axes[0], 0.0, 0.0, "Stage 3: risk neutral ($A_S = A_B = 0$)")
    panel(axes[1], 0.5, 0.5, "Stage 4: with CVaR ($A_S = A_B = 0.5$)")
    plt.tight_layout()

    out = FIGDIR / "stage_4_bargaining_set.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"\nsaved {out}")

    risk_aversion_figure()
    plt.show()


if __name__ == "__main__":
    main()
