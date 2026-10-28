from logging import getLogger

import gurobipy as gp

log = getLogger(__name__)


class BilevelModel:
    def __init__(self):
        self.configure_model()

    def configure_model(self):
        self.m = gp.Model()
        log.info("model setup")
