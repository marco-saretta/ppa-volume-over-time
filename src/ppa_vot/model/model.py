import logging
from types import SimpleNamespace

import gurobipy as gp

log = logging.getLogger(__name__)


class BilevelModel:
    def __init__(self, config, data):
        self.cfg = config
        self.data = data
        self.configure_model()
        self.add_vars()
        self.add_cons()

    def configure_model(self):
        env = gp.Env(empty=True)
        env.setParam("LogToConsole", 0)
        env.start()
        self.m = gp.Model(env=env)
        log.info("model setup")

    def add_vars(self):
        data = self.data
        self.vars = SimpleNamespace()
        INF = gp.GRB.INFINITY

        # Bargaining variables
        self.vars.w_G = self.m.addVar(lb=data.epsilon, name="w_G")  # surplus, >= epsilon
        self.vars.w_L = self.m.addVar(lb=data.epsilon, name="w_L")
        self.vars.ln_w_G = self.m.addVar(lb=-INF, name="ln_w_G")  # ln w, for the NBS objective
        self.vars.ln_w_L = self.m.addVar(lb=-INF, name="ln_w_L")
        self.vars.u_G = self.m.addVar(lb=-INF, name="u_G")  # mean-CVaR utility
        self.vars.u_L = self.m.addVar(lb=-INF, name="u_L")
        self.vars.phi_G = self.m.addMVar(data.n_Omega, lb=-INF, name="phi_G")  # net earnings
        self.vars.phi_L = self.m.addMVar(data.n_Omega, lb=-INF, name="phi_L")

        # Contract variables
        self.vars.v = self.m.addVar(lb=data.volume_lower, ub=data.volume_upper, name="v")
        # z = S V; the strike bounds become constraints on z and v, S = z / V after the solve
        self.vars.aux_sv = self.m.addVar(lb=-INF, name="aux_sv")
        self.vars.q = self.m.addMVar(
            (data.n_H, data.n_T, data.n_Omega), lb=data.quota_lower, ub=data.quota_upper, name="q"
        )

        # Dual variables of the lower level (V2 designs only)
        self.vars.rho = self.m.addMVar((data.n_T, data.n_Omega), lb=-INF, name="rho")  # volume
        self.vars.mu_u = self.m.addMVar(
            (data.n_H, data.n_T, data.n_Omega), lb=0, name="mu_u"
        )  # cap
        self.vars.mu_l = self.m.addMVar(
            (data.n_H, data.n_T, data.n_Omega), lb=0, name="mu_l"
        )  # floor

        # Risk aversion variables (CVaR)
        self.vars.zeta_G = self.m.addVar(lb=-INF, name="zeta_G")
        self.vars.zeta_L = self.m.addVar(lb=-INF, name="zeta_L")
        self.vars.eta_G = self.m.addMVar(data.n_Omega, lb=0, name="eta_G")
        self.vars.eta_L = self.m.addMVar(data.n_Omega, lb=0, name="eta_L")

        log.info("variables added")

    def add_cons(self):

        log.info("constraints added")

    def solve(self):
        self.m.optimize()
