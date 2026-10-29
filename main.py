import logging

import hydra
from hydra.core.hydra_config import HydraConfig
from omegaconf import DictConfig, OmegaConf

import ppa_vot

log = logging.getLogger(__name__)


@hydra.main(version_base="1.3", config_path="config", config_name="config")
def main(cfg: DictConfig):
    log.info("Output dir: %s", HydraConfig.get().runtime.output_dir)
    log.debug("Config:\n%s", OmegaConf.to_yaml(cfg))

    runner = ppa_vot.Runner(cfg)
    runner.run_pipeline()


if __name__ == "__main__":
    main()
