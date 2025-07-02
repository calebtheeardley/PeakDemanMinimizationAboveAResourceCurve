import cplex
import random
import json
import math

"""
* generate_jobs -> This function takes in a random sample of jobs and returns a list of job objects. This function also selects 
*   these jobs based on the given input parameters
* 
* INPUTS
*   jobs_array (List) -> an unsorted list of all of the jobs available to the user
*   start_time (int) -> The time after which all jobs must start
*   end_time (int) -> The time by which all jobs must end
*   max_length (int) -> The maximum duration of a given job
* 
* ADDITIONAL
* This function will select the jobs based on the parameters. However, it should not select different jobs than other algorithms becuase they will all
* be provided with the same jobs_array list and parameters
"""
def generate_jobs(jobs_array, start_time, end_time, max_length, batch_size):
    jobs = []

    # Iterate through the job objects and create an array of objects that fall within the specified time window
    i = 0
    curr_index = 0
    while (i < batch_size):
        aj = jobs_array[curr_index]['release']
        dj = jobs_array[curr_index]['deadline']
        lj = jobs_array[curr_index]['length']

        # Check if the specific job lies within the correct window
        # The funky syntax is used to put the job id at the very front of the dictionary
        if aj >= start_time and dj <= end_time and lj <= max_length:
            job_id = {"job_id" : i}
            job_object = {**job_id, **jobs_array[curr_index]}
            jobs.append(job_object)
            
            i += 1
        
        curr_index += 1

    return jobs


"""
* get_job_intervals -> This function is responsible for going through each of the jobs in the algorithm and returning all the intervals 
*   that the job could possibly run within
* 
* INPUTS
*   jobs (list) -> This is the list of jobs in this case
"""
def get_job_intervals(jobs, start_time):
    intervals = [[] for _ in range(len(jobs))]
    for i, job in enumerate(jobs):
        # Extract the necessary information from the job object
        release = job['release'] - start_time
        deadline = job['deadline'] - start_time
        duration = job['length']
        num = release

        # Add the execution intervals to the sublist
        while (num + duration <= deadline):
            intervals[i].append((num, num + duration))
            num += 1

    return intervals



"""
* get_job_heights -> This function returns a list of the height of each respective job. The index of the job height corresponds to the 
*   jobs id
* 
* INPUTS
*   jobs (list) -> The list of jobs for the trial
"""
def get_job_heights(jobs):
    height = [job['height'] for job in jobs]

    return height




"""
* generate_decision_variables -> This function generates a list of all of the decision variables for the ILP
* 
* INPUTS
*   intervals (list) -> This is the list of the intervals that each job can run within
* 
* ADDITIONAL
    - This code creates a list of decision variables with the form {'name': x_i_j, value: ?} where each name is a distinct time interval for a distinct job.
    - Specifically, this is saying that decision variable x_i_j is the ith possible interval for job j where the value is the actual interval of time steps.
    - This is stored here so we don't have to repeatedly query the intervals list
"""
def generate_decision_variables(intervals):
    decision_variables = []
    for j, interval_set in enumerate(intervals):
        for i, interval in enumerate(interval_set):
            # Add the decision variable and it's corresponding interval to the list
            decision_variables.append({'name' : f'x_{i}_{j}', 'value': interval})
    
    return decision_variables



"""
* generate_ilp -> This creates an ILP CPLEX instance
* 
* INPUTS
*   decision_variables (list) -> This is the list of all of the decision variables in the ILP
*   height (list) -> This list of job heights for each job in the trial
*   num_time_steps (int) -> The number of discrete time steps in the period
"""
def generate_ilp(decision_variables, height, num_time_steps): 
    # Create the cplex problem
    problem = cplex.Cplex()
    problem.set_problem_type(cplex.Cplex.problem_type.LP)
    problem.set_results_stream(None)

    # Maximize objective
    problem.objective.set_sense(problem.objective.sense.minimize)

    # This is the name of the objective variable that we will minimize
    objective_variables = [f'n_{i}' for i in range(num_time_steps)]

    # This retrieves the names of all of the decision variables 
    names = [variable['name'] for variable in decision_variables] + objective_variables

    max_height = sum(height)

    # these are the other parameters needed to form the basis of the linear programming problem
    obj = [0 for _ in range(len(decision_variables))] + [1 for _ in range(len(objective_variables))] 
    lb = [0 for _ in range(len(decision_variables))] + [0 for _ in range(len(objective_variables))]
    ub = [1 for _ in range(len(decision_variables)) ] + [max_height for _ in range(len(objective_variables))]

    # Establish the problem
    types = [problem.variables.type.continuous] * (len(decision_variables)) + [problem.variables.type.continuous] * (len(objective_variables))
    problem.variables.add(obj=obj, lb=lb, ub=ub, types=types, names=names)

    return problem


