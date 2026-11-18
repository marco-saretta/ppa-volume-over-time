# type activate mcp_julia to activate env for REPL
# to run from terminal: include("mcp_julia/src/test.jl")
using JuMP, PATHSolver, HiGHS

println("I am alive")

M = [0 0 -1 -1;
0 0 1 -2;
1 -1 2 -2;
1 2 -2 4]

q = [2, 2, -2, -6]

model = Model(PATHSolver.Optimizer)
@variable(model, x[1:4] >=0)
@constraint(model, M * x .+ q ⟂ x)
optimize!(model)

println(termination_status(model))       # LOCALLY_SOLVED if it worked
println(value.(x))                        # expected [2.8, 0.0, 0.8, 1.2]
