# Start by reading the data
from instance_reader import InstanceReader
from component import Component
from production_line import ProductionLine
from solution import Solution
from group import Group
import scipy.special as sp  # for the Gamma function
from scipy.optimize import minimize_scalar
from scipy.optimize import root_scalar
import numpy as np

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

# https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.gamma.html to verify that sp.gamma matches the integral described in the paper
def compute_phi_raw(cc, mtbf, lambd, x):
    gamma_val = sp.gamma(1 + 1 / lambd)
    x_safe = max(0, x) # Despite the bounds minimize_scalar() can evaluate points slightly outside the bounds due to numerical precision
    base = (gamma_val / mtbf) ** lambd
    #print(f"Gamma value: {gamma_val}, Base: {base}, x_safe: {x_safe}")
    return cc * base * (1 / lambd) * x_safe ** lambd # Described in the equation 10 of the paper

def cost_rate(x, cp, cc, mtbf, lambd, d):
    phi = compute_phi_raw(cc, mtbf, lambd, x)
    return (cp + phi) / (x + d)

def compute_optimal_x(cp, cc, mtbf, lambd, d):
    result = minimize_scalar(
        lambda x: cost_rate(x, cp, cc, mtbf, lambd, d),
        bounds=(0, 365),  # ENSURE THAT x* IS BETWEEN 0 AND 365
        method='bounded'
    )
    return result.x, result.fun  # x* and CR(x*)

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
    print(f"  Synthetic x*: {component.optimal_execution_time:.2f}")
    print(f"  Synthetic CR: {component.long_term_cost_rate_synthetic:.4f}")
    # print the execution schedule
    print(f"  Execution schedule for planning horizon: {component.execution_schedule}")
    print("  Δ x*: {:.2f}, Δ CR: {:.4f}".format(x_opt - component.optimal_execution_time_synthetic, cr_opt - component.long_term_cost_rate_synthetic))
    print()


# Calculates the equation 18 described in the paper. Requires that group's optimal execution time is already calculated. The calculation is done based on Dekker's paper, maximizing the economic profit
def compute_group_economic_profit(group, group_time):
    setup_savings = 0
    downtime_savings = 0
    increase_in_cost = 0
    production_line_ids = set()

    # Determine group-wide duration (max component PM duration)
    #max_duration = max(comp.preventive_maintenance_duration for comp in group.components) # We make the assumption that all repairmen work concurrently on all components of the group (DISCUSS IT)
    # calculate max duration as the sum of the individual durations
    max_duration = sum(comp.preventive_maintenance_duration for comp in group.components) # We make the assumption that all repairmen work concurrently on all components of the group (DISCUSS IT)

    for component in group.components:
        line = component.production_line_id
        production_line_ids.add(line)

        # Δt: how far from x* is the new execution time
        delta_t = abs(group_time - component.optimal_execution_time) # Group time is the execution time that maximizes the economic profit. The way it is derived is described in Wildeman, Dekker and Smit 1997 paper)
        delta_d = abs(max_duration - component.preventive_maintenance_duration) # The additional downtime due to the group time being larger than the component's PM duration

        cc = component.corrective_maintenance_cost
        mtbf = component.mean_time_between_failures
        lambd = component.lamda_efr
        x_star = component.optimal_execution_time

        # R_G part: Increase in expected CM cost due to shift
        phi_plus = compute_phi_raw(cc, mtbf, lambd, x_star + delta_t)
        phi_minus = compute_phi_raw(cc, mtbf, lambd, x_star - delta_t - delta_d)
        phi_star = compute_phi_raw(cc, mtbf, lambd, x_star)

        increase_in_cost += phi_plus + phi_minus - 2 * phi_star

    # Setup savings: only one setup per line
    for line_id in production_line_ids:
        line = get_production_line_by_id(line_id)
        setup_savings += line.preventive_maintenance_set_up_cost * (sum(1 for c in group.components if c.production_line_id == line_id) - 1)

    # Downtime savings
    for line_id in production_line_ids:
        line = get_production_line_by_id(line_id)
        components_on_line = [c for c in group.components if c.production_line_id == line_id]
        
        #total_individual_duration = sum(c.preventive_maintenance_duration for c in components_on_line) # Total individual maintenance duration for the line
        #downtime_savings += line.downtime_cost_rate * (total_individual_duration - max_duration)
        # By assuming sequential execution of maintenance tasks, there are no downtime cost savings rather cost increases (SOS DISCUSS IT)
        
    #economic_profit = abs(downtime_savings) + setup_savings - increase_in_cost
    economic_profit = setup_savings - increase_in_cost
    return economic_profit, {
        "downtime_savings": downtime_savings,
        "setup_savings": setup_savings,
        "increased_CM_cost": increase_in_cost
    }

example_group = Group(1)
#example_group.add_component(components[890])
example_group.add_component(components[37])
example_group.add_component(components[1007])
example_group.add_component(components[97])


# This function calculates the penalty function for a group of components assuming LTS (Long-Term Shift)
def group_penalty_function(t, group):
    penalty = 0
    for comp in group.components:
        delta_t = t - comp.optimal_execution_time # Δt: how far from x* is the new execution time (DISCUSS IT)
        phi_shifted = compute_phi_raw(comp.corrective_maintenance_cost, comp.mean_time_between_failures, comp.lamda_efr, comp.optimal_execution_time + delta_t)
        phi_star = compute_phi_raw(comp.corrective_maintenance_cost, comp.mean_time_between_failures, comp.lamda_efr, comp.optimal_execution_time)
        penalty += (phi_shifted - phi_star - delta_t * comp.long_term_cost_rate) # Add abs since we are interested in the distance from the optimal execution time
    return penalty

