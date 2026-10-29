import json
import logging
from pathlib import Path
from urllib.request import urlopen

import pandas as pd
from omegaconf import DictConfig

log = logging.getLogger(__name__)

HOURS_PER_WEEK = 168


class DataPreprocessor:
    """Generate synthetic hourly price, wind and load series and save them to CSV.

    Placeholder until real data is used. Settings live in config/data/default.yaml.
    """

    def __init__(self, config: DictConfig):
        self.cfg = config

        # methods
        self.setup_dirs()
        self.fetch_data()
        self.preprocess_data()

    def setup_dirs(self):
        self.root_dir = Path(self.cfg.paths.root)
        self.data_dir = Path(self.cfg.paths.data)
        self.raw_dir = self.data_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.proc_dir = self.data_dir / "processed"
        self.proc_dir.mkdir(exist_ok=True, parents=True)
        log.info("Data directories created")

    def fetch_data(self):
        self.get_power_system_right_now()

    def preprocess_data(self):
        self.get_wind_data()
        self.get_prices_data()
        self.get_load_data()

    def get_power_system_right_now(self) -> pd.DataFrame:
        """Hourly DK power system data from Energinet (wind, solar, production, exchange), in MW.

        Source: https://www.energidataservice.dk/tso-electricity/PowerSystemRightNow
        The 1-minute data is downloaded once to data/raw/ and reused on later runs.
        """
        start = pd.Timestamp(self.cfg.data.start)
        end = pd.Timestamp(self.cfg.data.end)
        raw_file = self.raw_dir / f"PowerSystemRightNow_{start:%Y%m%d}_{end:%Y%m%d}.csv"

        if raw_file.exists():
            log.info("Using cached %s", raw_file.name)
            df = pd.read_csv(raw_file, index_col=0, parse_dates=True)
        else:
            columns = [
                "Minutes1UTC",
                "OnshoreWindPower",
                "OffshoreWindPower",
                "SolarPower",
                "ProductionGe100MW",
                "ProductionLt100MW",
                "Exchange_Sum",
            ]
            url = (
                "https://api.energidataservice.dk/dataset/PowerSystemRightNow"
                f"?start={start:%Y-%m-%dT%H:%M}&end={end:%Y-%m-%dT%H:%M}"
                f"&columns={','.join(columns)}&sort=Minutes1UTC&limit=0"
            )
            log.info("Downloading PowerSystemRightNow %s to %s", start.date(), end.date())
            with urlopen(url, timeout=600) as response:
                records = json.load(response)["records"]
            df = pd.DataFrame(records).set_index("Minutes1UTC")
            df.index = pd.to_datetime(df.index)
            df.to_csv(raw_file)
            log.info("Saved %d rows to %s", len(df), raw_file.name)

        # 1-minute MW values -> hourly average MW (= MWh per hour)
        return df.resample("h").mean()

    def get_wind_data(self):
        log.info("Data fetched for wind")

    def get_prices_data(self):
        log.info("Data  fetched for prices")

    def get_load_data(self):
        log.info("Data  fetched for load")
