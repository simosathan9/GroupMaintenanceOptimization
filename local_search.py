from group import Group
from group_analysis import (
    find_feasible_interval,
    find_non_intersecting_pairs,
    find_optimal_group_time,
    compute_group_economic_profit,
    compute_grouping_structure_cost
)

def swap_operator(groups, planning_horizon, get_production_line_by_id, tabu_list):
    """
    Perform a swap operation between two groups.
    
    Args:
        groups: List of groups
        planning_horizon: Planning horizon in days
        get_production_line_by_id: Function to get production line by ID
        
    Returns:
        Tuple containing the best groups, components, and cost reduction
    """
    best_cost_reduction = None
    best_group1 = None
    best_group2 = None
    best_component1 = None
    best_component2 = None
    initial_cost = compute_grouping_structure_cost(groups, get_production_line_by_id, planning_horizon)
    
    # Iterate through all pairs of groups
    for i, group_1 in enumerate(groups):
        for j, group_2 in enumerate(groups):
            # Skip if it's the same group
            if i == j:
                continue
                
            # Try swapping each component from group_1 with each component from group_2
            for component_1 in group_1.components:
                for component_2 in group_2.components:
                    # Swap components
                    if ("swap", component_1.id, component_2.id) in tabu_list:
                        continue
                    group_1.remove_component(component_1)
                    group_2.remove_component(component_2)
                    group_1.add_component(component_2)
                    group_2.add_component(component_1)

                    # Calculate the new cost
                    new_cost = compute_grouping_structure_cost(groups, get_production_line_by_id, planning_horizon)

                    # Calculate the cost reduction
                    cost_reduction = initial_cost - new_cost

                    # Check if this is the best swap so far
                    if best_cost_reduction is None or cost_reduction > best_cost_reduction:
                        best_cost_reduction = cost_reduction
                        best_group1 = group_1
                        best_group2 = group_2
                        best_component1 = component_1
                        best_component2 = component_2

                    # Swap back to original state
                    group_1.remove_component(component_2)
                    group_2.remove_component(component_1)
                    group_1.add_component(component_1)
                    group_2.add_component(component_2)
    
    return best_group1, best_group2, best_component1, best_component2, best_cost_reduction

def apply_swap(groups, best_group1, best_group2, best_component1, best_component2):
    """
    Apply the swap operation to the groups.
    """
    # Perform the swap
    best_group1.remove_component(best_component1)
    best_group2.remove_component(best_component2)
    best_group1.add_component(best_component2)
    best_group2.add_component(best_component1)

def relocate_operator(groups, planning_horizon, get_production_line_by_id, tabu_list):
    """
    Perform a relocation operation between two groups.
    
    Args:
        groups: List of groups
        planning_horizon: Planning horizon in days
        get_production_line_by_id: Function to get production line by ID
        
    Returns:
        Tuple containing the best groups, component, and cost reduction
    """
    
    # Identify the component whose relocation leads to the best reduction in the grouping structure cost
    # relocate a component from one group to another
    best_cost_reduction = None
    best_group1 = None
    best_group2 = None
    best_component = None
    initial_cost = compute_grouping_structure_cost(groups, get_production_line_by_id, planning_horizon)
    
    for i, group_1 in enumerate(groups):
        for j, group_2 in enumerate(groups):
            # Skip if it's the same group
            if i >= j:
                continue
                
            # Use a copy of the components list to avoid modification issues during iteration
            for component in group_1.components:    
                # Relocate component
                if ("relocate", component.id, group_1.id, group_2.id) in tabu_list:
                    continue
                
                group_1.remove_component(component)
                group_2.add_component(component)

                # Calculate the new cost
                new_cost = compute_grouping_structure_cost(groups, get_production_line_by_id, planning_horizon)

                # Calculate the cost reduction
                cost_reduction = initial_cost - new_cost
                
                # Check if this is the best relocation so far
                if best_cost_reduction is None or cost_reduction > best_cost_reduction:
                    best_cost_reduction = cost_reduction
                    best_group1 = group_1
                    best_group2 = group_2
                    best_component = component

                # Relocate back to original state
                group_2.remove_component(component)
                group_1.add_component(component)
    
    return best_group1, best_group2, best_component, best_cost_reduction

