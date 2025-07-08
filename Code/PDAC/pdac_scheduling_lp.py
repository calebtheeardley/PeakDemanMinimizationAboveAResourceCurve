"""
----- Calculate Job Power Schedules with LP -----

This program is designed to take in n number of distinct power scheduling jobs and determine their ideal ordering in to minimize 
the peak amount of power demand above a provided resource curve.
This is a relaxed ILP problem. Therefore, it uses typical LP to solve the problem in polynomial time and then probability to estimate 
the optimal schedule of jobs.
"""
import cplex
import random
from collections import defaultdict



"""
----- Generate a list of jobs -----

* generate_jobs -> This function takes in a random sample of jobs and returns a list of job objects. This function also selects 
*   these jobs based on the given input parameters
* 
* INPUTS
*   jobs_array (List) -> an unsorted list of all of the jobs available to the user
*   start_time (int) -> The time after which all jobs must start
*   end_time (int) -> The time by which all jobs must end
*   max_length (int) -> The maximum duration of a given job
*   batch_size (int) -> The size of the job batch so be created
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
----- Generate a list of job intervals -----

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
----- Get the height of each job -----

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
----- Generate a list of LP decision variables ----- 

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
"""
def generate_ilp(decision_variables, height): 
    # Create the cplex problem
    problem = cplex.Cplex()
    problem.set_problem_type(cplex.Cplex.problem_type.LP)
    problem.set_results_stream(None)

    # Maximize objective
    problem.objective.set_sense(problem.objective.sense.minimize)

    # This is the name of the objective variable that we will minimize
    objective_variable = 'd'

    # This retrieves the names of all of the decision variables 
    names = [variable['name'] for variable in decision_variables] + [objective_variable]

    # these are the other parameters needed to form the basis of the linear programming problem
    obj = [0 for _ in range(len(decision_variables))] + [1] # only minimizing d
    lb = [0 for _ in range(len(decision_variables))] + [0]
    ub = [1 for _ in range(len(decision_variables)) ] + [sum(height)]


    # Establish the problem
    # *** Here the variables are set to a 'continuous' type. So they can assume any value in [0, 1] *** 
    types = [problem.variables.type.continuous] * (len(decision_variables)) + [problem.variables.type.continuous]
    problem.variables.add(obj=obj, lb=lb, ub=ub, types=types, names=names)

    return problem



"""
----- Generate the LP constraints -----

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
    those heights by the decision variables. However, the constraint ensures that the total sum is less than the max height d
    """
    # Preprocessing to make data lookup more efficient (using a hashmap)
    # Go through each decision variable and its corresponding interval and add the decision variable to each time step during which 
    # the job is (possibly) active
    time_to_jobs = defaultdict(list)
    for variable in decision_variables:
        job_id = int(variable['name'].split('_')[-1])
        job_start, job_end = variable['value'][0], variable['value'][1]

        for t in range(job_start, job_end):
            time_to_jobs[t].append((variable['name'], height[job_id]))
    
    # Go through each time step in the time period
    # Get each decision variable for that time step and add it to a running ILP constraint equation
    for i in range(num_time_steps):
        use_variables = []
        use_height = []

        for var_name, height in time_to_jobs.get(i, []):
            use_variables.append(var_name)
            use_height.append(height)
        
        use_variables.append('d')
        use_height.append(-1)

        # Add constraint
        # This constraint says that for all of the decision variables multiplied by their height at a specific time step
        # should not sum to more than the objective variable d.
        problem.linear_constraints.add(
            lin_expr=[[use_variables, use_height]],
            senses=['L'],
            rhs=[resources[i]]
        )


"""
----- Get the job heights from the schedule -----

* choose_relaxed_schedule -> This function chooses a schedule probabailistically based on the results of the LP solution
* 
* INPUTS
*   decision_variables (list) -> This is the list of all of the decision variables in the ILP
*   height (list) -> This list of job heights for each job in the trial
*   intervals (list) -> The list of intervals that each respective job can run in
*   problem (CPLEX problem) -> The CPLEX problem instance
"""
def choose_relaxed_schedule(decision_variables, intervals, num_time_steps, height, problem):
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
* solve_pdac_lp -> This function creates and solves a relaxed LP problem to schedule a jobs 
*   returns the objective value and schedule of job heights
* 
* INPUTS 
*   jobs_array (list) -> An unfiltered array of all of the possible jobs available for scheduling
*   resources (list) -> A list of height values representing the amount of available resources at each discrete time step
*   start_time (int) -> The earliest possible starting time for each job
*   end_time (int) -> The latest possible ending time for each job
*   max_length (int) -> The maximum length of a given job
*   batch_size (int) -> The number of jobs that should be included in the schedule
"""
def solve_pdac_lp(jobs_array, resources, start_time, end_time, max_length, batch_size):
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
    problem = generate_ilp(decision_variables, height)

    # Apply the linear constraints to the problem
    generate_constraints(resources, decision_variables, height, intervals, problem, num_time_steps)

    # Solve the relaxed LP
    problem.solve()

    # Get the heights of the jobs at each time step in the schedule
    final_heights = choose_relaxed_schedule(decision_variables, intervals, num_time_steps, height, problem)

    # Calculate the final objective value (PDAC) based on these heights and the resource curve
    objective_value = 0
    for i, height in enumerate(final_heights):
        if height - resources[i] > objective_value:
            objective_value = height - resources[i]

    return (objective_value, final_heights)