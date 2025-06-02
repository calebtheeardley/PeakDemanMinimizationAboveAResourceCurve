import json
import random
import csv

from plot_jobs import create_graph

"""
*********
    An important thing to note is that each instance is its own isolated test case
    So it may not be valid to take multiple job objects from different instances into one test case for our algorithm
*********
 """


"""
* get_jobs -> Given inputs regarding batch size, start time and end time, scrape the job instances files
    to accumulate job objects
*
* INPUTS 
* batch_size (int) -> The number of jobs to be scraped (0 - 1000)
* start_time (int) -> The minimum release time of all jobs (must be between 0 - 1440)
* end_time (int) -> The maximum deadline of all jobs (must be between 0 - 1440)

* OUTPUTS
* job_array (list[dict]) -> A list of job objects with the following structure
    {job_id, release, deadline, length, height}
"""
def get_jobs(batch_size, start_time, end_time):
    
    # Create a variable to keep track of the current batch size of the jobs that have been scraped so far
    # Additionally, initialize the array to hold the different job objects
    job_batch_size = 0
    job_array = []

    # Shuffle the instance files to get semi-random job combinations each execution
    file_num = 0
    files = [i for i in range(1, 1765)]
    random.shuffle(files)

    while (job_batch_size < batch_size):
        # Open the instance file with the current file_num extension
        path = f'../Data/instances/instance_{files[file_num]}.json'
        with open(path, 'r') as file:
            data = json.load(file)

        # Continue to look for another file if the instance file's block count is greater than 1
        # this means that there will be jobs with dependencies
        if data['additional']['generator__block_count'] != 1:
            file_num += 1
            continue

        for job_instance in data['jobs']:
            # Necessary Fields:
            #     Arrival time: aj
            #     Deadline time: dj
            #     Length of job: lj
            #     Height of job: hj
            aj = job_instance['release']
            dj = job_instance['deadline']
            lj = job_instance['duration']
            hj = job_instance['usages']['0']

            # If the job's interval lies within the specified start and end interval
            # add it to the array
            if aj >= start_time and dj <= end_time:
                job_object = {"job_id": job_batch_size, "release" : aj, "deadline": dj, "length": lj, "height": hj}
                job_array.append(job_object)

                job_batch_size += 1
            
            # Check whether we have reached the specified batch size
            if job_batch_size >= batch_size:
                break

        # Iterate to the next file
        file_num += 1

    # Return the array of job objects
    return job_array

"""
* get_jobs_aggregated -> Given inputs regarding batch size, start time and end time, scrape the job_data.json file 
    with all of the zero dependency job objects to accumulate a dataset to work with
*
* INPUTS 
* batch_size (int) -> The number of jobs to be scraped (0 - 1000)
* start_time (int) -> The minimum release time of all jobs (must be between 0 - 1440)
* end_time (int) -> The maximum deadline of all jobs (must be between 0 - 1440)

* OUTPUTS
* job_array (list[dict]) -> A list of job objects with the following structure
    {job_id, release, deadline, length, height}
"""
def get_jobs_aggregated(batch_size, start_time, end_time):

    # Open the job_data.json file 
    path = '../Data/job_data.json'
    with open(path, 'r') as file:
        data = json.load(file)
    
    # Randomly shuffle the jobs so that there is variation between trials
    jobs = data['jobs']
    random.shuffle(jobs)

    job_array = []

    # ** Maybe add a check to see if the batch size will be out of bounds ** 
    # Iterate through the job objects and create an array of objects that fall within the specified time window
    for i in range(batch_size):
        aj = jobs[i]['release']
        dj = jobs[i]['deadline']

        # check if the specific job lies within the correct window
        if aj >= start_time and dj <= end_time:
            jobs[i]['job_id'] = i
            job_array.append(jobs[i])
    
    # Return the array of job objects
    return job_array


"""
* write_jobs -> Write the scraped jobs to a local csv file, based on user specified parameters
*
* INPUTS 
* None
* 
* OUPUT
* None
"""
def write_jobs():

    # Get the preferred batch size, release time minimum and deadline time maximum
    batch_size = int(input("Job batch size: "))
    start_time = int(input("Start time boundary: "))
    end_time = int(input("End time boundary: "))

    # Gather jobs based on these user specifications
    for i in range(5):
        jobs = get_jobs(batch_size, start_time, end_time)
        create_graph(jobs, "instance_jobs_", i)

    for i in range(5):
        jobs = get_jobs_aggregated(batch_size, start_time, end_time)
        create_graph(jobs, "aggregated_jobs_", i)

    # Open a csv file and write the gathered data to it
    # with open('../job_data.csv', mode='w', newline='') as csvfile:
    #     fieldnames = ['job_id', 'release', 'deadline', 'length', 'height']
    #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    #     writer.writeheader()
    #     writer.writerows(jobs)


if __name__ == "__main__":
    write_jobs()
        





