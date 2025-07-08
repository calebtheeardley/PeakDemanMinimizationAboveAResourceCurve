# Power Job Scheduling Under a Resource Curve

## ** Code **

This folder contains all of the necessary code to scrape power jobs from an existing database, schedule those jobs using a variety of algorithms <br>
and generate analytical visuals of the performance of each of those algorithms. This folder is where the bulk of the project lives.

### AAC

This folder houses all of the code used to generate a power job schedule by focusing on minimizing the total job power area above the curve (AAC). <br>
The code in this folder is still a work in progress. Therefore, it's algorithms and code still have some bugs that are yet to be resolved. <br>
<br>
&emsp;&emsp; ** aac_scheduling_ilp.py ** -- This program is desined to schedule jobs based off of a Integer Linear Program (ILP) that minimizes the total area above the curve <br>
&emsp;&emsp; ** aac_scheduling_lp.py ** -- This program relaxes the previous ILP into an LP so that it can be solved in polynomial time. It then uses probability to schedule each of the jobs. Each probability is calculated by the LP

### PDAC

### Data Visualization

### Job Scraping

## ** Input Data **

## ** Output Data **
