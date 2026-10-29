import logging
from types import SimpleNamespace

import gurobipy as gp

log = logging.getLogger(__name__)


class BilevelModel:
    def __init__(self, config, data):
        self.cfg = config
        self.data = data
        self.configure_model()

    def configure_model(self):
        env = gp.Env(empty=True)
        env.setParam("LogToConsole", 0)
        env.start()
        self.m = gp.Model(env=env)
        log.info("model setup")

    def add_vars(self):
        self.vars = SimpleNamespace()

    def solve(self):
        self.m.optimize()
