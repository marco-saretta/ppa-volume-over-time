# Market clearing with one generator and one demand.
# Step 1: welfare maximisation as one problem (HiGHS).
# Step 2: each party alone + clearing, written as KKT conditions (MCP, PATH).
# Both should give the same quantity and the same price.
#
# type activate mcp_julia to activate env for REPL
# to run from the REPL: include("mcp_julia/src/test.jl")
# (the old 4-variable LCP test is in git: git show HEAD:mcp_julia/src/test.jl)

using JuMP, PATHSolver, HiGHS

# ---------------- data ----------------
# generator cost      C(g) = a*g + 0.5*b*g^2    marginal cost    a + b*g
# demand utility      U(d) = α*d - 0.5*β*d^2    marginal utility α - β*d
a, b = 10.0, 1.0
α, β = 50.0, 1.0
Gmax = 15.0          # try 25.0: the cap no longer binds

cost(g)    = a*g + 0.5*b*g^2
utility(d) = α*d - 0.5*β*d^2

# ---------------- step 1: welfare max (HiGHS) ----------------
# max U(d) - C(g)   s.t.  d - g = 0 : λ,   g <= Gmax : μ,   g, d >= 0
welf = Model(HiGHS.Optimizer)
set_silent(welf)
@variable(welf, g >= 0)
@variable(welf, d >= 0)
@objective(welf, Max, α*d - 0.5*β*d^2 - (a*g + 0.5*b*g^2))
@constraint(welf, balance, d - g == 0)
@constraint(welf, cap, g <= Gmax)
optimize!(welf)

g_W = value(g)
d_W = value(d)
λ_W = shadow_price(balance)   # dual(balance) has the opposite sign in a Max problem
μ_W = shadow_price(cap)

# ---------------- step 2: equilibrium (PATH) ----------------
# generator:  max_g  λ*g - C(g)         s.t. g <= Gmax : μ
# demand:     max_d  U(d) - λ*d
# market:     g - d = 0,  λ free
eq = Model(PATHSolver.Optimizer)
set_silent(eq)
@variable(eq, g >= 0)
@variable(eq, d >= 0)
@variable(eq, μ >= 0)
@variable(eq, λ)                               # free: no bound

@constraint(eq, a + b*g - λ + μ ⟂ g)           # generator: marginal cost + cap value >= price
@constraint(eq, Gmax - g ⟂ μ)                  # generator: cap
@constraint(eq, λ - (α - β*d) ⟂ d)             # demand: price >= marginal utility
@constraint(eq, g - d ⟂ λ)                     # market clears (λ free, so this is g - d = 0)
optimize!(eq)

g_E = value(g)
d_E = value(d)
λ_E = value(λ)
μ_E = value(μ)

# ---------------- compare ----------------
println("HiGHS  ", termination_status(welf), "   PATH  ", termination_status(eq))
println("              welfare     equilibrium")
println("g         ", round(g_W, digits=4), "        ", round(g_E, digits=4))
println("d         ", round(d_W, digits=4), "        ", round(d_E, digits=4))
println("λ price   ", round(λ_W, digits=4), "        ", round(λ_E, digits=4))
println("μ cap     ", round(μ_W, digits=4), "        ", round(μ_E, digits=4))

profit = λ_E*g_E - cost(g_E)
CS     = utility(d_E) - λ_E*d_E
println("profit = ", profit, "   consumer surplus = ", CS, "   W = ", profit + CS)
