from omegaconf import DictConfig


class DataExporter:
    def __init__(self, config: DictConfig):
        self.cfg = config
