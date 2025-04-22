# Group Maintenance Problem

This repository contains a solution to the Group Maintenance Problem, where components are grouped to optimize maintenance costs.

## Project Structure

The codebase is organized into modular components to support future development:

- `component.py`: Component class representing machinery components to be maintained
- `production_line.py`: ProductionLine class representing manufacturing lines
- `group.py`: Group class representing a grouping of components for maintenance
- `solution.py`: Solution class representing a complete maintenance solution
- `instance_reader.py`: Utility class for reading data from CSV and Excel files

### Mathematical and Analysis Modules

- `cost_functions.py`: Core cost calculation functions (cost rate, phi, etc.)
- `group_analysis.py`: Group analysis functions (economic profit, feasible intervals, etc.)
- `visualizations.py`: Visualization functions for cost analysis and group economic profit

### Main Execution

- `solver.py`: Main execution script that ties together all modules

## Data Files

- `synthetic_maintenance_data_with_duration.csv`: Synthetic data for components

## Usage

To run the analysis:

```bash
python solver.py
```

## Visualization Examples

The code supports multiple visualization types:

1. Cost rate function for individual components
2. Optimal execution time distribution
3. Group economic profit analysis

The visualizations help in understanding the economic impacts of different grouping strategies.

## Domain Structure

Automotive Plant contains a list with all production lines.
Each production line contains a list with the components that belong to it.

Component is considered the fundamental unit of our problem. Each component is accompanied by its costs (corrective and preventive), optimal execution times etc.

Solution objects represents a list of groups. A group contains various components. Each group is accompanied by its cost, begin and ending time etc.


## What Assumptions I am doing now/ Considerations
* Consider sequential execution of maintenance activities thus total duration of group maintenance equals the sup of the indiviual durations
* Consider Long Term Shift thus I use this to calculate the penalty `phi_plus - phi_star - delta_t * component.long_term_cost_rate`
* When there is sequential maintenance there are no downtime cost savings, the downtime actually is zero
* Not sure what holds regarding the updates of the future execution times. As Prof. Mourtos said components are grouped only once based on their x* and their feasible intervals (Dekker says that there has to be an intersection of the intervals so that the grouping leads to economic profit)
* In my code I have identified non intersecting intervals that lead to economic profit but I observe that the interval boundaries are really close. Not sure
if it has to do with my code/calculations are it is just numerically feasible
* CONSIDERATIONS: Let's say that some components are grouped and the downtime is 10 units of time. How will the optimal execution times for components outside the group that share the same production line with a grouped component will be shifted ? Their deterioration is supposed to stop when the production line is down. How exactly should i update ? 
* Should I group PM actions or components ? What I mean is that if a component has an x*=50 then has to be maintained at 50,100,150,200 etc. Is the grouping for each component happening only once based on its optimal execution time ? Or every PM action has to be grouped ? That said a component might be grouped at time t_1 with different ones that will be grouped at time t_2. If the PM actions are grouped then the update of the execution times probably follows the rule set in equation 13.
* Discuss which penalty must be used to calculate the feasible interval for each component.

* PM duration for a group is calculated by executing components of the same production line in parallel — taking the maximum PM duration per line. Lines are handled sequentially, so the total group duration is the sum of these per-line maxima.

* Use this to author the BSc thesis https://chatgpt.com/c/68021bfc-1768-8000-b0af-14aa9d9e8c04
