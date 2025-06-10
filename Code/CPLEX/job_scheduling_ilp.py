import cplex

"""
*** Problem ***
One problem to note is that if a job finishes at a certain time and another job ends at a certain time, 
then the program will consider that an overlap and therefore will not schedule one of those two jobs if it has the 
opportunity to. Additionally, it will say that the max height is the sum of those two jobs 

*** Question ***
Do we want the program to think that this case is an overlap? 
"""

# This is The list of job objects that will be scheduled
# They each have a release, deadline, duration and height
jobs = [ 
    {'release' : 0, 'deadline' : 4, 'duration' : 2, 'height' : 1},  
    {'release' : 1, 'deadline' : 6, 'duration' : 1, 'height' : 2},
    {'release' : 3, 'deadline' : 8, 'duration' : 2, 'height' : 1},
    {'release' : 4, 'deadline' : 6, 'duration' : 2, 'height' : 2},
    {'release' : 0, 'deadline' : 5, 'duration' : 1, 'height' : 1},
    {'release' : 3, 'deadline' : 7, 'duration' : 1, 'height' : 1},
    {'release' : 5, 'deadline' : 7, 'duration' : 1, 'height' : 3},
    {'release' : 0, 'deadline' : 8, 'duration' : 1, 'height' : 2},
]


# This creates j number of distinct sub-lists where j is the number of jobs
# Each sublist contains all of the finite possible intervals during which job j could be executed
intervals = [[] for _ in range(len(jobs))]
for i, job in enumerate(jobs):
    release = job['release']
    deadline = job['deadline']
    duration = job['duration']
    num = release

    while (num + duration <= deadline):
        intervals[i].append((num, num + duration))
        num += 1

# This establishes the height of each job
# This can be accessed later during the execution of the linear program
height = [job['height'] for job in jobs]

# This represents each distinct time step
# It could be easily replaced with a set integer representing the number of time steps
# In a certain period
# times = [i for i in range(8)]
num_time_steps = 10

# This list will represent the value of the resource curve at each distinct time step
# However, for now, it will be left 0 for all time steps for the purposes of debugging
# resources = [0 for _ in range(num_time_steps)]
resources = [0, 1, 1, 3, 4, 3, 3, 2, 0, 0]

# This creates a list of objects with the form {'name': x_i_j, value: ?}
# where each name is a distinct time interval for a distinct job
# Specifically, this is saying that decisino variable x_i_j is the ith possible interval for job j 
# where the value is the actual interval of time steps. This is stored here so we don't have to repeatedly query the intervals list
decision_variables = []
for j, interval_set in enumerate(intervals):
    for i, interval in enumerate(interval_set):
        decision_variables.append({'name' : f'x_{i}_{j}', 'value': interval})

# This is the name of the objective variable that we will minimize
objective_variable = 'd'


"""
Solve the ILP - with cplex
"""
# Create the cplex problem
problem = cplex.Cplex()
problem.set_problem_type(cplex.Cplex.problem_type.LP)
problem.set_results_stream(None)

# Maximize objective
problem.objective.set_sense(problem.objective.sense.minimize)

# This retrieves the names of all of the decision variables 
names = [variable['name'] for variable in decision_variables] + [objective_variable]

# these are the other parameters needed to form the basis of the linear programming problem
obj = [0 for _ in range(len(decision_variables))] + [1]# only minimizing d
lb = [0 for _ in range(len(decision_variables))] + [0]
ub = [1 for _ in range(len(decision_variables)) ] + [sum(height)]#[max(height)]  # d is bounded [0, 4]

# Establish the problem
types = [problem.variables.type.integer] * (len(decision_variables)) + [problem.variables.type.continuous]
problem.variables.add(obj=obj, lb=lb, ub=ub, types=types, names=names)


# --- Add constraints ---

# This for loop adds the constraints that make it so that a job can run during only one interval 
# So for each job, aggregate all of the decision variables that correspond to each possible execution interval for that job
# Then specify that they all of those decision variables can only add up to one 
curr_index = 0
for i, interval in enumerate(intervals):
    if i == 0:
        variables = decision_variables[i : i + len(interval)]
        variables = [v['name'] for v in variables]
        curr_index += len(interval)
    elif i > 0:
        variables = decision_variables[curr_index : curr_index + (len(interval))]
        variables = [v['name'] for v in variables]
        curr_index += len(interval)
    
    # The coefficient of each decision variable is one
    constraints = [1 for _ in range(len(variables))]

    # This is saying that the sum of each of the decision variabels can only equal one
    problem.linear_constraints.add(
        lin_expr=[ [ variables, constraints ] ],
        senses=['E'],
        rhs=[1]
    )
    


# Timestamp constraints:
# This for loop establishes the timestamp constraints
# It aggregates all of the desicion variables that correspond to intervals that could possibly be running during that time step
# It then aggregates the heights corresponding to the jobs that each decision variable represents. 
# It multiplies those heights by the decision variables
# However, the constrain ensures that the total sum is less than the max height d
for i in range(num_time_steps):
    use_variables = []
    use_height = []

    for variable in decision_variables:
        
        # Check the interval times of the corresponding variable
        # Then check if the current timestep falls within that interval
        job_interval_start, job_interval_end = variable['value'][0], variable['value'][1]

        # if i >= job_interval_start and i <= job_interval_end: #COME BACK TO THIS
        if job_interval_start <= i < job_interval_end:
            job_id = int(variable['name'].split('_')[-1])

            use_height.append(height[job_id])
            use_variables.append(variable['name'])

    # Add d to the decision variables 
    use_variables.append('d')
    use_height.append(-1)

    # print(use_variables, use_height)

    # Add the linear constraint to the problem
    problem.linear_constraints.add(
        lin_expr=[ [ use_variables, use_height ] ],
        senses=['L'],
        rhs=[resources[i]]
    )


# --- Solve the model ---
problem.solve()

# --- Output solution ---
solution = problem.solution
print("Status:", solution.get_status_string())
print("Objective value:", solution.get_objective_value())

# for name in names:
#     val = solution.get_values(name)
#     if val == 1 and name != 'd':
#         job_id = int(name.split('_')[-1])
#         interval_id = int(name.split('_')[1])
#         print(f"Job {job_id} interval: {intervals[job_id][interval_id]}")
#     # print(f"{name} = {val}")
