import logging

import hydra
from omegaconf import DictConfig

log = logging.getLogger(__name__)


@hydra.main(version_base="1.3", config_path="config", config_name="config")
def main(cfg: DictConfig):
    log.info("i am alive")


if __name__ == "__main__":
    main()
