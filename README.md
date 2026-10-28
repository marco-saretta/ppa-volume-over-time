# PPA Volume over Time

Code and paper for a study of Power Purchase Agreements (PPAs) where only the cumulative volume over a period (e.g. one week) is contracted, and the hourly delivery path is a decision variable. Negotiated contract terms are modelled as a bilevel problem with a Nash bargaining upper level and a CVaR-aware lower level.

Marco Saretta, Salvador Pineda Morente, Juan Miguel Morales Gonzalez, Jalal Kazempour

## Layout

```text
ppa_vot/    Python package (models, data, figures)
config/     Hydra configuration
tests/      pytest tests
notes/      Working notes
overleaf/   Paper (git submodule, Overleaf project, Elsevier template)
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) and a Gurobi licence.

```sh
git clone --recurse-submodules git@github.com:marco-saretta/ppa-volume-over-time.git
cd ppa-volume-over-time
uv sync
uv run python -m ppa_vot.main
```

The `overleaf` submodule asks for credentials on first clone: username `git`, password an Overleaf git token (Account Settings, Git Integration). If you cloned without `--recurse-submodules`, run `git submodule update --init`.

## Tests

```sh
uv run pytest
```