def find_optimal_group_time(group):
    result = minimize_scalar(lambda t: group_penalty_function(t, group), bounds=(0, 365), method='bounded')
    return result.x, result.fun

def update_component_schedule(group, group_time):
    for component in group.components:
        delta_t = group_time - component.optimal_execution_time

        # Shift all times by delta_t and round to 2 decimals
        new_schedule = [round(float(t + delta_t), 2) for t in component.execution_schedule]
        new_schedule = [t for t in new_schedule if t > 0]

        component.execution_schedule_2 = new_schedule

# Find the optimal execution time for the group. Calculates the optimal execution time for the group based on the components in the group Dekker's paper
group_time = find_optimal_group_time(example_group)[0]
# As prof. Mourtos said the schedules that are updated are the ones of the other components outside of the group
# Additionally components that will be grouped together will be maintained together always there will be no reevaluation in the future (DISCUSS IT with Phuc)
update_component_schedule(example_group, group_time)

# Calculate profit
profit, details = compute_group_economic_profit(example_group, group_time) # Discuss what holds regarding total duration of group maintenance because in sequential maintenance there no downtime cost savings
# With sequential the downtime cost is increased

def penalty_function(delta_t, component):
    x_star = component.optimal_execution_time
    cc = component.corrective_maintenance_cost
    mtbf = component.mean_time_between_failures
    lambd = component.lamda_efr
    phi_plus = compute_phi_raw(cc, mtbf, lambd, x_star + delta_t)
    phi_star = compute_phi_raw(cc, mtbf, lambd, x_star)
    return phi_plus - phi_star - delta_t * component.long_term_cost_rate

def find_feasible_interval(component):
    production_line = get_production_line_by_id(component.production_line_id)
    S = production_line.preventive_maintenance_set_up_cost
    x_star = component.optimal_execution_time

    def root_eq(delta_t):
        return penalty_function(delta_t, component) - S

    # Search for Δt⁻ in the negative direction
    try:
        sol_neg = root_scalar(root_eq, bracket=[-x_star + 0.01, 0], method='brentq')
        delta_t_minus = sol_neg.root if sol_neg.converged else None
    except:
        delta_t_minus = None

    # Search for Δt⁺ in the positive direction
    try:
        sol_pos = root_scalar(root_eq, bracket=[0, 365 - x_star], method='brentq')
        delta_t_plus = sol_pos.root if sol_pos.converged else None
    except:
        delta_t_plus = None

    if delta_t_minus is not None and delta_t_plus is not None:
        return (x_star + delta_t_minus, x_star + delta_t_plus)
    else:
        return None  # No feasible interval

# Print each components in the group the optimal execution time and then the group's optimal execution time
print(f"\nGroup execution time: {group_time:.2f}")
for component in example_group.components:
    print(f"\nComponent {int(component.id)}:")
    print(f"  Optimal execution time: {component.optimal_execution_time:.2f}")
    print(f"  Execution schedule before: {component.execution_schedule}")
    print(f"  Execution schedule after: {component.execution_schedule_2}")
    # find its feasible interval
    interval = find_feasible_interval(component)
    if interval:
        print(f"  Feasible interval: ({interval[0]:.2f}, {interval[1]:.2f})")
    else:
        print(f"  No feasible grouping interval found for component {int(component.id)}.")
print(f"\nGroup economic profit: {profit:.2f}")








# ------------------------------------------------------------------------------
"""
# Identify pairs that have not intersecting intervals and not lead to economic profit
def find_non_intersecting_pairs(components):
    non_intersecting_pairs = []
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            interval_i = find_feasible_interval(components[i])
            interval_j = find_feasible_interval(components[j])
            if interval_i and interval_j:
                # Check if intervals do not intersect
                if interval_i[1] < interval_j[0] or interval_j[1] < interval_i[0]:
                    non_intersecting_pairs.append((components[i], components[j]))
    return non_intersecting_pairs
non_intersecting_pairs = find_non_intersecting_pairs(components)
# check if the pairs lead to economic profit
def check_economic_profit(pair):
    component_a, component_b = pair
    group = Group(1)
    group.add_component(component_a)
    group.add_component(component_b)
    group_time = find_optimal_group_time(group)[0]
    profit, details = compute_group_economic_profit(group, group_time)
    production_line_a = get_production_line_by_id(component_a.production_line_id)
    production_line_b = get_production_line_by_id(component_b.production_line_id)
    if production_line_a.id == production_line_b.id:
        if profit > 0:
            print(f"Pair ({component_a.id}, {component_b.id}) leads to economic profit.")
            print(f"  Economic profit: {profit:.2f}")
            # print the intervals also
            interval_a = find_feasible_interval(component_a)
            interval_b = find_feasible_interval(component_b)
            print(f"  Interval A: ({interval_a[0]:.2f}, {interval_a[1]:.2f})")
            print(f"  Interval B: ({interval_b[0]:.2f}, {interval_b[1]:.2f})")
            print(f"  Hello World")

for pair in non_intersecting_pairs:
    check_economic_profit(pair)
"""