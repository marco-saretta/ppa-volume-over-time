import logging

import gurobipy as gp

log = logging.getLogger(__name__)


class BilevelModel:
    def __init__(self):
        self.configure_model()

    def configure_model(self):
        self.m = gp.Model()
        log.info("model setup")

    def solve(self):
        self.m.optimize()
