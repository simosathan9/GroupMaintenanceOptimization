from group import Group
from group_analysis import (
    compute_group_economic_profit, 
    find_optimal_group_time, 
    update_component_schedule,
    find_feasible_interval
)

def constructive_heuristic(solution, get_production_line_by_id):
    """
    Constructive heuristic that adds components to groups based on the best economic profit if there is an intersection
    on their feasible intervals. The interval must intersect with all component's feasible intervals in the group.
    """
    # Import components here to avoid circular imports
    from solver import components
    
    # Create a copy of components to work with
    available_components = list(components)
    group_id = 1
    
    # Calculate feasible intervals for all components
    component_intervals = {}
    for component in available_components:
        interval = find_feasible_interval(component, get_production_line_by_id)
        if interval:
            component_intervals[component.id] = interval
    
    # Continue until no more components can be grouped
    while available_components:
        # Start a new group with the first available component
        current_group = Group(group_id)
        seed_component = available_components.pop(0)
        current_group.add_component(seed_component)
        
        # Current group feasible interval starts as the seed component's interval
        if seed_component.id not in component_intervals:
            # If the seed component has no feasible interval, add it as a singleton group
            solution.solution.append(current_group)
            group_id += 1
            continue
            
        current_interval = component_intervals[seed_component.id]
        
        # Continue adding components to the current group
        improvements = True
        while improvements and available_components:
            best_profit = 0
            best_component = None
            best_interval = None
            best_time = None
            
            # Evaluate each remaining component for potential addition to the group
            for i, candidate in enumerate(available_components):
                # Skip if candidate has no feasible interval
                if candidate.id not in component_intervals:
                    continue
                    
                candidate_interval = component_intervals[candidate.id]
                
                # Check if intervals intersect
                intersection_start = max(current_interval[0], candidate_interval[0])
                intersection_end = min(current_interval[1], candidate_interval[1])
                
                if intersection_start <= intersection_end:
                    # Valid intersection found, check economic profit
                    temp_group = Group(0)  # Temporary group for evaluation
                    for comp in current_group.components:
                        temp_group.add_component(comp)
                    temp_group.add_component(candidate)
                    
                    # Find optimal time within the intersection
                    optimal_time = find_optimal_group_time(temp_group)[0]
                    
                    # Check if optimal time is within the intersection
                    if intersection_start <= optimal_time <= intersection_end:
                        profit, _ = compute_group_economic_profit(temp_group, optimal_time, get_production_line_by_id)
                        
                        # Update best candidate if profit is better
                        if profit > best_profit:
                            best_profit = profit
                            best_component = candidate
                            best_interval = (intersection_start, intersection_end)
                            best_time = optimal_time
            
            # If a profitable addition was found, add it to the group
            if best_component and best_profit > 0:
                # Add component to group
                current_group.add_component(best_component)
                # Update current interval to the intersection
                current_interval = best_interval
                # Remove component from available list
                available_components.remove(best_component)
            else:
                # No more profitable additions possible
                improvements = False
        
        # Once group is complete, update execution schedules
        if len(current_group.components) > 1:
            # Only update if there's more than one component (actual group)
            group_time = find_optimal_group_time(current_group)[0]
            update_component_schedule(current_group, group_time)
        
        # Add the group to the solution
        solution.solution.append(current_group)
        group_id += 1
    
    # Calculate total cost for the solution
    # This would require implementing a cost calculation for the entire solution
    # which is not clearly defined in the provided code
    
    return solution