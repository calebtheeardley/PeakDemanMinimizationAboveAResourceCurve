import cplex

def lp_solve():
    problem = cplex.Cplex()
    problem.set_problem_type(cplex.Cplex.problem_type.LP)
    problem.set_results_stream(None)  # Suppress output

    # Maximize objective
    problem.objective.set_sense(problem.objective.sense.maximize)

    names = ["x1", "x2"]
    objective = [40.0, 30.0]
    lower_bounds = [0.0, 0.0]
    upper_bounds = [cplex.infinity, cplex.infinity]
    problem.variables.add(obj=objective, lb=lower_bounds, ub=upper_bounds, names=names)

    # Constraints
    problem.linear_constraints.add(
        lin_expr = [[["x1", "x2"], [2.0, 1.0]]],
        senses = ["L"],
        rhs=[100.0]
    )
    problem.linear_constraints.add(
        lin_expr = [[["x1", "x2"], [3.0, 4.0]]],
        senses = ["L"], # "L" means less than or equal to (≤). (Other options: "E" for =, "G" for ≥)
        rhs=[120.0]
    )

    problem.solve()

    # Print results
    print("Solution status:", problem.solution.get_status_string())
    print("Objective value:", problem.solution.get_objective_value())
    for name in names:
        print(f"{name} = {problem.solution.get_values(name)}")
    
lp_solve()
