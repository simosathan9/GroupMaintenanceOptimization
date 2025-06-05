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
    find_feasible_interval,
    compute_grouping_structure_cost,
)
# Import metaheuristic algorithms
from constructive_heuristic import best_fit_bin_packing
# Import moved to avoid circular import
reader = InstanceReader("datasets/testing_dataset.csv")
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
    'PM_duration': 'Duration'
})
production_lines = []
production_line_map = {}

for index, row in data.iterrows():
    line_id = row['Production Line']
    if line_id not in production_line_map:
        production_line = ProductionLine(line_id, 5, 3, 5)
        production_line_map[line_id] = production_line
        production_lines.append(production_line)

def get_production_line_by_id(id):
    for production_line in production_lines:
        if production_line.id == id:
            return production_line
    return None

# In the same way we will calculate the downtime cost reduction as each production line is accompanied with its downtime cost rate
maintenance_durations = data['Duration'].tolist()
for index, row in data.iterrows():
    component = Component(row['ID'], row['Duration'], row['Corrective_Specific_Cost'], row['Preventive_Specific_Cost'], get_production_line_by_id(row['Production Line']), row['Weibull_Parameter'], row['MTBF'])
    components.append(component)

for component in components:
    cc = component.corrective_maintenance_cost # includes production line setup cost
    cp = component.preventive_maintenance_cost # includes production line setup cost and downtime cost
    mtbf = component.mean_time_between_failures
    lambd = component.lamda_efr
    d = component.preventive_maintenance_duration  # duration of PM

    x_opt, cr_opt = compute_optimal_x(cp, cc, mtbf, lambd, d)
    component.optimal_execution_time = x_opt
    component.long_term_cost_rate = cr_opt
    component.feasible_interval = find_feasible_interval(component, get_production_line_by_id)

    print(f"Component {component.id}:")
    print(f"  Optimal x*: {x_opt:.2f}")
    print(f"  Feasible interval: {component.feasible_interval[0]:.2f} - {component.feasible_interval[1]:.2f}")
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

#--------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------
# Now let's use the best-fit bin packing algorithm to create groups
print("\n=== Best-Fit Bin Packing Solution (Minimizing Grouping Structure Cost) ===")

# Define planning horizon (1 year)
planning_horizon = 365

# Get the individual component costs for comparison
individual_components_groups = []
for i, component in enumerate(components):
    group = Group(i+1)
    group.add_component(component)
    individual_components_groups.append(group)

individual_cost = compute_grouping_structure_cost(individual_components_groups, get_production_line_by_id, planning_horizon)
print(f"Initial cost with no grouping: {individual_cost:.2f}")

# Run the bin packing algorithm
bin_packing_groups = best_fit_bin_packing(components, get_production_line_by_id, planning_horizon)

