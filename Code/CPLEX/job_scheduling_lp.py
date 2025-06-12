import cplex
import random
import json
import matplotlib.pyplot as plt
import numpy as np
import csv
import os

start_time = 0
end_time = 1400
max_length = 700

for batch_size in range(100, 600, 100):

    print(batch_size)

    for k in range(4):
        # This is The list of job objects that will be scheduled
        # They each have a release, deadline, duration and height
        path = '../../Input_Data/job_data.json'
        with open(path, 'r') as file:
            data = json.load(file)

        # Randomly shuffle the jobs so that there is variation between trials
        jobs_array = data['jobs']
        random.shuffle(jobs_array)

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


        # Specify the number of time steps 
        num_time_steps = end_time - start_time


        # Instantiate the resource curve

        path = '../../Input_Data/solar_data.json'
        with open(path, 'r') as file:
            data = json.load(file)

        wind_energy = data['series'][1]['data']
        solar_energy = data['series'][2]['data']
        hydro_energy = data['series'][3]['data']

        # Have 165 hours and you want minute by minute resolution. Therefore the total length of this list needs to be 165 * 60 in length
        # The first 60 values of the list need to equal 0, the next need to equal 1. Therefore, i // 60
        wind_energy_7_days = [0 for _ in range(165 * 60)]
        for i in range(len(wind_energy_7_days)):
            wind_energy_7_days[i] = wind_energy[ i // 60 ]['value']

        solar_energy_7_days = [0 for _ in range(165 * 60)]
        for i in range(len(solar_energy_7_days)):
            solar_energy_7_days[i] = solar_energy[ i // 60 ]['value']

        hydro_energy_7_days = [0 for _ in range(165 * 60)]
        for i in range(len(hydro_energy_7_days)):
            hydro_energy_7_days[i] = hydro_energy[ i // 60 ]['value']


        total = []
        for i in range(165 * 60):
            total_sum = wind_energy_7_days[i] + solar_energy_7_days[i] + hydro_energy_7_days[i]
            total.append(total_sum)

        day = 3
        resources = total[(24 * day) + start_time : (24 * day) + end_time]


        bad_heights = [0 for _ in range(num_time_steps)]
        for job in jobs:
            aj = job['release'] - start_time
            hj = job['height']
            lj = job['length']

            for i in range(aj, aj + lj):
                bad_heights[i] += hj


        scale_factor = (max(resources) * 2) / max(bad_heights)

        # Iterate through the jobs and add their corresponding heights
        height = [job['height'] * scale_factor for job in jobs]


        decision_variables = []
        for j, interval_set in enumerate(intervals):
            for i, interval in enumerate(interval_set):
                # Add the decision variable and it's corresponding interval to the list
                decision_variables.append({'name' : f'x_{i}_{j}', 'value': interval})

        # This is the name of the objective variable that we will minimize
        objective_variable = 'd'


        # Create the cplex problem
        problem = cplex.Cplex()
        problem.set_problem_type(cplex.Cplex.problem_type.LP)
        problem.set_results_stream(None)

        # Maximize objective
        problem.objective.set_sense(problem.objective.sense.minimize)

        # This retrieves the names of all of the decision variables 
        names = [variable['name'] for variable in decision_variables] + [objective_variable]

        # these are the other parameters needed to form the basis of the linear programming problem
        obj = [0 for _ in range(len(decision_variables))] + [1] # only minimizing d
        lb = [0 for _ in range(len(decision_variables))] + [0]
        ub = [1 for _ in range(len(decision_variables)) ] + [sum(height)]


        # Establish the problem
        types = [problem.variables.type.continuous] * (len(decision_variables)) + [problem.variables.type.continuous]
        problem.variables.add(obj=obj, lb=lb, ub=ub, types=types, names=names)


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

            # Add d to the decision variables 
            use_variables.append('d')
            use_height.append(-1)

            # Add the linear constraint to the problem
            problem.linear_constraints.add(
                lin_expr=[ [ use_variables, use_height ] ],
                senses=['L'],
                rhs=[resources[i]]
            )


        print("start solve")
        problem.solve()
        solution = problem.solution
        print("end solve")


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


        objective_value = 0
        for i, height in enumerate(final_heights):
            if height - resources[i] > objective_value:
                objective_value = height - resources[i]

        print("Inexact Objective Value:", objective_value)

        naive_objective_value = 0
        for i, height in enumerate(bad_heights):
            if (height * scale_factor) - resources[i] > naive_objective_value:
                naive_objective_value = (height * scale_factor) - resources[i]

        print("Naive Objective Value:", naive_objective_value)

        # Write to a data csv file
        data = [
            {"batch_size": batch_size,"trial #": k, "naive obective val": naive_objective_value, "inexact objective val": objective_value}
        ]

        with open(f"../../Output_Data/Results/objective_values_{batch_size}.csv", "a", newline="") as csvfile:
            fieldnames = ['batch_size', 'trial #', 'naive obective val', 'inexact objective val']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if k == 0:
                writer.writeheader()
            writer.writerows(data)

            csvfile.close()


        # job_graph_xvalues = np.array([i for i in range(start_time, end_time)])

        # job_graph_yvalues = np.array(final_heights)
        # bad_job_graph_yvalues = np.array([height * scale_factor for height in bad_heights])
        # resources_graph_yvalues = np.array(resources)

        # plt.plot(job_graph_xvalues, bad_job_graph_yvalues, label='naive jobs', color='green')
        # plt.plot(job_graph_xvalues, job_graph_yvalues, label='inexact jobs')
        # plt.plot(job_graph_xvalues, resources_graph_yvalues, label='resources', color='orange')


        # plt.xlabel("Time")
        # plt.ylabel("Power Units")
        # plt.legend()

        # def save_figure_safely(path):
        #     os.makedirs(os.path.dirname(path), exist_ok=True)
        #     plt.savefig(path)

        # # Usage
        # save_figure_safely(f"../../Output_Data/Figures/Job_Size_{batch_size}/Trial_{k}.jpg")

        # plt.show()