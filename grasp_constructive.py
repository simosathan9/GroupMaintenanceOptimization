from group import Group
from group_analysis import (
    find_feasible_interval,
    find_non_intersecting_pairs,
    find_optimal_group_time,
    compute_group_economic_profit,
    compute_grouping_structure_cost
)
import random

def grasp_constructive_heuristic(components, get_production_line_by_id, planning_horizon=365):
    """
    GRASP constructive heuristic that ensures groups contain only components 
    from the same production line and always selects from exactly the top 3 best options.
    
    Args:
        components: List of components to be grouped
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days (default 365)
        
    Returns:
        List of Group objects representing the grouping solution
    """
    # Calculate feasible intervals for all components
    component_intervals = {}
    for component in components:
        component_intervals[component] = component.feasible_interval
    
    # Identify non-intersecting component pairs (components that cannot be grouped together)
    non_intersecting_pairs = find_non_intersecting_pairs(components, find_feasible_interval, get_production_line_by_id)
    non_intersecting_set = set()
    for comp1, comp2 in non_intersecting_pairs:
        non_intersecting_set.add((comp1.id, comp2.id))
        non_intersecting_set.add((comp2.id, comp1.id))
    
    # Filter components to those with feasible intervals
    valid_components = [comp for comp in components if comp in component_intervals]
    
    # Sort components by decreasing maintenance cost to prioritize more expensive components
    sorted_components = sorted(valid_components, key=lambda x: x.optimal_execution_time, reverse=True)
    
    groups = []
    group_id = 1
    
    # Process each component
    for component in sorted_components:
        # Store all valid placement options with their costs
        placement_options = []
        
        # Calculate baseline cost - if the component were in its own group
        baseline_group = Group(-1)  # Temporary group just for calculation
        baseline_group.add_component(component)
        baseline_cost = compute_grouping_structure_cost([baseline_group], get_production_line_by_id, planning_horizon)
        
        # Option 1: Create a new group
        placement_options.append({
            'type': 'new_group',
            'group': None,
            'cost_increase': baseline_cost
        })
        
        # Try each existing group
        for group in groups:    
            # Check if component can be added to this group (same production line)
            if not group.can_add_component(component):
                continue
                
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
            temp_group.production_line_id = group.production_line_id
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
            
            # Add this option to our list
            placement_options.append({
                'type': 'existing_group',
                'group': group,
                'cost_increase': cost_increase
            })
        
        # Sort placement options by cost increase (best to worst)
        placement_options.sort(key=lambda x: x['cost_increase'])
        
        # Select top 3 options (or all if fewer than 3 available)
        top_options = placement_options[:min(3, len(placement_options))]
        
        # Randomly select one option from the top 3
        selected_option = random.choice(top_options)
        
        # Execute the selected option
        if selected_option['type'] == 'new_group':
            # Create a new group for this component
            new_group = Group(group_id)
            new_group.add_component(component)
            groups.append(new_group)
            group_id += 1
        else:
            # Add to the selected existing group
            selected_option['group'].add_component(component)
    
    # Final update of all groups' properties
    for group in groups:
        group_time, _ = find_optimal_group_time(group)
        profit, _ = compute_group_economic_profit(group, group_time, get_production_line_by_id)
        group.economic_profit = profit
    
    return groups