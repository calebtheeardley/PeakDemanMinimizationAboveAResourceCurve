import json
import random

job_array = []
for i in range(1, 1765):
    path = f'../Data/instances/instance_{i}.json'
    with open(path, 'r') as file:
        data = json.load(file)
    
    if data['additional']['generator__block_count'] != 1:
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

        job_object = {"release" : aj, "deadline": dj, "length": lj, "height": hj}
        job_array.append(job_object)

json_data = {'jobs' : job_array}

with open('job_data.json', 'w') as file:
    json.dump(json_data, file)





