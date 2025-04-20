# Start by reading the data
from instance_reader import InstanceReader
from component import Component
from production_line import ProductionLine
from solution import Solution
from group import Group
import numpy as np

# Import from reorganized modules
from cost_functions import compute_optimal_x
from visualizations import plot_group_economic_profit, plot_feasible_interval_penalty
# Import group_analysis functions to avoid circular import
from group_analysis import (
    compute_group_economic_profit, 
    find_optimal_group_time, 
    update_component_schedule,
    find_feasible_interval,
    find_non_intersecting_pairs,
    compute_grouping_structure_cost,
)
# Import moved to avoid circular import
reader = InstanceReader("synthetic_maintenance_data_with_duration.csv")
# for each row in the data, create a component object and add it to the components list
components = []
production_lines = []
solution = Solution()
data = reader.read_data_csv().rename(columns={
    'Line': 'Production Line',
    'Component': 'ID',
    'MTBF': 'MTBF',
    'λ': 'Weibull_Parameter',
    'cp': 'Preventive_Specific_Cost',
    'cc': 'Corrective_Specific_Cost',
    'PM_duration': 'Duration',
    'x*': 'Optimal_Execution_Time',
    'CR': 'Long_term_Cost_Rate',
})
for index, row in data.iterrows():
    production_line = ProductionLine(row['Production Line'], 5, 3, 5)
    production_lines.append(production_line)

def get_production_line_by_id(id):
    for production_line in production_lines:
        if production_line.id == id:
            return production_line
    return None

# It is necessary to have the production lines list in this file so that when set-up cost reduction occurs
# due to a component being added to a group we can retrieve the production line to which the component belongs and that stores the set-up cost

# In the same way we will calculate the downtime cost reduction as each production line is accompanied with its downtime cost rate
maintenance_durations = data['Duration'].tolist()
optimal_execution_times = data['Optimal_Execution_Time'].tolist()
for index, row in data.iterrows():
    component = Component(row['ID'], row['Duration'], row['Corrective_Specific_Cost'], row['Preventive_Specific_Cost'], get_production_line_by_id(row['Production Line']), row['Weibull_Parameter'], row['MTBF'], row['Optimal_Execution_Time'], row['Long_term_Cost_Rate'])
    components.append(component)
    # Print the components
    print(component.__str__())

for component in components:
    cc = component.corrective_maintenance_cost # includes production line setup cost
    cp = component.preventive_maintenance_cost # includes production line setup cost and downtime cost
    mtbf = component.mean_time_between_failures
    lambd = component.lamda_efr
    d = component.preventive_maintenance_duration  # duration of PM

    x_opt, cr_opt = compute_optimal_x(cp, cc, mtbf, lambd, d)
    component.optimal_execution_time = x_opt
    component.long_term_cost_rate = cr_opt
    
    # We will use the optimal execution time to calculate the exact times for the Planning Horizon
    schedule = []
    t = x_opt
    while t <= 365:
        schedule.append(round(t, 2))
        t += x_opt  # Next execution after x_opt days
    component.execution_schedule = schedule

    print(f"Component {component.id}:")
    print(f"  Optimal x*: {x_opt:.2f}")
    print(f"  Cost Rate (CR): {cr_opt:.4f}")
    print()
    
# print correctly the optimal execution times range min and max

min_optimal_execution_time = 1000
max_optimal_execution_time = 0
for component in components:
    if component.optimal_execution_time < min_optimal_execution_time:
        min_optimal_execution_time = component.optimal_execution_time
    if component.optimal_execution_time > max_optimal_execution_time:
        max_optimal_execution_time = component.optimal_execution_time
print(f"Minimum optimal execution time: {min_optimal_execution_time:.2f}")
print(f"Maximum optimal execution time: {max_optimal_execution_time:.2f}")

example_group = Group(1)
example_group.add_component(components[4])
example_group.add_component(components[752])

# Find the optimal execution time for the group. Calculates the optimal execution time for the group based on the components in the group Dekker's paper
group_time = find_optimal_group_time(example_group)[0]
# As prof. Mourtos said the schedules that are updated are the ones of the other components outside of the group
# Additionally components that will be grouped together will be maintained together always there will be no reevaluation in the future (DISCUSS IT with Phuc)
update_component_schedule(example_group, group_time)

