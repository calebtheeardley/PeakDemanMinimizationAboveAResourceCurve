import json
import random

from plot_jobs import create_graph

"""
An important thing to note is that each instance is its own isolated test case
So it may not be valid to take multiple job objects from different instances into one test case for our algorithm
"""
batch_size = int(input("Job batch size: "))
start_time = int(input("Start time boundary: "))
end_time = int(input("End time boundary: "))

def get_jobs(batch_size, start_time, end_time):
    """
    Given a batch size of X, loop through instance files with block count of 1 (for now)
    until the job batch size reaches the specified batch size
    """
    job_batch_size = 0
    job_array = []

    file_num = 0
    files = [i for i in range(1, 1765)]
    random.shuffle(files)
    while (job_batch_size < batch_size):
        """
        Open a data file and check whether it has a block count of 1
        Then iterate through all of its job objects
        """
        path = f'../Data/instances/instance_{files[file_num]}.json'

        with open(path, 'r') as file:
            data = json.load(file)

        """
        If the block count is not 1, then we need to look through a different instance file
        """
        if data['additional']['generator__block_count'] != 1:
            file_num += 1
            continue

        for job_instance in data['jobs']:
            """
            Necessary Fields:
                Arrival time: aj
                Deadline time: dj
                Length of job: lj
                Height of job: hj
            """
            aj = job_instance['release']
            dj = job_instance['deadline']
            lj = job_instance['duration']
            hj = job_instance['usages']['0']

            if aj >= start_time and dj <= end_time:
                job_object = {"id": job_instance['id'], "release" : aj, "deadline": dj, "length": lj, "height": hj}
                job_array.append(job_object)

                job_batch_size += 1
            
            if job_batch_size >= batch_size:
                break
    
    return job_array

jobs = get_jobs(batch_size, start_time, end_time)
create_graph(jobs)
        