# Calculate the final grouped structure cost
final_cost = compute_grouping_structure_cost(bin_packing_groups, get_production_line_by_id, planning_horizon)
print(f"Final cost after grouping: {final_cost:.2f}")
print(f"Cost reduction: {individual_cost - final_cost:.2f} ({((individual_cost - final_cost) / individual_cost * 100):.2f}%)")
"""
# Print the bin packing solution statistics
print(f"\nTotal number of groups created: {len(bin_packing_groups)}")
multi_component_groups = [g for g in bin_packing_groups if len(g.components) > 1]
print(f"Number of multi-component groups: {len(multi_component_groups)}")

# Calculate the total economic profit
total_economic_profit = 0
for group in bin_packing_groups:
    if len(group.components) > 1:
        group_time = find_optimal_group_time(group)[0]
        profit, _ = compute_group_economic_profit(group, group_time, get_production_line_by_id)
        total_economic_profit += profit

print(f"Total economic profit from grouping: {total_economic_profit:.2f}")

# Show details of multi-component groups
print("\nMulti-component groups details:")
for group in sorted(multi_component_groups, key=lambda g: len(g.components), reverse=True):
    group_time = find_optimal_group_time(group)[0]
    profit, details = compute_group_economic_profit(group, group_time, get_production_line_by_id)
    
    print(f"\nGroup {group.id} - Components: {len(group.components)}, Execution time: {group_time:.2f}, Profit: {profit:.2f}")
    print(f"  Setup savings: {details['setup_savings']:.2f}")
    print(f"  Downtime savings: {details['downtime_savings']:.2f}")
    print(f"  Increased CM cost: {details['increased_CM_cost']:.2f}")
    print(f"  Components: {[int(c.id) for c in group.components]}")
    #print(f"  Production lines: {sorted(set(c.production_line_id for c in group.components))}") production line id in numpy format
    # print production line ids as int and not numpy format
    print(f"  Production lines: {[int(c.production_line_id) for c in group.components]}")
    
    # Show feasible interval verification for the first few components (limited to avoid excessive output)
    if len(group.components) <= 5:  # Only show details for small groups
        print("  Feasible intervals:")
        for component in group.components:
            interval = find_feasible_interval(component, get_production_line_by_id)
            if interval:
                print(f"    Component {int(component.id)}: ({interval[0]:.2f}, {interval[1]:.2f}), Optimal: {component.optimal_execution_time:.2f}")
            else:
                print(f"    Component {int(component.id)}: No feasible interval found.")
            # Plot the group economic profit analysis
        #plot_group_economic_profit(group, get_production_line_by_id, find_optimal_group_time)

# Plot the feasible interval penalty function
#plot_feasible_interval_penalty(components[5], get_production_line_by_id)
#
from local_search import local_search_scheme

# Calculate and print the cost of the initial solution from bin packing
initial_bin_packing_cost = compute_grouping_structure_cost(bin_packing_groups, get_production_line_by_id, planning_horizon)
print(f"\nInitial bin packing solution cost: {initial_bin_packing_cost:.2f}")

# Import metaheuristic approaches
from local_search import local_search_scheme
from alns import alns_scheme

# Choose which metaheuristic to run
metaheuristic_approach = "alns"  # Options: "local_search", "alns", "both"

if metaheuristic_approach == "local_search" or metaheuristic_approach == "both":
    # Run the enhanced local search
    print("\n=== Running Enhanced Local Search ===")
    local_search_solution = local_search_scheme(
        bin_packing_groups, 
        get_production_line_by_id, 
        planning_horizon,
        max_iterations=20
    )
    
    # Calculate and print the cost of the local search solution
    local_search_cost = compute_grouping_structure_cost(local_search_solution, get_production_line_by_id, planning_horizon)
    print(f"\nFinal solution cost after local search: {local_search_cost:.2f}")
    print(f"Improvement over bin packing: {initial_bin_packing_cost - local_search_cost:.2f} ({((initial_bin_packing_cost - local_search_cost) / initial_bin_packing_cost * 100):.2f}%)")
    print(f"Total improvement over individual components: {individual_cost - local_search_cost:.2f} ({((individual_cost - local_search_cost) / individual_cost * 100):.2f}%)")
    
    # Set the final solution to be the local search solution
    if metaheuristic_approach == "local_search":
        solution = local_search_solution
        final_cost = local_search_cost

if metaheuristic_approach == "alns" or metaheuristic_approach == "both":
    # Run the Adaptive Large Neighborhood Search
    print("\n=== Running Adaptive Large Neighborhood Search ===")
    alns_solution = alns_scheme(
        bin_packing_groups,
        get_production_line_by_id,
        planning_horizon,
        max_iterations=100,
        non_improving_iterations=20,
        initial_temperature=100,
        cooling_rate=0.95
    )
    
    # Calculate and print the cost of the ALNS solution
    alns_cost = compute_grouping_structure_cost(alns_solution, get_production_line_by_id, planning_horizon)
    print(f"\nFinal solution cost after ALNS: {alns_cost:.2f}")
    print(f"Improvement over bin packing: {initial_bin_packing_cost - alns_cost:.2f} ({((initial_bin_packing_cost - alns_cost) / initial_bin_packing_cost * 100):.2f}%)")
    print(f"Total improvement over individual components: {individual_cost - alns_cost:.2f} ({((individual_cost - alns_cost) / individual_cost * 100):.2f}%)")
    
    # Set the final solution to be the ALNS solution
    if metaheuristic_approach == "alns":
        solution = alns_solution
        final_cost = alns_cost

if metaheuristic_approach == "both":
    # Compare the two approaches and choose the best
    if alns_cost < local_search_cost:
        solution = alns_solution
        final_cost = alns_cost
        print(f"\nALNS outperformed Local Search by {local_search_cost - alns_cost:.2f} ({((local_search_cost - alns_cost) / local_search_cost * 100):.2f}%)")
    else:
        solution = local_search_solution
        final_cost = local_search_cost
        print(f"\nLocal Search outperformed ALNS by {alns_cost - local_search_cost:.2f} ({((alns_cost - local_search_cost) / alns_cost * 100):.2f}%)")

# Print the final solution
print("\n=== Final Solution After Metaheuristic ===")
for group in solution:
    group_time = find_optimal_group_time(group)[0]
    profit, details = compute_group_economic_profit(group, group_time, get_production_line_by_id)
    
    print(f"\nGroup {group.id} - Components: {len(group.components)}, Execution time: {group_time:.2f}, Profit: {profit:.2f}")
    print(f"  Setup savings: {details['setup_savings']:.2f}")
    print(f"  Downtime savings: {details['downtime_savings']:.2f}")
    print(f"  Increased CM cost: {details['increased_CM_cost']:.2f}")
    print(f"  Components: {[int(c.id) for c in group.components]}")
    #print(f"  Production lines: {sorted(set(c.production_line_id for c in group.components))}") production line id in numpy format
    # print production line ids as int and not numpy format
    print(f"  Production lines: {[int(c.production_line_id) for c in group.components]}")
    
    # Show feasible interval verification for the first few components (limited to avoid excessive output)
    if len(group.components) <= 5:  # Only show details for small groups
        print("  Feasible intervals:")
        for component in group.components:
            interval = find_feasible_interval(component, get_production_line_by_id)
            if interval:
                print(f"    Component {int(component.id)}: ({interval[0]:.2f}, {interval[1]:.2f}), Optimal: {component.optimal_execution_time:.2f}")
            else:
                print(f"    Component {int(component.id)}: No feasible interval found.")
"""