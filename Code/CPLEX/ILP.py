import cplex
from docplex.mp.model import Model

# # Create a model
# model = Model(name="Simple ILP")

# # Define integer decision variables
# x = model.integer_var(name="x")
# y = model.integer_var(name="y")

# # Add constraints
# model.add_constraint(2*x + y <= 8, "c1")
# model.add_constraint(x + 2*y <= 6, "c2")

# # Define the objective
# model.maximize(3*x + 2*y)

# # Solve the problem
# solution = model.solve()

# # Display results
# if solution:
#     print("Optimal Solution:")
#     print(f"x = {x.solution_value}")
#     print(f"y = {y.solution_value}")
#     print(f"Objective value = {model.objective_value}")
# else:
#     print("No feasible solution found.")

def solve_ilp():
    problem = cplex.Cplex()
    problem.set_problem_type(cplex.Cplex.problem_type.LP)
    problem.set_results_stream(None)

    # Maximize objective
    problem.objective.set_sense(problem.objective.sense.maximize)

    names = ['x', 'y']
    objective = [3, 2]
    lower_bounds = [0, 0]
    upper_bounds = [cplex.infinity, cplex.infinity]
    types = [problem.variables.type.integer] * 2
    problem.variables.add(obj=objective, lb=lower_bounds, ub=upper_bounds, names=names, types=types)

    problem.linear_constraints.add(
        lin_expr=[[['x', 'y'], [2, 1]]],
        senses=["L"],
        rhs=[8]
    )

    problem.linear_constraints.add(
        lin_expr=[[['x', 'y'], [1, 2]]],
        senses=["L"],
        rhs=[6]
    )

    problem.solve()

    # Print results
    print("Solution status:", problem.solution.get_status_string())
    print("Objective value:", problem.solution.get_objective_value())
    for name in names:
        print(f"{name} = {problem.solution.get_values(name)}")

solve_ilp()

