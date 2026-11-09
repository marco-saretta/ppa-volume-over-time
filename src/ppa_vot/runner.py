import logging

from .data_ops import DataExporter, DataLoader, DataPreprocessor
from .model import BilevelModel
from .utils import stage

log = logging.getLogger(__name__)


class Runner:
    def __init__(self, cfg):
        self.cfg = cfg
        log.info("Runner instantiated")

    def run_pipeline(self):
        with stage("preprocess"):
            self.preprocess_data()
        with stage("load_data"):
            self.load_data()
        with stage("build_model"):
            self.build_model()
        with stage("solve"):
            self.solve_model()
        with stage("export_data"):
            self.export_data()

    def preprocess_data(self):
        DataPreprocessor(config=self.cfg)

    def load_data(self):
        log.info("Set up DataLoader")
        self.data = DataLoader(cfg=self.cfg)

    def build_model(self):
        self.model = BilevelModel(config=self.cfg, data=self.data)

    def solve_model(self):
        self.model.solve()

    def export_data(self):
        DataExporter(config=self.cfg)
