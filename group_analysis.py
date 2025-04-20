from scipy.optimize import minimize_scalar, root_scalar
from cost_functions import compute_phi_raw, penalty_function

def compute_group_economic_profit(group, group_time, get_production_line_by_id):
    setup_savings = 0
    downtime_savings = 0
    increase_in_cost = 0
    production_line_ids = set()

    # Determine group-wide duration (max component PM duration)
    max_duration = sum(comp.preventive_maintenance_duration for comp in group.components)

    for component in group.components:
        line = component.production_line_id
        production_line_ids.add(line)

        # Δt: how far from x* is the new execution time
        delta_t = abs(group_time - component.optimal_execution_time)
        delta_d = abs(max_duration - component.preventive_maintenance_duration)

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

    # Calculate economic profit
    economic_profit = setup_savings - increase_in_cost # Downtime cost savings are not included in the economic profit calculation
    return economic_profit, {
        "downtime_savings": downtime_savings,
        "setup_savings": setup_savings,
        "increased_CM_cost": increase_in_cost
    }

# This function is used to calculate the penalty for a group of components. The penalty minimization helps find the group's optimal execution time
def group_penalty_function(t, group):
    penalty = 0
    for comp in group.components:
        delta_t = t - comp.optimal_execution_time
        phi_shifted = compute_phi_raw(comp.corrective_maintenance_cost, comp.mean_time_between_failures, comp.lamda_efr, comp.optimal_execution_time + delta_t)
        phi_star = compute_phi_raw(comp.corrective_maintenance_cost, comp.mean_time_between_failures, comp.lamda_efr, comp.optimal_execution_time)
        penalty += (phi_shifted - phi_star - delta_t * comp.long_term_cost_rate)
    return penalty

def find_optimal_group_time(group):
    result = minimize_scalar(lambda t: group_penalty_function(t, group), bounds=(0, 365), method='bounded')
    return result.x, result.fun

# DISCUSS how the update of the optimal execution times will be done after the grouping
def update_component_schedule(group, group_time):
    for component in group.components:
        delta_t = group_time - component.optimal_execution_time

        # Shift all times by delta_t and round to 2 decimals
        new_schedule = [round(float(t + delta_t), 2) for t in component.execution_schedule]
        new_schedule = [t for t in new_schedule if t > 0]

        component.execution_schedule_2 = new_schedule

#def update_optimal_execution_times_outside_group(components, group): (MUST BE IMPLEMENTED DISCUSS HOW IT HAS TO BE DONE)

# This function finds for a given component the feasible interval within which the penalty for shifting away from the optimal execution time does not exceed the setup cost of the production line
def find_feasible_interval(component, get_production_line_by_id):
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

def find_non_intersecting_pairs(components, find_feasible_interval, get_production_line_by_id):
    non_intersecting_pairs = []
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            interval_i = find_feasible_interval(components[i], get_production_line_by_id)
            interval_j = find_feasible_interval(components[j], get_production_line_by_id)
            if interval_i and interval_j:
                # Check if intervals do not intersect
                if interval_i[1] < interval_j[0] or interval_j[1] < interval_i[0]:
                    non_intersecting_pairs.append((components[i], components[j]))
    return non_intersecting_pairs

def compute_grouping_structure_cost(groups, get_production_line_fn, d_PH):
    # Step 1: Calculate the total individual cost
    total_individual_cost = 0
    all_components = []
    for group in groups:
        all_components.extend(group.components)
    
    total_individual_cost = d_PH * sum(comp.long_term_cost_rate for comp in all_components)

    # Step 2: Calculate total group economic profit
    total_economic_profit = 0
    for group in groups:
        # Compute optimal time for this group
        group_time = find_optimal_group_time(group)[0]
        profit, _ = compute_group_economic_profit(group, group_time, get_production_line_fn)
        total_economic_profit += profit

    # Step 3: Calculate grouped structure cost
    grouped_structure_cost = total_individual_cost - total_economic_profit

    return grouped_structure_cost