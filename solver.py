# Start by reading the data
from instance_reader import InstanceReader
from component import Component
from production_line import ProductionLine
from solution import Solution
from group import Group
import numpy as np
from cost_functions import compute_optimal_x
from visualizations import plot_group_economic_profit, plot_feasible_interval_penalty, plot_component_planning_horizon, plot_cascading_effects_comparison
from group_analysis import (
    compute_group_economic_profit, 
    find_optimal_group_time,
    find_feasible_interval,
    compute_grouping_structure_cost,
)
from group import group_components_by_line
from constructive_heuristic import best_fit_bin_packing
from grasp_constructive import grasp_constructive_heuristic
# Import metaheuristic approaches
from local_search import local_search_scheme
from alns import alns_scheme

reader = InstanceReader("datasets/testing_dataset.csv")
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
  
#plot_component_planning_horizon(components, get_production_line_by_id)
global_best_solution = None
global_best_cost = float('inf')

for i in range(1):
    print("\n=== Best-Fit Bin Packing Solution (Minimizing Grouping Structure Cost) ===")

    # Define planning horizon (1 year)
    planning_horizon = 365

    # Construct initial solution using GRASP
    grouping_structure = grasp_constructive_heuristic(components, get_production_line_by_id, planning_horizon)

    # Evaluate initial cost
    grouping_structure_cost = compute_grouping_structure_cost(grouping_structure, get_production_line_by_id, planning_horizon)
    print(f"\nInitial grouping structure cost: {grouping_structure_cost:.2f}")

    metaheuristic_approach = "alns"  # Options: "local_search", "alns", "both"

    # Initialize current best for this iteration
    best_solution = grouping_structure
    best_cost = grouping_structure_cost

    # Run Local Search
    if metaheuristic_approach in {"local_search", "both"}:
        print("\n=== Running Enhanced Local Search ===")
        local_search_solution = local_search_scheme(
            grouping_structure,
            get_production_line_by_id,
            planning_horizon,
            max_iterations=20
        )
        local_search_cost = compute_grouping_structure_cost(local_search_solution, get_production_line_by_id, planning_horizon)
        print(f"\nFinal solution cost after local search: {local_search_cost:.2f}")
        print(f"Improvement over heuristic: {grouping_structure_cost - local_search_cost:.2f} "
              f"({((grouping_structure_cost - local_search_cost) / grouping_structure_cost * 100):.2f}%)")

        if local_search_cost < best_cost:
            best_cost = local_search_cost
            best_solution = local_search_solution

    # Run ALNS
    if metaheuristic_approach in {"alns", "both"}:
        print("\n=== Running Adaptive Large Neighborhood Search ===")
        alns_solution = alns_scheme(
            grouping_structure,
            get_production_line_by_id,
            planning_horizon,
            max_iterations=500,
            non_improving_iterations=100,
            initial_temperature=100,
            cooling_rate=0.999999999
        )
        alns_cost = compute_grouping_structure_cost(alns_solution, get_production_line_by_id, planning_horizon)
        print(f"\nFinal solution cost after ALNS: {alns_cost:.2f}")
        print(f"Improvement over heuristic: {grouping_structure_cost - alns_cost:.2f} "
              f"({((grouping_structure_cost - alns_cost) / grouping_structure_cost * 100):.2f}%)")

        if alns_cost < best_cost:
            best_cost = alns_cost
            best_solution = alns_solution

    # Log which metaheuristic was better if both were run
    if metaheuristic_approach == "both":
        if best_solution == alns_solution:
            print(f"\nALNS outperformed Local Search by {local_search_cost - alns_cost:.2f} "
                  f"({((local_search_cost - alns_cost) / local_search_cost * 100):.2f}%)")
        else:
            print(f"\nLocal Search outperformed ALNS by {alns_cost - local_search_cost:.2f} "
                  f"({((alns_cost - local_search_cost) / alns_cost * 100):.2f}%)")

    # Update global best
    if best_cost < global_best_cost:
        global_best_cost = best_cost
        global_best_solution = best_solution

