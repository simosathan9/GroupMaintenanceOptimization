from scipy.optimize import minimize_scalar, root_scalar
from cost_functions import compute_phi_raw, penalty_function

def compute_group_economic_profit(group, group_time, get_production_line_by_id):
    setup_savings = 0
    downtime_savings = 0
    increase_in_cost = 0
    production_line_ids = set()

    # --- CM Cost Increase Calculation ---
    for component in group.components:
        production_line_ids.add(component.production_line_id)

        delta_t = abs(group_time - component.optimal_execution_time)
        cc = component.corrective_maintenance_cost
        mtbf = component.mean_time_between_failures
        lambd = component.lamda_efr
        x_star = component.optimal_execution_time

        phi_plus = compute_phi_raw(cc, mtbf, lambd, x_star + delta_t)
        phi_minus = compute_phi_raw(cc, mtbf, lambd, x_star - delta_t)
        phi_star = compute_phi_raw(cc, mtbf, lambd, x_star)

        increase_in_cost += (phi_plus + phi_minus - 2 * phi_star)

    # --- Setup Savings: 1 setup per line ---
    for line_id in production_line_ids:
        line = get_production_line_by_id(line_id)
        num_components = sum(1 for c in group.components if c.production_line_id == line_id)
        setup_savings += line.preventive_maintenance_set_up_cost * (num_components - 1)

    # --- Downtime Cost Savings (Equation 15) ---
    for line_id in production_line_ids:
        components_on_line = [c for c in group.components if c.production_line_id == line_id]
        line = get_production_line_by_id(line_id)

        total_individual_duration = sum(c.preventive_maintenance_duration for c in components_on_line)
        max_parallel_duration = max(c.preventive_maintenance_duration for c in components_on_line)

        line_downtime_savings = line.downtime_cost_rate * (total_individual_duration - max_parallel_duration)
        downtime_savings += line_downtime_savings

    # --- Final Economic Profit ---
    economic_profit = setup_savings + downtime_savings - increase_in_cost
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

def find_optimal_group_time(group, use_effective_time=False):
    """
    Find optimal execution time for a group.
    If use_effective_time is True and group has effective_execution_time set,
    use that instead of optimizing.
    """
    if use_effective_time and hasattr(group, 'effective_execution_time') and group.effective_execution_time > 0:
        return group.effective_execution_time, group_penalty_function(group.effective_execution_time, group)
    
    result = minimize_scalar(lambda t: group_penalty_function(t, group), bounds=(0, 365), method='bounded')
    
    # Store as planned execution time if not using effective time
    if not use_effective_time:
        group.planned_execution_time = result.x
    
    return result.x, result.fun

# This function finds for a given component the feasible interval within which the penalty for shifting away from the optimal execution time does not exceed the setup cost of the production line
def find_feasible_interval(component, get_production_line_by_id):
    production_line = get_production_line_by_id(component.production_line_id)
    S = production_line.preventive_maintenance_set_up_cost
    x_star = component.optimal_execution_time

    def root_eq(delta_t):
        return penalty_function(delta_t, component) - S

    # Search for Δt⁻ in the negative direction
    try:
        sol_neg = root_scalar(root_eq, bracket=[-x_star + 0.01, 0], method='brentq') # Root scalar is a root-finding algorithm based on Bolzano's condition
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
            interval_i = components[i].feasible_interval 
            interval_j = components[j].feasible_interval
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

def compute_grouping_structure_cost_with_cascading(groups, get_production_line_fn, d_PH):
    """
    Compute grouping structure cost considering cascading delays.
    This should be called AFTER the constructive heuristic completes.
    """
    # Step 1: Calculate the total individual cost
    total_individual_cost = 0
    all_components = []
    for group in groups:
        all_components.extend(group.components)
    
    total_individual_cost = d_PH * sum(comp.long_term_cost_rate for comp in all_components)

    # Step 2: Apply cascading delays
    from group import group_components_by_line, apply_cascading_delays
    groups_by_line = group_components_by_line(groups)
    apply_cascading_delays(groups_by_line, get_production_line_fn)

    # Step 3: Calculate total group economic profit using effective execution times
    total_economic_profit = 0
    for group in groups:
        group_time = group.effective_execution_time if hasattr(group, 'effective_execution_time') and group.effective_execution_time > 0 else find_optimal_group_time(group)[0]
        profit, components_dict = compute_group_economic_profit(group, group_time, get_production_line_fn)
        group.economic_profit = (profit, components_dict)
        total_economic_profit += profit

    # Step 4: Calculate grouped structure cost
    grouped_structure_cost = total_individual_cost - total_economic_profit

    return grouped_structure_cost