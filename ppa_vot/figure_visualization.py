"""
Barter set figure: decision-space box (M, S) mapped to the utility possibility
set U, with the barter set B highlighted inside it.

This is a genuine closed-form example (two-scenario CVaR, symmetric price
risk, asymmetric risk aversion), not a hand-drawn schematic: every curve is
computed from the actual w_G(M,S), w_L(M,S) formulas, so the connector slope
of exactly -1 and the kink at M = P = D = Q are real model properties, not
artistic choices.

Requires: numpy, matplotlib
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle

# from matplotlib.lines import Line2D


class CasesPlotter:
    def __init__(self, plot_scale=1.5):
        self.Q = 10.0  # production P = demand D = Q
        self.lam_bar = 50.0  # E[lambda]
        self.rho = 30.0  # symmetric CVaR risk premium, rho = (lambda_H - lambda_L)/2
        self.A_G = 0.4
        self.A_L = 0.6  # risk aversion, generator / load
        self.S_R = 20
        self.S_U = 80.0  # strike price bounds
        self.M_U = 20.0  # contract volume upper bound (M_R = 0)

        self.plot_scale = plot_scale

        self.set_colors()
        self.gen_params()
        self.compute_key_points()

    def wG(self, M, S):
        """Generator surplus w_G(M,S) = u_G - d_G, relative to disagreement point."""
        return M * (S - self.lam_bar) + self.A_G * self.rho * (self.Q - np.abs(self.Q - M))

    def wL(self, M, S):
        """Load surplus w_L(M,S) = u_L - d_L, relative to disagreement point."""
        return M * (self.lam_bar - S) + self.A_L * self.rho * (self.Q - np.abs(self.Q - M))

    def gen_params(self):
        """Sweep M at S = S^R and S = S^U to trace V1, V2, plus the crossing point at M* = Q."""
        self.M_grid = np.linspace(0, self.M_U, 400)
        self.V1 = np.column_stack(
            [self.wG(self.M_grid, self.S_R), self.wL(self.M_grid, self.S_R)]
        )  # S = S^R sweep
        self.V2 = np.column_stack(
            [self.wG(self.M_grid, self.S_U), self.wL(self.M_grid, self.S_U)]
        )  # S = S^U sweep

        # The kink (and, for this simple two-scenario model, the exact slope-crossing
        # point M*) sits at M = Q, the physical full hedge.
        self.M_star = self.Q
        self.V1_star = np.array([self.wG(self.M_star, self.S_R), self.wL(self.M_star, self.S_R)])
        self.V2_star = np.array([self.wG(self.M_star, self.S_U), self.wL(self.M_star, self.S_U)])

    @staticmethod
    def line_axis_crossing(p0, p1, axis, value=0.0):
        """Intersection of segment p0-p1 with w_G = value (axis=0) or w_L = value (axis=1)."""
        t = (value - p0[axis]) / (p1[axis] - p0[axis])
        return p0 + t * (p1 - p0)

    def compute_key_points(self):
        """I, J: intersections of the M* connector with the w_G = 0 and w_L = 0 axes."""
        self.I = self.line_axis_crossing(self.V1_star, self.V2_star, axis=0)  # crosses w_G = 0
        self.J = self.line_axis_crossing(self.V1_star, self.V2_star, axis=1)  # crosses w_L = 0
        self.zeta = np.array([0.0, 0.0])

    # -----------------------------------------------------------------------
    # Colours (consistent across both panels: same colour = same edge/curve)
    # -----------------------------------------------------------------------
    def set_colors(self):
        self.c_teal = "#1D9E75"  # S = S^R  -> V1
        self.c_coral = "#D85A30"  # S = S^U  -> V2
        self.c_amber = "#BA7517"  # M = M^U  -> straight connector at the boundary
        self.c_purple = "#534AB7"  # M = M*   -> straight connector at the crossing (defines B)
        self.c_grey = "#5F5E5A"  # M = 0    -> collapses to the disagreement point

    # ---------------------------- Panel 1: decision space ----------------------
    def plot_decision_space(self, ax):
        ax.add_patch(
            Rectangle(
                (0, self.S_R),
                self.M_U,
                self.S_U - self.S_R,
                fill=False,
                edgecolor="0.6",
                linewidth=0.8,
            )
        )
        ax.plot(
            [0, 0],
            [self.S_R, self.S_U],
            color=self.c_grey,
            linewidth=2.5,
            linestyle="--",
            label="M = 0 (collapses to disagreement point)",
        )
        ax.plot(
            [0, self.M_U],
            [self.S_R, self.S_R],
            color=self.c_teal,
            linewidth=2.5,
            label="S = S$^R$  ->  V1",
        )
        ax.plot(
            [0, self.M_U],
            [self.S_U, self.S_U],
            color=self.c_coral,
            linewidth=2.5,
            label="S = S$^U$  ->  V2",
        )
        ax.plot(
            [self.M_U, self.M_U],
            [self.S_R, self.S_U],
            color=self.c_amber,
            linewidth=2.5,
            label="M = M$^U$  ->  boundary connector",
        )
        ax.plot(
            [self.M_star, self.M_star],
            [self.S_R, self.S_U],
            color=self.c_purple,
            linewidth=1.5,
            linestyle=":",
            label="M = M*  ->  crossing connector (defines B)",
        )
        ax.set_xlabel("Contract volume $M$")
        ax.set_ylabel("Strike price $S$")
        ax.set_title("Decision space")
        ax.set_xlim(-1, self.M_U + 1)
        ax.set_ylim(self.S_R - 5, self.S_U + 5)
        ax.spines[["top", "right"]].set_visible(False)

    # ---------------------------- Panel 2: utility space ------------------------
    def plot_utility_space(self, ax):
        # Grey wedge U: V1 curve, boundary connector, V2 curve reversed, back to origin
        wedge_pts = np.vstack([self.V1, self.V2[::-1]])
        ax.add_patch(Polygon(wedge_pts, closed=True, facecolor="0.85", edgecolor="none", zorder=1))

        ax.plot(self.V1[:, 0], self.V1[:, 1], color=self.c_teal, linewidth=2.2, zorder=3)
        ax.plot(self.V2[:, 0], self.V2[:, 1], color=self.c_coral, linewidth=2.2, zorder=3)
        ax.plot(
            [self.V1[-1, 0], self.V2[-1, 0]],
            [self.V1[-1, 1], self.V2[-1, 1]],
            color=self.c_amber,
            linewidth=2.2,
            zorder=3,
        )
        # ax.plot([self.V1_star[0], self.V2_star[0]], [self.V1_star[1], self.V2_star[1]],
        #         color=self.c_purple, linewidth=1.4, linestyle=":", zorder=3)
        #
        # # Red barter set triangle: zeta, I, J
        # ax.add_patch(Polygon([self.zeta, self.I, self.J], closed=True, facecolor="#E24B4A",
        #                       edgecolor="#A32D2D", alpha=0.85, zorder=4))
        #
        # ax.axhline(0, color="0.75", linewidth=0.6, zorder=0)
        # ax.axvline(0, color="0.75", linewidth=0.6, zorder=0)
        #
        # ax.scatter(*self.zeta, color="black", s=25, zorder=5)
        # ax.annotate(r"$\zeta = (d_G, d_L)$", self.zeta, textcoords="offset points",
        #             xytext=(-45, -12), fontsize=10)
        # ax.annotate("$X$", self.V1_star, textcoords="offset points", xytext=(-14, 4), fontsize=10)
        # ax.annotate("$Y$", self.V2_star, textcoords="offset points", xytext=(6, -4), fontsize=10)
        # ax.annotate("$I$", self.I, textcoords="offset points", xytext=(-16, 2), fontsize=10)
        # ax.annotate("$J$", self.J, textcoords="offset points", xytext=(2, -14), fontsize=10)
        # ax.annotate("$V_1$", self.V1[-1], textcoords="offset points", xytext=(-25, 5),
        #             fontsize=11, color=self.c_teal)
        # ax.annotate("$V_2$", self.V2[-1], textcoords="offset points", xytext=(5, -5),
        #             fontsize=11, color=self.c_coral)
        # ax.annotate("$U$", (400, 300), fontsize=12)
        # ax.annotate("$B$", (60, 100), fontsize=12, color="#A32D2D")
        #
        # ax.set_xlabel(r"$u_G - d_G$")
        # ax.set_ylabel(r"$u_L - d_L$")
        # ax.set_title("Utility space")
        # ax.spines[["top", "right"]].set_visible(False)
        # ax.set_aspect("equal", adjustable="datalim")

    def legend_handles(self):
        pass
        # return [
        #     Line2D([0], [0], color=self.c_grey, lw=2.5, ls="--",
        #             label="M = 0 (collapses to $\\zeta$)"),
        #     Line2D([0], [0], color=self.c_teal, lw=2.5, label=r"$V_1$: $S=S^R$ sweep"),
        #     Line2D([0], [0], color=self.c_coral, lw=2.5, label=r"$V_2$: $S=S^U$ sweep"),
        #     Line2D([0], [0], color=self.c_amber, lw=2.5, label=r"connector at $M^U$"),
        #     Line2D([0], [0], color=self.c_purple, lw=1.5, ls=":", label=r"connector at $M^*$"),
        # ]

    def plot(self):
        fig, axes = plt.subplots(1, 4, figsize=(8 * self.plot_scale, 2 * self.plot_scale))

        self.plot_decision_space(axes[0])  # First subplot
        self.plot_utility_space(axes[1])
        # axes[2], axes[3] reserved for the remaining cases (no-agreement / boundary-pinned, ...)

        # fig.legend(handles=self.legend_handles(), loc="lower center", ncol=5, frameon=False,
        #            bbox_to_anchor=(0.5, -0.04), fontsize=9)

        plt.show()
        # plt.tight_layout()
        # plt.savefig("/mnt/user-data/outputs/barter_set_figure.pdf", bbox_inches="tight", dpi=300)
        # plt.savefig("/mnt/user-data/outputs/barter_set_figure.png", bbox_inches="tight", dpi=200)
        # print("Saved.")


if __name__ == "__main__":
    CasesPlotter().plot()
