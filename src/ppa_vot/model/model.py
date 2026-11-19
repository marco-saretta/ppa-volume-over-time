import logging
from types import SimpleNamespace

import gurobipy as gp
import numpy as np

log = logging.getLogger(__name__)


class BilevelModel:
    def __init__(self, config, data):
        self.cfg = config
        self.data = data
        self.configure_model()
        self.add_v()
        self.add_cons()
        self.add_objective()
        if data.guess:
            self.add_start()

    def configure_model(self):
        solver_dict = self.cfg.simulations.solver
        env = gp.Env(empty=True)
        env.setParam("LogToConsole", 0)
        env.start()
        self.m = gp.Model(env=env)

        # solver params
        self.m.setParam("MIPGap", solver_dict.MIPGap)
        self.m.setParam("NumericFocus", solver_dict.NumericFocus)
        self.m.setParam("FeasibilityTol", solver_dict.FeasibilityTol)
        self.m.setParam("OptimalityTol", solver_dict.OptimalityTol)

        log.info("model setup")

    def add_v(self):
        data = self.data
        self.v = SimpleNamespace()  # all decision variables
        INF = gp.GRB.INFINITY

        # Bargaining variables
        # surplus in [epsilon, W_max]: no contract creates more than W_max (see DataLoader)
        self.v.w_G = self.m.addVar(lb=data.epsilon, ub=data.W_max, name="w_G")
        self.v.w_L = self.m.addVar(lb=data.epsilon, ub=data.W_max, name="w_L")
        # ln w, for the NBS objective only
        if data.objective == "nbs":
            ln_lb, ln_ub = np.log(data.epsilon), np.log(data.W_max)
            self.v.ln_w_G = self.m.addVar(lb=ln_lb, ub=ln_ub, name="ln_w_G")
            self.v.ln_w_L = self.m.addVar(lb=ln_lb, ub=ln_ub, name="ln_w_L")
        self.v.u_G = self.m.addVar(lb=-INF, name="u_G")  # mean-CVaR utility
        self.v.u_L = self.m.addVar(lb=-INF, name="u_L")
        self.v.phi_G = self.m.addMVar(data.n_Omega, lb=-INF, name="phi_G")  # net earnings
        self.v.phi_L = self.m.addMVar(data.n_Omega, lb=-INF, name="phi_L")

        # Contract variables
        self.v.V = self.m.addVar(lb=data.volume_lower, ub=data.volume_upper, name="V")
        # z = S V; the strike bounds become constraints on z and V, S = z / V after the solve
        self.v.aux_sv = self.m.addVar(lb=-INF, name="aux_sv")
        self.v.q = self.m.addMVar(
            (data.n_H, data.n_T, data.n_Omega), lb=data.quota_lower, ub=data.quota_upper, name="q"
        )

        # Dual variables of the lower level (V2 designs only), bounded by the week's prices:
        # rho = price of the last hour used, so a valid rho lies between the week's lowest and
        # highest price; then mu_cap, mu_floor never exceed the week's price spread
        lam = data.sc_prices
        spread = np.broadcast_to(lam.max(axis=0) - lam.min(axis=0), lam.shape)  # (h, t, omega)
        self.v.rho = self.m.addMVar(
            (data.n_T, data.n_Omega), lb=lam.min(axis=0), ub=lam.max(axis=0), name="rho"
        )  # volume
        self.v.mu_u = self.m.addMVar(lam.shape, lb=0, ub=spread, name="mu_u")  # cap
        self.v.mu_l = self.m.addMVar(lam.shape, lb=0, ub=spread, name="mu_l")  # floor

        # Binary expansion of V (eq:sl_vexp): V = delta_V sum_k 2^k z_k, xi_k = rho z_k
        if data.binary:
            n_K = int(np.ceil(np.log2(data.volume_upper / data.delta_V + 1)))  # digits
            self.weights = data.delta_V * 2.0 ** np.arange(n_K)  # delta_V 2^k, shape (n_K,)
            self.v.z = self.m.addMVar(n_K, vtype=gp.GRB.BINARY, name="z")
            self.v.xi = self.m.addMVar((n_K, data.n_T, data.n_Omega), lb=-INF, name="xi")
            log.info("binary expansion: %d digits, delta_V = %g", n_K, data.delta_V)

        # Risk aversion variables (CVaR)
        self.v.zeta_G = self.m.addVar(lb=-INF, name="zeta_G")
        self.v.zeta_L = self.m.addVar(lb=-INF, name="zeta_L")
        self.v.eta_G = self.m.addMVar(data.n_Omega, lb=0, name="eta_G")
        self.v.eta_L = self.m.addMVar(data.n_Omega, lb=0, name="eta_L")

        log.info("variables added")

    def add_cons(self):
        v, data = self.v, self.data

        # Surpluses
        self.m.addConstr(v.w_G == v.u_G - data.d_G)
        self.m.addConstr(v.w_L == v.u_L - data.d_L)

        # Surplus log equivalence (NBS objective only)
        if data.objective == "nbs":
            self.m.addGenConstrLog(v.w_G, v.ln_w_G)
            self.m.addGenConstrLog(v.w_L, v.ln_w_L)

        # Utilities
        self.m.addConstr(
            v.u_G
            == (1 - data.beta_G) * data.pi @ v.phi_G
            + data.beta_G * (v.zeta_G - 1 / (1 - data.alpha_G) * data.pi @ v.eta_G)
        )
        self.m.addConstr(
            v.u_L
            == (1 - data.beta_L) * data.pi @ v.phi_L
            + data.beta_L * (v.zeta_L - 1 / (1 - data.alpha_L) * data.pi @ v.eta_L)
        )
        # CVaR: shortfall below zeta, one row per scenario
        self.m.addConstr(v.eta_G >= v.zeta_G - v.phi_G)
        self.m.addConstr(v.eta_L >= v.zeta_L - v.phi_L)

        # Net eargnings
        # numpy (n_Omega,): merchant revenue and cost
        spot_G = (data.sc_prices * data.sc_p_G).sum(axis=(0, 1))
        spot_L = (data.sc_prices * data.sc_p_L).sum(axis=(0, 1))
        # (n_Omega,): PPA energy valued at the spot price
        lam_q = (data.sc_prices * v.q).sum(axis=0).sum(axis=0)
        self.m.addConstr(v.phi_G == data.n_T * v.aux_sv + spot_G - lam_q)
        self.m.addConstr(v.phi_L == -data.n_T * v.aux_sv - spot_L + lam_q)

        # weekly volume equivalent
        self.m.addConstr(v.q.sum(axis=0) == v.V)

        # Strike bounds times V (eq:sl_strike): S_lo V <= z <= S_hi V
        self.m.addConstr(v.aux_sv >= data.strike_lower * v.V)
        self.m.addConstr(v.aux_sv <= data.strike_upper * v.V)

        # Dual feasibility
        self.m.addConstr(data.sc_prices - v.rho + v.mu_u - v.mu_l == 0)

        # Strong duality THAT NAUGHTY CONSTRAINT: rho V is linearised or left bilinear
        if data.binary:
            lam_min = data.sc_prices.min(axis=0)  # (t, omega), = lb of rho (eq:sl_rho_bounds)
            lam_max = data.sc_prices.max(axis=0)  # (t, omega), = ub of rho
            z = v.z.reshape(-1, 1, 1)  # (k, 1, 1), broadcasts against xi (k, t, omega)
            self.m.addConstr(v.V == self.weights @ v.z)  # eq:sl_vexp
            self.m.addConstr(v.xi >= lam_min * z)  # eq:sl_xi_z
            self.m.addConstr(v.xi <= lam_max * z)
            self.m.addConstr(v.xi >= v.rho - lam_max * (1 - z))  # eq:sl_xi_rho
            self.m.addConstr(v.xi <= v.rho - lam_min * (1 - z))
            rho_V = (self.weights.reshape(-1, 1, 1) * v.xi).sum(axis=0)  # (t, omega), linear
        else:
            rho_V = v.rho * v.V  # bilinear: Gurobi solves it as a nonconvex MIQCP
        self.m.addConstr(
            (data.sc_prices * v.q).sum(axis=0)
            == rho_V - data.quota_upper * v.mu_u.sum(axis=0) + data.quota_lower * v.mu_l.sum(axis=0)
        )
        log.info("constraints added (binary expansion: %s)", data.binary)

    def add_objective(self):
        v, tau_G = self.v, self.data.tau_G
        if self.data.objective == "nbs":
            expr = tau_G * v.ln_w_G + (1 - tau_G) * v.ln_w_L
        else:
            # joint surplus: the strike is a transfer, so the NBS volume maximises W;
            # the exporter sets the strike afterwards from w_G = tau_G W
            expr = v.w_G + v.w_L
        self.m.setObjective(expr=expr, sense=gp.GRB.MAXIMIZE)
        log.info("objective: %s", self.data.objective)

    def add_start(self):
        # Partial MIP start: only S and V are given. Gurobi completes the other variables by
        # solving the model with them fixed, and keeps the result as the first incumbent.
        # It is a starting point, not a constraint: the search still covers the whole range of V.
        # The bounds of the guess are checked in DataLoader.
        data, v = self.data, self.v
        V, S = data.guess_volume, data.guess_strike
        if data.binary:
            # V must be on the grid: V = delta_V * n, n written in binary digits z_k
            n = int(round(V / data.delta_V))
            V = n * data.delta_V
            v.z.Start = [(n >> k) & 1 for k in range(len(self.weights))]
        v.V.Start = V
        # a wrong strike makes the start infeasible (w_G or w_L below epsilon), so it is optional
        if S is not None:
            v.aux_sv.Start = S * V  # aux_sv = S V
        log.info("MIP start: V = %g, S = %s", V, S)

    def solve(self):
        # self.m.Params.TimeLimit = 1800  # seconds; the exporter keeps the best solution found
        self.m.optimize()
        m = self.m
        # Runtime is wall clock (inflated by suspends); Work is deterministic, use it to compare
        log.info(
            "Gurobi (binary expansion: %s): status %d, runtime %.1f s, work %.1f units, "
            "%d binaries, %d constraints",
            self.data.binary,
            m.Status,
            m.Runtime,
            m.Work,
            m.NumBinVars,
            m.NumConstrs,
        )
        if m.SolCount > 0:
            gap = m.MIPGap if m.IsMIP else 0.0
            log.info(
                "objective %.6f, gap %.2e, V %.2f, S %.3f",
                m.ObjVal,
                gap,
                self.v.V.X,
                self.v.aux_sv.X / max(self.v.V.X, 1e-9),
            )