# Calculate profit
profit, details = compute_group_economic_profit(example_group, group_time, get_production_line_by_id) # Discuss what holds regarding total duration of group maintenance because in sequential maintenance there no downtime cost savings
# With sequential the downtime cost is increased

# Print each components in the group the optimal execution time and then the group's optimal execution time
print(f"\nGroup execution time: {group_time:.2f}")
for component in example_group.components:
    print(f"\nComponent {int(component.id)}:")
    print(f"  Optimal execution time: {component.optimal_execution_time:.2f}")
    print(f"  Execution schedule before: {component.execution_schedule}")
    print(f"  Execution schedule after: {component.execution_schedule_2}")
    interval = find_feasible_interval(component, get_production_line_by_id)
    if interval:
        print(f"  Feasible interval: ({interval[0]:.2f}, {interval[1]:.2f})")
    else:
        print(f"  No feasible grouping interval found for component {int(component.id)}.")
print(f"\nGroup economic profit: {profit:.2f}")

# Plot the group economic profit analysis
plot_group_economic_profit(example_group, get_production_line_by_id, find_optimal_group_time)
# Plot the feasible interval penalty function
plot_feasible_interval_penalty(components[5], get_production_line_by_id)




"""
# Now run the greedy constructive heuristic
print("\n" + "="*50)
print("Running Greedy Constructive Heuristic")
print("="*50)

# Import here to avoid circular import
from metaheuristics import constructive_heuristic

# Create a new solution object for the heuristic
greedy_solution = Solution()
greedy_solution = constructive_heuristic(greedy_solution, get_production_line_by_id)

# Calculate and print summary statistics
total_groups = len(greedy_solution.solution)
total_components = sum(len(group.components) for group in greedy_solution.solution)
singleton_groups = sum(1 for group in greedy_solution.solution if len(group.components) == 1)
grouped_components = total_components - singleton_groups

print(f"\nGreedy heuristic results:")
print(f"Total number of groups: {total_groups}")
print(f"Total components processed: {total_components}")
print(f"Number of singleton groups: {singleton_groups}")
print(f"Number of components in multi-component groups: {grouped_components}")
print(f"Percentage of components in groups: {(grouped_components/total_components)*100:.2f}%")

# Calculate total solution cost
cost_summary = greedy_solution.calculate_total_cost(get_production_line_by_id)

print(f"\nSolution cost summary:")
print(f"  Baseline cost (no grouping): {cost_summary['baseline_cost']:.2f}")
print(f"  Total economic profit from grouping: {cost_summary['total_profit']:.2f}")
print(f"  Total setup savings: {cost_summary['total_setup_savings']:.2f}")
print(f"  Total increased corrective maintenance cost: {cost_summary['total_increased_cost']:.2f}")
print(f"  Final solution cost: {cost_summary['total_cost']:.2f}")
print(f"  Cost reduction: {(1 - cost_summary['total_cost']/cost_summary['baseline_cost'])*100:.2f}%")

# Print details for the largest groups (e.g., all groups)
print("\nLargest groups:")
sorted_groups = sorted(greedy_solution.solution, key=lambda g: len(g.components), reverse=True)
for i, group in enumerate(sorted_groups):
    group_time = find_optimal_group_time(group)[0]
    update_component_schedule(group, group_time)
    update_non_group_component_schedules(group, components, get_production_line_by_id)
    profit, details = compute_group_economic_profit(group, group_time, get_production_line_by_id)
    print(f"\nGroup {group.id} - Components: {len(group.components)}, Profit: {profit:.2f}")
    print(f"  Setup savings: {details['setup_savings']:.2f}")
    print(f"  Increased CM cost: {details['increased_CM_cost']:.2f}")
    print(f"  Components: {[int(c.id) for c in group.components]}")
    #plot_group_economic_profit(group, get_production_line_by_id, find_optimal_group_time)
    print(f"  Group execution time: {group_time:.2f}")
        
#print the total cost of the grouping structure
cost = compute_grouping_structure_cost(greedy_solution.solution, get_production_line_by_id, 365)
print(f"\nTotal cost of the grouping structure: {cost:.2f}")
"""