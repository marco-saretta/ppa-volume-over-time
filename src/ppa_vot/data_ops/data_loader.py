from dataclasses import dataclass
from logging import getLogger

log = getLogger(__name__)


@dataclass
class DataLoader:
    def __init__(self, cfg):
        log.info("Start dataloading")
