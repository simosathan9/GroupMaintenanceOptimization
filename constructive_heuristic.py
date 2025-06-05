from group import Group
from group_analysis import (
    find_feasible_interval,
    find_non_intersecting_pairs,
    find_optimal_group_time,
    compute_group_economic_profit,
    compute_grouping_structure_cost
)

def best_fit_bin_packing(components, get_production_line_by_id, planning_horizon=365):
    """
    Best-fit bin packing algorithm for grouping maintenance components.
    This is a greedy heuristic that places each component into the group that results in 
    the smallest increase in total grouping structure cost.
    
    Args:
        components: List of components to be grouped
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days (default 365)
        max_components_per_group: Maximum number of components allowed per group (optional)
        
    Returns:
        List of Group objects representing the grouping solution
    """
    # Calculate feasible intervals for all components
    component_intervals = {}
    for component in components:
        interval = find_feasible_interval(component, get_production_line_by_id)
        if interval:
            component_intervals[component] = interval
    
    # Identify non-intersecting component pairs (components that cannot be grouped together)
    non_intersecting_pairs = find_non_intersecting_pairs(components, find_feasible_interval, get_production_line_by_id)
    non_intersecting_set = set()
    for comp1, comp2 in non_intersecting_pairs:
        non_intersecting_set.add((comp1.id, comp2.id))
        non_intersecting_set.add((comp2.id, comp1.id))
    
    # Filter components to those with feasible intervals
    valid_components = [comp for comp in components if comp in component_intervals]
    
    # Sort components by decreasing maintenance cost to prioritize more expensive components
    sorted_components = sorted(valid_components, key=lambda x: x.long_term_cost_rate, reverse=True)
    
    groups = []
    group_id = 1
    
    # Process each component
    for component in sorted_components:
        # Calculate the cost of adding this component to each existing group
        best_group = None
        current_cost_increase = float('inf')  # Initialize with infinity
        
        # Calculate baseline cost - if the component were in its own group
        baseline_group = Group(-1)  # Temporary group just for calculation
        baseline_group.add_component(component)
        baseline_cost = compute_grouping_structure_cost([baseline_group], get_production_line_by_id, planning_horizon)
        
        # Try each existing group
        for group in groups:    
            # Check if component can be added (no non-intersecting intervals)
            can_be_added = True
            for existing_comp in group.components:
                if (component.id, existing_comp.id) in non_intersecting_set:
                    can_be_added = False
                    break
                    
            if not can_be_added:
                continue
                
            # Make a temporary copy of the group with the new component
            temp_group = Group(group.id)
            for c in group.components:
                temp_group.add_component(c)
            temp_group.add_component(component)
            
            # Calculate optimal time for the group with the added component
            group_time, _ = find_optimal_group_time(temp_group)
            
            # Calculate new cost of this group with the component added
            new_group_cost = compute_grouping_structure_cost([temp_group], get_production_line_by_id, planning_horizon)
            
            # Calculate cost increase (new_group_cost - old_group_cost)
            old_group_cost = compute_grouping_structure_cost([group], get_production_line_by_id, planning_horizon)
            cost_increase = new_group_cost - old_group_cost
            
            # If this is better than our current best option, update it
            if cost_increase < current_cost_increase:
                current_cost_increase = cost_increase
                best_group = group
        
        # Check if creating a new group is better than adding to an existing group
        new_group_cost_increase = baseline_cost
        
        if best_group is None or new_group_cost_increase <= current_cost_increase:
            # Create a new group for this component
            new_group = Group(group_id)
            new_group.add_component(component)
            group_time = component.optimal_execution_time
            groups.append(new_group)
            group_id += 1
        else:
            # Add to the best existing group
            best_group.add_component(component)
            group_time, _ = find_optimal_group_time(best_group)
    
    # Final update of all groups' properties
    for group in groups:
        group_time, _ = find_optimal_group_time(group)
        profit, _ = compute_group_economic_profit(group, group_time, get_production_line_by_id)
        group.economic_profit = profit
    
    return groups