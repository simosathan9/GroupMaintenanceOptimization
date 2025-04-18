## Repository Structure

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

* Use this to author the BSc thesis https://chatgpt.com/c/68021bfc-1768-8000-b0af-14aa9d9e8c04
