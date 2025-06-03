import cplex

# cplex python documentation - https://www.ibm.com/docs/en/icos/22.1.1?topic=tutorial-building-solving-small-lp-python

def solve_lp():
    # Create CPLEX problem instance
    problem = cplex.Cplex()
    problem.set_problem_type(cplex.Cplex.problem_type.LP)
    problem.set_results_stream(None)  # Suppress output

    # Maximize objective
    problem.objective.set_sense(problem.objective.sense.maximize)

    # Add variables (names, lower bounds, upper bounds, objective coefficients)
    names = ["x1", "x2"]
    objective = [2.0, 3.0]  # Maximize 2x + 3y
    lower_bounds = [0.0, 0.0]
    upper_bounds = [cplex.infinity, cplex.infinity]
    problem.variables.add(obj=objective, lb=lower_bounds, ub=upper_bounds, names=names)

    # Add constraint: x1 + x2 ≤ 4
    problem.linear_constraints.add(
        lin_expr=[[["x1", "x2"], [1.0, 1.0]]],
        senses=["L"],
        rhs=[4.0]
    )

    # Solve
    problem.solve()

    # Print results
    print("Solution status:", problem.solution.get_status_string())
    print("Objective value:", problem.solution.get_objective_value())
    for name in names:
        print(f"{name} = {problem.solution.get_values(name)}")

solve_lp()