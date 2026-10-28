# PPA Volume over Time

Code for a study of Power Purchase Agreements (PPAs) where only the cumulative volume over a period (e.g. one week) is contracted, and the hourly delivery path is a decision variable. Negotiated contract terms are modelled as a bilevel problem with a Nash bargaining upper level and a CVaR-aware lower level.

Marco Saretta, Salvador Pineda Morente, Juan Miguel Morales Gonzalez, Jalal Kazempour

## Layout

```text
src/ppa_vot/  Python package
config/       Hydra configuration
tests/        pytest tests
```

## Setup

Requires [uv](https://docs.astral.sh/uv/) and a Gurobi licence.

```sh
git clone git@github.com:marco-saretta/ppa-volume-over-time.git
cd ppa-volume-over-time
uv sync
```

## Tests

```sh
uv run pytest
```
