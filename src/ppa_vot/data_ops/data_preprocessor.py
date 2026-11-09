import json
import logging
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
import pandas as pd
from omegaconf import DictConfig, OmegaConf

log = logging.getLogger(__name__)

HOURS_PER_WEEK = 168
SETTINGS_FILE = "settings.json"  # settings used for the files in data/processed/
MAX_GAP_HOURS = 2  # shorter wind gaps are interpolated; weeks with longer gaps are not drawn


class DataPreprocessor:
    """Download DK1 data to data/raw/, bootstrap scenarios and save them to data/processed/.

    prices.csv       day-ahead price, EUR/MWh
    production.csv   wind output, scaled to a mean weekly energy of generator_size MWh
    consumption.csv  business consumption in DK1, scaled to a mean weekly energy of load_size MWh

    The three files have the same shape: rows (week, hour) of one scenario, one column per
    scenario. Every scenario strings together `weeks` historical weeks drawn with replacement;
    the three series use the same drawn weeks, so their link is kept.
    Settings: config/data/default.yaml (window, source) and simulations.data (scenarios, sizes).
    """

    def __init__(self, config: DictConfig):
        self.cfg = config
        self.start = pd.Timestamp(self.cfg.data.start)
        self.end = pd.Timestamp(self.cfg.data.end)

        # methods
        self.setup_dirs()
        if self.scenarios_exist():
            log.info("Scenarios in %s already match the config: skipping", self.proc_dir)
            return
        self.fetch_data()
        self.preprocess_data()
        self.save_settings()

    def setup_dirs(self):
        self.root_dir = Path(self.cfg.paths.root)
        self.data_dir = Path(self.cfg.paths.data)
        self.raw_dir = self.data_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.proc_dir = self.data_dir / "processed"
        self.proc_dir.mkdir(exist_ok=True, parents=True)
        log.info("Data directories created")

    # ---- skip if the scenarios exist ----------------------------------------------------------
    def settings(self) -> dict:
        """Config entries the scenarios depend on: data window and simulations.data."""
        return {
            "start": self.cfg.data.start,
            "end": self.cfg.data.end,
            **OmegaConf.to_container(self.cfg.simulations.data, resolve=True),
        }

    def scenarios_exist(self) -> bool:
        """True if the three files exist and were built with the current settings."""
        files = [self.proc_dir / f"{n}.csv" for n in ("prices", "production", "consumption")]
        stamp = self.proc_dir / SETTINGS_FILE
        if not stamp.exists() or not all(f.exists() for f in files):
            return False
        with open(stamp) as f:
            return json.load(f) == self.settings()

    def save_settings(self):
        with open(self.proc_dir / SETTINGS_FILE, "w") as f:
            json.dump(self.settings(), f, indent=2)

    def fetch_data(self):
        self.raw_prices = self.download(
            "DayAheadPrices",
            columns=["TimeUTC", "PriceArea", "DayAheadPriceEUR"],
            filter={"PriceArea": ["DK1"]},
        )
        self.raw_power = self.download(
            "PowerSystemRightNow", columns=["Minutes1UTC", "OnshoreWindPower", "OffshoreWindPower"]
        )
        self.raw_consumption = self.download(
            "ConsumptionConsumerCategoryHour",
            columns=["TimeUTC", "RegionName", "ConsumerCategory3", "ConsumptionkWh"],
            filter={"RegionName": list(self.cfg.data.dk1_regions)},
        )

    def preprocess_data(self):
        self.get_prices_data()
        self.get_wind_data()
        self.get_load_data()
        self.bootstrap_scenarios()

    # ---- download -----------------------------------------------------------------------------
    def download(
        self, dataset: str, columns: list[str], filter: dict | None = None
    ) -> pd.DataFrame:
        """One Energinet dataset as a DataFrame, cached in data/raw/ (downloaded once).

        Source: https://www.energidataservice.dk/ (API guide: /guides/api-guides).
        One day of margin on each side: the API window is in Danish time, and the
        hourly series are cut to the UTC window afterwards.
        """
        raw_file = self.raw_dir / f"{dataset}_{self.start:%Y%m%d}_{self.end:%Y%m%d}.csv"
        if raw_file.exists():
            log.info("Using cached %s", raw_file.name)
            return pd.read_csv(raw_file)

        params = {
            "start": f"{self.start - pd.Timedelta('1D'):%Y-%m-%dT%H:%M}",
            "end": f"{self.end + pd.Timedelta('1D'):%Y-%m-%dT%H:%M}",
            "columns": ",".join(columns),
            "sort": f"{columns[0]} ASC",
            "limit": 0,  # every row (the API default is 100)
        }
        if filter:
            params["filter"] = json.dumps(filter)
        url = f"{self.cfg.data.api_url}/{dataset}?{urlencode(params)}"

        log.info("Downloading %s %s to %s", dataset, self.start.date(), self.end.date())
        with urlopen(url, timeout=600) as response:
            df = pd.DataFrame(json.load(response)["records"])
        df.to_csv(raw_file, index=False)
        log.info("Saved %d rows to %s", len(df), raw_file.name)
        return df

    # ---- hourly history on the UTC window [start, end) -------------------------------------------
    def to_hourly(self, df: pd.DataFrame, time_col: str) -> pd.Series:
        """Hourly mean of the single value column, on every hour of the window (NaN if missing)."""
        s = df.set_index(pd.to_datetime(df[time_col])).drop(columns=time_col).squeeze(axis=1)
        s = s.sort_index().resample("h").mean()
        return s.reindex(pd.date_range(self.start, self.end, freq="h", inclusive="left"))

    def get_prices_data(self):
        # 15-minute prices -> hourly mean, EUR/MWh
        self.prices = self.to_hourly(self.raw_prices[["TimeUTC", "DayAheadPriceEUR"]], "TimeUTC")
        assert not self.prices.isna().any(), "hour without a price"

    def get_wind_data(self):
        # 1-minute MW of onshore + offshore wind -> hourly mean MW (= MWh per hour)
        df = self.raw_power[["Minutes1UTC"]].assign(
            wind=self.raw_power["OnshoreWindPower"] + self.raw_power["OffshoreWindPower"]
        )
        self.wind = self.to_hourly(df, "Minutes1UTC").interpolate(
            limit=MAX_GAP_HOURS, limit_area="inside"
        )

    def get_load_data(self):
        # business consumption ("Erhverv"), summed over the DK1 regions, kWh -> MWh
        df = self.raw_consumption
        df = df[df["ConsumerCategory3"] == "Erhverv"]
        df = df.groupby("TimeUTC", as_index=False)["ConsumptionkWh"].sum()
        self.load = self.to_hourly(df, "TimeUTC") / 1000
        assert not self.load.isna().any(), "hour without consumption"

    # ---- scenarios -------------------------------------------------------------------------------
    def bootstrap_scenarios(self):
        sim = self.cfg.simulations.data
        size = sim.player_size

        # One row per historical week: shape (weeks of history, 168)
        def by_week(s: pd.Series) -> np.ndarray:
            return s.to_numpy().reshape(-1, HOURS_PER_WEEK)

        price, wind, load = by_week(self.prices), by_week(self.wind), by_week(self.load)

        # Scaling on the whole history: mean weekly energy = generator_size and load_size (MWh)
        production = size.generator_size * wind / (np.nanmean(wind) * HOURS_PER_WEEK)
        consumption = size.load_size * load / (load.mean() * HOURS_PER_WEEK)
        log.info(
            "Generator: %.0f MWh per week, peak %.2f MW (use it for quota_upper)",
            size.generator_size,
            np.nanmax(production),
        )

        # Pool of weeks to draw from: weeks with a wind gap longer than MAX_GAP_HOURS are left out
        pool = np.flatnonzero(~np.isnan(production).any(axis=1))
        dropped = self.prices.index[::HOURS_PER_WEEK][np.isnan(production).any(axis=1)]
        log.info(
            "Drawing from %d of %d weeks (left out, wind gaps: %s)",
            len(pool),
            len(price),
            ", ".join(f"{d:%Y-%m-%d}" for d in dropped),
        )

        # drawn[s, t] = historical week used as week t of scenario s
        rng = np.random.default_rng(sim.seed)
        drawn = rng.choice(pool, size=(sim.scenarios, sim.weeks))

        index = pd.MultiIndex.from_product(
            [range(sim.weeks), range(HOURS_PER_WEEK)], names=["week", "hour"]
        )
        for name, values in {
            "prices": price,
            "production": production,
            "consumption": consumption,
        }.items():
            # values[drawn] has shape (scenarios, weeks, 168) -> rows (week, hour), columns scenario
            out = pd.DataFrame(values[drawn].reshape(sim.scenarios, -1).T, index=index)
            out.columns.name = "scenario"
            out.to_csv(self.proc_dir / f"{name}.csv")
        log.info("Saved %d scenarios of %d weeks to %s", sim.scenarios, sim.weeks, self.proc_dir)