"""
* generate_contraints -> This function generates and applies the necessary linear constraints to the ILP instance
* 
* INPUTS
*   decision_variables (list) -> This is the list of all of the decision variables in the ILP
*   height (list) -> This list of job heights for each job in the trial
*   intervals (list) -> The list of intervals that each respective job can run in
*   problem (CPLEX problem) -> The CPLEX problem instance
* 
* ADDITIONAL
* This function does not have a return value. It's job is to apply the constraints to the problem
"""

def generate_constraints(resources, decision_variables, height, intervals, problem, num_time_steps):
    """
    This will generate the first set of constraints

    This for loop adds the constraints that make it so that a job can run during only one interval. So for each job, aggregate all of the decision variables that correspond to each possible execution interval for that job. 
    Then specify that they all of those decision variables can only add up to one
    """
    curr_index = 0
    for interval in intervals:
        # Aggregate all the decision variables that belong to one job
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


    """
    This generates the second set of constraints

    It aggregates all of the desicion variables that correspond to intervals that could possibly be running during that time step.
    It then aggregates the heights corresponding to the jobs that each decision variable represents. It multiplies 
    those heights by the decision variables. However, the constrain ensures that the total sum is less than the max height d
    """
    for i in range(num_time_steps):
        use_variables = []
        use_height = []

        for variable in decision_variables:
            
            # Check the interval times of the corresponding variable
            # Then check if the current timestep falls within that interval
            job_interval_start, job_interval_end = variable['value'][0], variable['value'][1]

            if job_interval_start <= i < job_interval_end:
                job_id = int(variable['name'].split('_')[-1])

                use_height.append(height[job_id])
                use_variables.append(variable['name'])

        # Add the objective variable corresponding to this time step to the decision variables 
        use_variables.append(f'n_{i}')
        use_height.append(-1)

        # Add the linear constraint to the problem
        problem.linear_constraints.add(
            lin_expr=[ [ use_variables, use_height ] ],
            senses=['L'],
            rhs=[resources[i]]
        )


"""
* choose_relaxed_schedule -> This function chooses a schedule probabailistically based on the results of the LP solution
* 
* INPUTS
*   decision_variables (list) -> This is the list of all of the decision variables in the ILP
*   height (list) -> This list of job heights for each job in the trial
*   intervals (list) -> The list of intervals that each respective job can run in
*   problem (CPLEX problem) -> The CPLEX problem instance
"""
def choose_relaxed_schedule(decision_variables, intervals, num_time_steps, height, problem):
    problem.solve()
    solution = problem.solution


    # Loop through each of the jobs and generate a random number
    # Choose a decision variable based on the probability of the current value of the decision variables
    # Add that chosen variable to a final list so that the overall objective value can be ascertained
    final_intervals = []
    final_heights = [0 for _ in range(num_time_steps)]

    curr_index = 0
    # Loop through each job
    for job_id in range(len(intervals)):
        # Generate a random number for the job to be used to select a specific interval
        random_num = random.uniform(0, 1)
        probability = 0

        # Loop through each interval in the job and get the value corresponding to each interval (decision variable)
        # Add the decision variable to the final interval list based on the random number 
        for i, interval in enumerate(intervals[job_id]):
            decision_variable = decision_variables[curr_index]
            decision_value = solution.get_values(decision_variable['name'])
            probability += decision_value

            if random_num <= probability and len(final_intervals) <= job_id:
                final_intervals.append(decision_variable)
            
            curr_index += 1

    # Generate the height of all of the jobs over the course of all of the time steps
    # Do this by iterating through all of the selected job intervals in final_intervals and add their height values 
    # to the final_heights arrays. From this we can determine the objective value of d
    # simply take the maximum from this height list
    for job_id, job in enumerate(final_intervals):
        job_start = job['value'][0]
        job_end = job['value'][1]
        job_height = height[job_id]

        for i in range(job_start, job_end):
            final_heights[i] += job_height

    return final_heights



"""
* solve_lp -> This function solves the provided LP instance
* 
* INPUTS 
*   problem -> The CPLEX ILP instance
"""
def solve_aac_lp(jobs_array, resources, start_time, end_time, max_length, batch_size):
    # Specify the number of time steps 
    num_time_steps = end_time - start_time

    # Generate the jobs
    jobs = generate_jobs(jobs_array, start_time, end_time, max_length, batch_size)

    # Generate the intervals
    intervals = get_job_intervals(jobs, start_time)

    # Get the job heights
    height = get_job_heights(jobs)

    # Generate the decision variables
    decision_variables = generate_decision_variables(intervals)

    # Instantiate the CPLEX ILP
    problem = generate_ilp(decision_variables, height, num_time_steps)

    # Apply the linear constraints to the problem
    generate_constraints(resources, decision_variables, height, intervals, problem, num_time_steps)

    # Choose the schedule
    final_heights = choose_relaxed_schedule(decision_variables, intervals, num_time_steps, height, problem)

    objective_value = 0
    for i, height in enumerate(final_heights):
        if height - resources[i] > objective_value:
            objective_value = height - resources[i]


    # print("Greedy Objctive Value:", objective_value)
    return objective_value
