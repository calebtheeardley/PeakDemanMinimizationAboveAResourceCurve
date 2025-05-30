import matplotlib.pyplot as plt
import numpy as np

def create_graph(jobs):
    time_array = [0 for _ in range(1440)]
    for job_object in jobs:
        aj = job_object['release']
        dj = job_object['deadline']
        lj = job_object['length']
        hj = job_object['height']

        for i in range(aj, aj + lj + 1):
            time_array[i] += hj

    graph_xvalues = np.array([i for i in range(1440)])
    graph_yvalues = np.array(time_array)

    # Create Bar Graph (Vertical)
    plt.bar(graph_xvalues, graph_yvalues, color='skyblue')

    # Add Labels and Title
    plt.xlabel("Time")
    plt.ylabel("Energy Units")
    plt.title("Job Power Usage")

    plt.show()
    

            

