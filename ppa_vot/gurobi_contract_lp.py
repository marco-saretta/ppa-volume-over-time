"""Three LP models that answer: does risk aversion make a contract happen?

Reproduces notes/why-cvar-and-mdp.md, Stages 1, 3 and 4, but instead of
plugging in the numbers by hand, an LP chooses the contracted volume M and
the total payment Pi = lambda * M that maximise the worse-off party's gain
over the disagreement point. With full transferability (prop:transfer) this
maximin objective equals the symmetric (theta = 1/2) Nash split, so its
optimal value is exactly W(M*) / 2.

The three models below share one builder, solve_contract(). Only two inputs
change between calls:
  - Model A, deterministic:      one scenario,  A_S = A_B = 0
  - Model B, stochastic, risk neutral: two scenarios, A_S = A_B = 0
  - Model C, stochastic, CVaR:         two scenarios, A_S = A_B = 0.5
Model A and B share A = 0 and differ only in whether the price is known.
Model B and C share the scenario data and differ only in A. That isolates
risk aversion, not uncertainty, as what creates the contract.

Profit is written in terms of Pi = lambda * M rather than lambda directly
(prop:decoupling), which keeps every constraint linear: no bilinear term,
no QP, no MIP. Each model is a plain LP.
"""

import gurobipy as gp
from gurobipy import GRB

P = 10.0  # seller production, MWh
D = 10.0  # buyer demand, MWh
M_MAX = 40.0  # generous upper bound on the contracted volume, MWh
BETA = 0.5  # CVaR confidence level

DETERMINISTIC = [(1.0, 50.0)]  # (probability, lambda_DA), single certain price
STOCHASTIC = [(0.5, 20.0), (0.5, 80.0)]  # Stage 3-4 scenarios


def add_utility(model, phi, probs, A, beta, name):
    """u = (1 - A) E[phi] + A CVaR_beta(phi), via the Rockafellar-Uryasev epigraph.

    zeta and s are hoisted into the outer maximisation: since the outer
    problem is itself a max and CVaR_beta(phi) = max_zeta {...}, adding zeta
    as a free variable of the outer LP and pushing s down via its own bound
    reproduces the CVaR exactly at the optimum, with no separate inner solve.
    """
    n = len(phi)
    zeta = model.addVar(lb=-GRB.INFINITY, name=f"zeta_{name}")
    s = model.addVars(n, lb=0.0, name=f"s_{name}")
    for w in range(n):
        model.addConstr(s[w] >= zeta - phi[w], name=f"cvar_{name}_{w}")
    cvar = zeta - (1.0 / (1.0 - beta)) * gp.quicksum(probs[w] * s[w] for w in range(n))
    expec = gp.quicksum(probs[w] * phi[w] for w in range(n))
    u = model.addVar(lb=-GRB.INFINITY, name=f"u_{name}")
    model.addConstr(u == (1 - A) * expec + A * cvar, name=f"u_def_{name}")
    return u


def disagreement(scenarios, A, party, beta=BETA):
    """u^i at M = 0, Pi = 0: the no-contract merchant position, solved as its own LP."""
    with gp.Env(empty=True) as env:
        env.setParam("OutputFlag", 0)
        env.start()
        with gp.Model(env=env) as m:
            probs = [p for p, _ in scenarios]
            if party == "S":
                phi = [lam * P for _, lam in scenarios]
            else:
                phi = [-lam * D for _, lam in scenarios]
            u = add_utility(m, phi, probs, A, beta, "d")
            m.setObjective(u, GRB.MAXIMIZE)  # phi is data, so this just evaluates u
            m.optimize()
            return u.X


def solve_contract(scenarios, A_S, A_B, beta=BETA, label=""):
    """Build and solve the maximin LP; return a dict of the optimal contract."""
    d_S = disagreement(scenarios, A_S, "S", beta)
    d_B = disagreement(scenarios, A_B, "B", beta)
    probs = [p for p, _ in scenarios]

    with gp.Env(empty=True) as env:
        env.setParam("OutputFlag", 0)
        env.start()
        with gp.Model(f"contract_{label}", env=env) as m:
            M = m.addVar(lb=0.0, ub=M_MAX, name="M")
            Pi = m.addVar(lb=-GRB.INFINITY, name="Pi")

            phi_S = [Pi + lam * (P - M) for _, lam in scenarios]
            phi_B = [-Pi + lam * (M - D) for _, lam in scenarios]

            u_S = add_utility(m, phi_S, probs, A_S, beta, "S")
            u_B = add_utility(m, phi_B, probs, A_B, beta, "B")

            x = m.addVar(lb=-GRB.INFINITY, name="x")  # seller gain over disagreement
            y = m.addVar(lb=-GRB.INFINITY, name="y")  # buyer gain over disagreement
            m.addConstr(x == u_S - d_S)
            m.addConstr(y == u_B - d_B)

            t = m.addVar(lb=-GRB.INFINITY, name="t")  # worse-off party's gain
            m.addConstr(t <= x)
            m.addConstr(t <= y)
            m.setObjective(t, GRB.MAXIMIZE)

            m.optimize()
            if m.Status != GRB.OPTIMAL:
                m.setParam("OutputFlag", 1)
                m.optimize()
                raise RuntimeError(f"model {label} did not solve to optimality: status {m.Status}")

            M_star, Pi_star = M.X, Pi.X
            lam_star = Pi_star / M_star if M_star > 1e-6 else float("nan")
            return {
                "label": label,
                "d_S": d_S,
                "d_B": d_B,
                "M": M_star,
                "Pi": Pi_star,
                "lambda": lam_star,
                "x": x.X,
                "y": y.X,
                "W": x.X + y.X,
                "t": t.X,
            }


def report(res):
    print(
        f"{res['label']:32s}  "
        f"d^S={res['d_S']:7.1f}  d^B={res['d_B']:7.1f}  |  "
        f"M*={res['M']:6.2f}  lambda*={res['lambda']:6.2f}  |  "
        f"x={res['x']:7.2f}  y={res['y']:7.2f}  W={res['W']:7.2f}  "
        f"t*={res['t']:7.2f}"
    )


def main():
    print(f"{'model':32s}  {'disagreement':24s}     {'contract':26s}     {'gains':30s}")
    a = solve_contract(DETERMINISTIC, A_S=0.0, A_B=0.0, label="A: deterministic")
    b = solve_contract(STOCHASTIC, A_S=0.0, A_B=0.0, label="B: stochastic, risk neutral")
    c = solve_contract(STOCHASTIC, A_S=0.5, A_B=0.5, label="C: stochastic, CVaR (A=0.5)")
    for res in (a, b, c):
        report(res)

    print()
    print("A -> B changes only the price from certain to uncertain: t* stays 0.")
    print("B -> C changes only A from 0 to 0.5, same price scenarios: t* jumps to 150.")
    print("Uncertainty alone does nothing. Risk aversion is what makes the contract exist.")


if __name__ == "__main__":
    main()
