from logging import getLogger

from .data_ops import DataLoader
from .model import BilevelModel

log = getLogger(__name__)


class Runner:
    def __init__(self, cfg):
        self.cfg = cfg
        log.info("Runner instantiated")

    def run_pipeline(self):
        log.info("Running pipeline")
        self.load_data()
        self.build_model()

    def load_data(self):
        log.info("Set up DataLoader")
        self.data = DataLoader(cfg=self.cfg)

    def build_model(self):
        self.model = BilevelModel()
