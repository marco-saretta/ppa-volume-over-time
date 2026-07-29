# PPA Volume over Time: A Bilevel Approach

Marco Saretta, Jalal Kazempour

## Overview

This repository holds the code and paper for a study on Power Purchase Agreements (PPAs) in which the contracted volume must be delivered over a period (e.g. one week) rather than hour by hour.

Standard PPAs (pay as consumed or baseload) fix the delivered volume every hour, leaving the seller exposed to volume risk whenever production does not match the profile. We introduce a third arrangement, volume over time, where only the cumulative volume over the period is contracted. The hourly delivery schedule becomes a decision variable (a delivery path), constrained by a delivery cap and a volume balance over the period.

Four model variants follow from two modelling choices: whether the contract terms (strike price and volume) are exogenous or negotiated, and whether the delivery path is agreed jointly or nominated by one party. The negotiated cases are formulated as bilevel programmes, with a Nash Bargaining Solution at the upper level allocating utility between buyer and seller, and the delivery path chosen at the lower level. Party utilities can include a CVaR risk term alongside expected profit.

## Repository structure

```
ppa_vot/        Python package with the analysis/simulation code
overleaf/       Git submodule, linked to the Overleaf project for the paper
```

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for Python dependency management.

```
uv sync
```

This creates a `.venv` with the pinned dependencies from `uv.lock` (Gurobi, HiGHS, linopy, Hydra, numpy, pandas, polars, pyarrow among them).

Run the entry point with:

```
uv run python -m ppa_vot.main
```
