import logging

import gurobipy as gp

log = logging.getLogger(__name__)


class BilevelModel:
    def __init__(self):
        self.configure_model()

    def configure_model(self):
        # Gurobi also sends its output to the "gurobipy" Python logger (and so to
        # Hydra's log file). Turn off its own console printing to avoid duplicate lines.
        env = gp.Env(empty=True)
        env.setParam("LogToConsole", 0)
        env.start()
        self.m = gp.Model(env=env)
        log.info("model setup")

    def solve(self):
        self.m.optimize()
