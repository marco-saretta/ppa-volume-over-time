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

    def configure_model(self):
        env = gp.Env(empty=True)
        env.setParam("LogToConsole", 0)
        env.start()
        self.m = gp.Model(env=env)
        log.info("model setup")

    def add_v(self):
        data = self.data
        self.v = SimpleNamespace()  # all decision variables
        INF = gp.GRB.INFINITY

        # Bargaining variables
        # surplus in [epsilon, W_max]: no contract creates more than W_max (see DataLoader)
        self.v.w_G = self.m.addVar(lb=data.epsilon, ub=data.W_max, name="w_G")
        self.v.w_L = self.m.addVar(lb=data.epsilon, ub=data.W_max, name="w_L")
        # ln w, for the NBS objective
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

        # Surplus log equivalence
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

        # Strong duality THAT NAUGHTY CONSTRAINT
        self.m.addConstr(
            (data.sc_prices * v.q).sum(axis=0)
            == v.rho * v.V
            - data.quota_upper * v.mu_u.sum(axis=0)
            + data.quota_lower * v.mu_l.sum(axis=0)
        )
        log.info("constraints added")

    def add_objective(self):
        self.m.setObjective(
            expr=self.data.tau_G * self.v.ln_w_G + (1 - self.data.tau_G) * self.v.ln_w_L,
            sense=gp.GRB.MAXIMIZE,
        )

    def solve(self):
        # self.m.Params.TimeLimit = 1800  # seconds; the exporter keeps the best solution found
        self.m.optimize()