# Apply cascading delays manually to show the process
groups_by_line = group_components_by_line(global_best_solution)
print(f"\n=== Applying Cascading Delays by Production Line (for scheduling only) ===")

for line_id, line_groups in groups_by_line.items():
    print(f"\nProduction Line {int(line_id)}:")
    # Sort groups by planned execution time
    sorted_groups = sorted(line_groups, key=lambda g: g.planned_execution_time)
    
    cumulative_delay = 0
    for i, group in enumerate(sorted_groups):
        if len(group.components) > 1:  # Only show multi-component groups
            old_time = group.planned_execution_time
            group.effective_execution_time = group.planned_execution_time + cumulative_delay
            downtime = group.get_group_downtime()
            
            print(f"  Group {group.id}: {old_time:.2f} → {group.effective_execution_time:.2f} (delay: +{cumulative_delay:.2f})")
            print(f"    Downtime added: {downtime:.2f}")
            
            # Add this group's downtime to cumulative delay for subsequent groups
            cumulative_delay += downtime

# Visualize the cascading effects comparison
plot_cascading_effects_comparison(groups_by_line)
            
print(f"\n=== Detailed Component Analysis After Cascading Effects ===")
for line_id, line_groups in groups_by_line.items():
    for group in line_groups:
            if len(group.components) > 1:  # Only show multi-component groups
                effective_time = group.effective_execution_time if hasattr(group, 'effective_execution_time') else group.planned_execution_time
                optimal_time = group.planned_execution_time
                
                print(f"\nGroup {group.id}:")
                print(f"  Components: {[int(c.id) for c in group.components]}")
                print(f"  Component normal times: {[f'{c.optimal_execution_time:.2f}' for c in group.components]}")
                print(f"  Optimal group time: {optimal_time:.2f}")
                print(f"  Final execution time (after cascading): {effective_time:.2f}")
                
                # Show individual component deviations
                for component in group.components:
                    normal_time = component.optimal_execution_time
                    deviation_from_normal = effective_time - normal_time
                    interval = component.feasible_interval
                    print(f"    Component {int(component.id)}: {normal_time:.2f} → {effective_time:.2f} (deviation: {deviation_from_normal:+.2f}), Feasible interval: ({interval[0]:.2f}, {interval[1]:.2f})")
                
                downtime = group.get_group_downtime()
                print(f"  Group downtime: {downtime:.2f}")
                
                # Calculate economic profit using the OPTIMAL time (not effective time)
                # because downtime doesn't change the economic calculations
                _, profit_details = compute_group_economic_profit(group, optimal_time, get_production_line_by_id)
                print(f"  Components of economic profit: {profit_details.get('setup_savings', 0):.2f} (setup savings), {profit_details.get('downtime_savings', 0):.2f} (downtime savings), {profit_details.get('increased_CM_cost', 0):.2f} (increased CM cost)")
                print(f"  Group economic profit: {_:.2f}")

# Final output of the best solution found
print("\n=== Best Solution Found ===")
print(f"Total cost: {global_best_cost:.2f}")
print(f"Total cost reduction from initial bin packing: {grouping_structure_cost - global_best_cost:.2f} ({((grouping_structure_cost - global_best_cost) / grouping_structure_cost * 100):.2f}%)")
print(f"Number of groups: {len(global_best_solution)}")

print(f"\n=== Final Schedule with Cascading Effects (for implementation) ===")
for group in global_best_solution:
    if len(group.components) > 1:  # Only show multi-component groups
        group_time = find_optimal_group_time(group)[0]
        effective_time = getattr(group, 'effective_execution_time', group_time)
        print(f"Group {group.id}:")
        print(f"  Optimal execution time: {group_time:.2f}")
        print(f"  Scheduled execution time: {effective_time:.2f}")
        print(f"  Components: {[int(c.id) for c in group.components]}")
        print(f"  Production lines: {[int(c.production_line_id) for c in group.components]}")
        print(f"  Downtime duration: {group.get_group_downtime():.2f}")