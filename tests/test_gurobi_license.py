import gurobipy as gb


def test_gurobi_license():
    gb.Model()
