"""
----- Calculate job schedules naively ----- 

This program is designed to generate a very naive schedule of jobs. It does this by taking each job in a given batch and simply scheduling it at the 
very first possible instance. In other words, it schedules each job at the job's start time. The purpose of this algorithm is to compare its results
to those of the more efficient / specialized ones such as the ILP and relaxed LP
"""


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
*   batch_size (int) -> The size of the batch
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

            flexible_object = {**job_id, **jobs_array[curr_index]}
            jobs.append(flexible_object)
            
            i += 1
        
        curr_index += 1

    return jobs


"""
----- Get the job heights of the schedule -----

* choose_naive_schedule -> This function generates a list of heights for each discrete time step in the time period. 
*   Based off of the the naive schedule
* 
* INPUTS
*   jobs (list) -> The list of jobs to be scheduled
*   num_time_steps (int) -> The number of discrete time steps
*   start_time (int) -> The earliest possible time steps for each job
"""
def choose_naive_schedule(jobs, num_time_steps, start_time):
    naive_heights = [0 for _ in range(num_time_steps)]
    for job in jobs:
        aj = job['release'] - start_time
        hj = job['height']
        lj = job['length']

        # Add the height of the job beginning at it's start time
        for i in range(aj, aj + lj):
            naive_heights[i] += hj
    
    return naive_heights


"""
* solve_pdac_naive -> This function takes in the given parameters and jobs to calculate a simple naive schedule.
* 
* INPUTS 
*   jobs_array (list) -> An unfiltered array of all of the possible jobs available for scheduling
*   resources (list) -> A list of height values representing the amount of available resources at each discrete time step
*   start_time (int) -> The earliest possible starting time for each job
*   end_time (int) -> The latest possible ending time for each job
*   max_length (int) -> The maximum length of a given job
*   batch_size (int) -> The number of jobs that should be included in the schedule
"""
def solve_pdac_naive(jobs_array, resources, start_time, end_time, max_length, batch_size):
    # Calculate the number of time steps
    num_time_steps = end_time - start_time

    # Generate a list of jobs of size batch_size based on the provided parameters
    jobs = generate_jobs(jobs_array, start_time, end_time, max_length, batch_size)

    # Get the list of job heights in the schedule
    final_heights = choose_naive_schedule(jobs, num_time_steps, start_time, end_time)

    # Calculate the final objective value (PDAC) based on these heights and the resource curve
    objective_value = 0
    for i, height in enumerate(final_heights):
        if height - resources[i] > objective_value:
            objective_value = height - resources[i]

    return (objective_value, final_heights)