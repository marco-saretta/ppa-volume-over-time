#!/usr/bin/env bash
# Why does the binary expansion return a wrong V?  Diagnostics, 2026-11-19.
#
# Setting: binary expansion, 3 weeks x 100 scenarios, MIPGap 1e-6. The exact sweep gives V* = 357
# (W 7201.26). Group A (objective nbs/joint x NumericFocus 0/3, multirun/binary_diag/A_*) is done:
# all four runs wrong (V 283, 262, 327, 315), each with gap 0. Every returned V has a better
# neighbour V+1, and the region of V* is discarded in the last nodes as "infeasible" or "cutoff".
#
# Groups still to run (each: joint objective first, it is faster, then nbs):
#   C  V fixed at 357            sanity check of the setup, about a minute
#   E  Cuts = 0                  are the root cuts cutting off V*?
#   F  Presolve = 0              are presolve reductions cutting off V*?
#   B  tolerances 1e-9           is it the feasibility / optimality tolerance?
#   D  V restricted to [300,400] does a small search range find V*?
#   G  Cuts = 0 and Presolve = 0 joint only, in case E and F alone do not settle it
#
# Usage, from anywhere:
#   bash scripts/run_binary_diagnostics.sh          # all groups, in the order C E F B D G
#   bash scripts/run_binary_diagnostics.sh E F      # only some groups
#   uv run python scripts/summarize_diagnostics.py  # table of every run, checked against the sweep
#
# Finished runs (Gurobi status 2 optimal or 9 time limit) are skipped, so the script can be stopped
# and restarted at any time. Ctrl-C stops the current solve (status 11, the incumbent is still
# exported) and then the script; at the next start that run is moved to _incomplete/ and redone.
# Every run is capped at TimeLimit = 3600 s (status 9 then; the summary still checks the bound).

set -u
cd "$(dirname "$0")/.." || exit 1  # repo root
OUT=multirun/binary_diag
trap 'echo; echo "=== $(date +%T) interrupted: stopping the script"; exit 130' INT TERM

# Settings of every run, all explicit so that later edits of demo.yaml do not change the tests.
# A run overrides any of them with key=value.
declare -A BASE=(
  [simulations.data.scenarios]=100
  [simulations.data.weeks]=3
  [simulations.model.binary_expansion.do]=true
  [simulations.model.contract.guess.do]=false
  [simulations.model.contract.volume_lower]=0
  [simulations.model.contract.volume_upper]=600
  [simulations.solver.MIPGap]=1e-6
  [simulations.solver.NumericFocus]=0
  [simulations.solver.FeasibilityTol]=1e-6
  [simulations.solver.OptimalityTol]=1e-6
  [simulations.solver.Cuts]=-1
  [simulations.solver.Presolve]=-1
  [simulations.solver.TimeLimit]=3600
)

is_done() {  # is_done <run dir>: scalars.json with Gurobi status 2 (optimal) or 9 (time limit)
  [ -f "$1/scalars.json" ] && python3 -c \
    'import json, sys; sys.exit(json.load(open(sys.argv[1])).get("status") not in (2, 9))' \
    "$1/scalars.json"
}

run_one() {  # run_one <group>/<n> key=value ...
  local name=$1; shift
  local dir=$OUT/$name
  if is_done "$dir"; then echo "--- $(date +%T) skip $dir (done)"; return 0; fi
  if [ -e "$dir" ]; then  # unfinished or interrupted: keep it aside, do not mix logs
    local aside=$OUT/_incomplete/${name//\//_}_$(date +%Y%m%d-%H%M%S)
    mkdir -p "$OUT/_incomplete" && mv "$dir" "$aside"
    echo "--- moved unfinished $dir to $aside"
  fi
  local -A cfg=()
  local k kv
  for k in "${!BASE[@]}"; do cfg[$k]=${BASE[$k]}; done
  for kv in "$@"; do cfg[${kv%%=*}]=${kv#*=}; done
  local args=()
  for k in "${!cfg[@]}"; do args+=("$k=${cfg[$k]}"); done
  echo "=== $(date +%T) $dir: $*"
  # systemd-inhibit: no suspend while solving (suspends inflate the runtime)
  systemd-inhibit --what=sleep --why="binary diagnostics $name" \
    uv run main.py "${args[@]}" hydra.run.dir="$dir"
}

both() {  # both <group> key=value ...: joint objective (n = 1) first, then nbs (n = 0)
  local g=$1; shift
  run_one "$g/1" simulations.model.NBS.objective=joint "$@"
  run_one "$g/0" simulations.model.NBS.objective=nbs "$@"
}

for g in ${*:-C E F B D G}; do
  case $g in
    C) both C_fixed_V357 \
         simulations.model.contract.volume_lower=357 simulations.model.contract.volume_upper=357 ;;
    E) both E_cuts_off simulations.solver.Cuts=0 ;;
    F) both F_presolve_off simulations.solver.Presolve=0 ;;
    B) both B_tolerances simulations.solver.FeasibilityTol=1e-9 simulations.solver.OptimalityTol=1e-9 ;;
    D) both D_window_300_400 \
         simulations.model.contract.volume_lower=300 simulations.model.contract.volume_upper=400 ;;
    G) run_one G_cuts_presolve_off/1 simulations.model.NBS.objective=joint \
         simulations.solver.Cuts=0 simulations.solver.Presolve=0 ;;
    A) echo "--- group A is done (multirun/binary_diag/A_objective_numericfocus), not rerun" ;;
    *) echo "unknown group $g (use C E F B D G)" ;;
  esac
done

echo "=== $(date +%T) done. Summary:"
uv run python scripts/summarize_diagnostics.py "$OUT"
