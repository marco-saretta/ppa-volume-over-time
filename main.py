import hydra
from omegaconf import DictConfig


@hydra.main(version_base="1.3", config_path="config", config_name="config")
def main(cfg: DictConfig):
    print("I am alive")


if __name__ == "__main__":
    main()
