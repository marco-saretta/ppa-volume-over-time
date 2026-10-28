import gurobipy as gb

m = gb.Model()
x = m.addMVar(1000000)
m.optimize()
