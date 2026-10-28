import matplotlib.pyplot as plt
import numpy as np


def plot_zero_sum(lambda_DA=50.0, M=10.0, lambda_range=(30, 70)):
    """Stage 2: the bargaining frontier under deterministic prices.

    Sweeps the strike price lambda_PPA at a fixed contracted volume M and
    plots the achievable gains (u^S - d^S, u^B - d^B). See
    notes/why-cvar-and-mdp.md, Stage 1-2: the frontier is the line x + y = 0.
    """
    lambda_PPA = np.linspace(*lambda_range, 200)
    x = M * (lambda_PPA - lambda_DA)  # u^S - d^S
    y = M * (lambda_DA - lambda_PPA)  # u^B - d^B

    _, ax = plt.subplots(figsize=(6, 6))
    ax.plot(x, y, color="tab:blue", lw=2, label=r"frontier ($x+y=0$)")
    ax.axhline(0, color="0.6", lw=0.8)
    ax.axvline(0, color="0.6", lw=0.8)
    ax.scatter([0], [0], color="black", zorder=5, label="disagreement point")

    # the three strike prices worked by hand in the notes
    for lam in (45, 50, 55):
        xi = M * (lam - lambda_DA)
        yi = M * (lambda_DA - lam)
        ax.scatter([xi], [yi], color="tab:red", zorder=5)
        ax.annotate(rf"$\lambda={lam}$", (xi, yi), textcoords="offset points", xytext=(6, 6))

    ax.set_xlabel(r"seller gain  $x = u^S - d^S$  [EUR]")
    ax.set_ylabel(r"buyer gain  $y = u^B - d^B$  [EUR]")
    ax.set_title("Stage 2: bargaining frontier, deterministic prices")
    ax.legend()
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    plt.show()


if __name__ == "__main__":
    plot_zero_sum()
