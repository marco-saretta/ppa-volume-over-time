import json
from pathlib import Path

import numpy as np
import yaml


def latest_run(outputs: Path = Path("outputs")) -> Path:
    """Most recent run folder outputs/<date>/<time>/ that has results (skips aborted runs)."""
    runs = sorted(p.parent for p in outputs.glob("*/*/arrays.npz"))  # names sort by date-time
    if not runs:
        raise FileNotFoundError(f"no arrays.npz under {outputs}")
    return runs[-1]


def load_results(run_dir: Path):
    """Arrays (dict of ndarrays), scalars (dict) and command-line overrides of one run."""
    with np.load(run_dir / "arrays.npz") as npz:  # lazy file: copy into a dict, then close
        arrays = {name: npz[name] for name in npz.files}
    scalars = json.loads((run_dir / "scalars.json").read_text())
    overrides = yaml.safe_load((run_dir / ".hydra" / "overrides.yaml").read_text())
    return arrays, scalars, overrides


if __name__ == "__main__":
    run = latest_run()
    arrays, scalars, overrides = load_results(run)
    print(f"run: {run}  overrides: {overrides}")
    for name, a in arrays.items():
        print(f"  {name:6s} {str(a.shape):16s} min {a.min():10.3f}  max {a.max():10.3f}")
    print({k: round(v, 3) for k, v in scalars.items()})
