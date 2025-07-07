import random
import json
import csv
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


def choose_naive_schedule(jobs, num_time_steps, start_time, end_time):
    naive_heights = [0 for _ in range(num_time_steps)]
    for job in jobs:
        aj = job['release'] - start_time
        hj = job['height']
        lj = job['length']

        for i in range(aj, aj + lj):
            naive_heights[i] += hj
    
    return naive_heights


def solve_pdac_naive(jobs_array, resources, start_time, end_time, max_length, batch_size):
    num_time_steps = end_time - start_time

    jobs = generate_jobs(jobs_array, start_time, end_time, max_length, batch_size)

    final_heights = choose_naive_schedule(jobs, num_time_steps, start_time, end_time)

    objective_value = 0
    for i, height in enumerate(final_heights):
        if height - resources[i] > objective_value:
            objective_value = height - resources[i]

    # print("Greedy Objctive Value:", objective_value)
    return objective_value