def apply_relocate(groups, best_group1, best_group2, best_component):
    """
    Apply the relocation operation to the groups.
    """
    # Perform the relocation
    best_group1.remove_component(best_component)
    best_group2.add_component(best_component)

def clone_groups(groups):
    """
    Clone groups without deep copying the components.
    Keep the same component references (no deepcopy).
    """
    from group import Group

    cloned_groups = []
    for group in groups:
        new_group = Group(group.id)
        for component in group.components:
            new_group.add_component(component)  # use the same reference
        cloned_groups.append(new_group)
    return cloned_groups

from collections import deque

def local_search_scheme(groups, get_production_line_by_id, planning_horizon, max_iterations=20, tabu_tenure=5):
    """
    Perform local search to optimize the grouping structure cost.
    
    Args:
        groups: List of groups to optimize
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        max_iterations: Maximum number of iterations
    
    Returns:
        Best solution found during the search
    """
    current_solution = groups
    current_cost = compute_grouping_structure_cost(current_solution, get_production_line_by_id, planning_horizon)
    
    # Track the global best solution
    global_best_solution = clone_groups(current_solution)
    global_best_cost = current_cost
    
    tabu_list = deque(maxlen=tabu_tenure) # Deque is a double-ended queue that allows appending and popping from both ends
    
    print(f"Initial cost: {current_cost:.2f}")
    
    for iteration in range(max_iterations):
        print(f"Iteration {iteration + 1}/{max_iterations}")
        # Apply swap operator
        best_swap = swap_operator(current_solution, planning_horizon, get_production_line_by_id, tabu_list)
        
        # --- Relocate Operator (now respects Tabu list) ---
        best_relocate = relocate_operator(current_solution, planning_horizon, get_production_line_by_id, tabu_list)
        
        # --- Select best move ---
        best_move = None
        if best_swap:
            _, _, _, _, swap_reduction = best_swap
            # Aspiration: Override tabu if this swap beats global best
            if ("swap", best_swap[2].id, best_swap[3].id) not in tabu_list or (current_cost - swap_reduction) < global_best_cost:
                best_move = ("swap", best_swap)
        
        if best_relocate:
            _, _, _, relocate_reduction = best_relocate
            # Aspiration: Override tabu if this relocate beats global best
            if ("relocate", best_relocate[2].id, best_relocate[0].id, best_relocate[1].id) not in tabu_list or (current_cost - relocate_reduction) < global_best_cost:
                if best_move is None or relocate_reduction > best_swap[4]:
                    best_move = ("relocate", best_relocate)
        
        # --- Apply the best move ---
        if best_move:
            move_type, move_data = best_move
            if move_type == "swap":
                g1, g2, c1, c2, cost_reduction = move_data
                print(f"Applying swap: {c1.id} <-> {c2.id}, Cost reduction: {cost_reduction:.2f}")
                apply_swap(current_solution, g1, g2, c1, c2)
                tabu_list.append(("swap", c1.id, c2.id))  # Add to tabu list
                current_cost -= cost_reduction
            else:
                g1, g2, c, cost_reduction = move_data
                print(f"Applying relocate: {c.id} from {g1.id} to {g2.id}, Cost reduction: {cost_reduction:.2f}")
                apply_relocate(current_solution, g1, g2, c)
                tabu_list.append(("relocate", c.id, g1.id, g2.id))  # Add to tabu list
                current_cost -= cost_reduction
            
            # Update global best
            if current_cost < global_best_cost:
                global_best_solution = clone_groups(current_solution)
                global_best_cost = current_cost
    
    return global_best_solution