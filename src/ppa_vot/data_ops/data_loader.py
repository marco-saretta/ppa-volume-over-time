import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class DataLoader:
    def __init__(self, config):
        self.cfg = config
