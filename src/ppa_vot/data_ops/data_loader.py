import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from omegaconf import DictConfig

log = logging.getLogger(__name__)


@dataclass
class DataLoader:
    cfg: DictConfig = field(repr=False)  # the only argument: DataLoader(cfg=...)

    # filled in __post_init__, not passed by the caller
    # parameters
    epsilon: float = field(init=False)
    tau_G: float = field(init=False)
    alpha_G: float = field(init=False)
    beta_G: float = field(init=False)
    alpha_L: float = field(init=False)
    beta_L: float = field(init=False)
    strike_lower: float = field(init=False)
    strike_upper: float = field(init=False)
    volume_lower: float = field(init=False)
    volume_upper: float = field(init=False)
    quota_lower: float = field(init=False)
    quota_upper: float = field(init=False)

    # cardinalities of the sets H (hours of a week), T (weeks), Omega (scenarios)
    n_H: int = field(init=False)
    n_T: int = field(init=False)
    n_Omega: int = field(init=False)

    # scenario tensors, shape (n_H, n_T, n_Omega): element [h, t, omega]
    sc_prices: np.ndarray = field(init=False, repr=False)  # day-ahead price lambda, EUR/MWh
    sc_p_G: np.ndarray = field(init=False, repr=False)  # generator production P^G, MWh
    sc_p_L: np.ndarray = field(init=False, repr=False)  # load consumption P^L, MWh
    pi: np.ndarray = field(init=False, repr=False)  # scenario probability, shape (n_Omega,)

    def __post_init__(self):
        self.hydra_params()
        self.load_scenarios()

    def hydra_params(self):
        sim = self.cfg.simulations.model
        self.epsilon = sim.NBS.epsilon
        self.tau_G = sim.NBS.bargaining_power_G

        self.alpha_G = sim.risk_aversion.alpha_G
        self.beta_G = sim.risk_aversion.beta_G
        self.alpha_L = sim.risk_aversion.alpha_L
        self.beta_L = sim.risk_aversion.beta_L

        self.strike_lower = sim.contract.strike_lower
        self.strike_upper = sim.contract.strike_upper
        self.volume_lower = sim.contract.volume_lower
        self.volume_upper = sim.contract.volume_upper
        self.quota_lower = sim.contract.quota_lower
        self.quota_upper = sim.contract.quota_upper
        log.info("Parameters read from cfg.simulations.model (%s)", self.cfg.simulations.name)

    def load_scenarios(self):
        """Read the processed files as tensors [h, t, omega].

        Each file has rows (week, hour) and one column per scenario.
        """
        proc_dir = Path(self.cfg.paths.data) / "processed"

        def tensor(name: str) -> np.ndarray:
            df = pd.read_csv(proc_dir / f"{name}.csv", index_col=["week", "hour"])
            n_T = df.index.get_level_values("week").nunique()
            n_H = df.index.get_level_values("hour").nunique()
            # rows are ordered week by week:
            # (n_T * n_H, n_Omega) -> (n_T, n_H, n_Omega) -> (n_H, n_T, n_Omega)
            return df.to_numpy().reshape(n_T, n_H, -1).transpose(1, 0, 2)

        self.sc_prices = tensor("prices")
        self.sc_p_G = tensor("production")
        self.sc_p_L = tensor("consumption")
        assert self.sc_prices.shape == self.sc_p_G.shape == self.sc_p_L.shape, "shapes differ"

        self.n_H, self.n_T, self.n_Omega = self.sc_prices.shape
        self.pi = np.full(self.n_Omega, 1 / self.n_Omega)  # equiprobable scenarios
        log.info(
            "Scenarios loaded: |H| = %d, |T| = %d, |Omega| = %d", self.n_H, self.n_T, self.n_Omega
        )
