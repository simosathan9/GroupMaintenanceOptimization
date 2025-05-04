from group import Group
from group_analysis import compute_grouping_structure_cost
from local_search import local_search_scheme, clone_groups
from alns import alns_scheme

def combined_scheme(initial_solution, get_production_line_by_id, planning_horizon,
                   max_iterations=100, 
                   local_search_frequency=5,
                   local_search_iterations=10,
                   alns_iterations=20,
                   initial_temperature=100, 
                   cooling_rate=0.95):
    """
    Combined scheme that alternates between ALNS (for diversification) and 
    local search (for intensification).
    
    Args:
        initial_solution: Initial grouping solution
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        max_iterations: Maximum number of combined iterations
        local_search_frequency: How often to apply local search
        local_search_iterations: Number of iterations for local search
        alns_iterations: Number of iterations for ALNS per combined iteration
        initial_temperature: Initial temperature for ALNS simulated annealing
        cooling_rate: Cooling rate for ALNS temperature
        
    Returns:
        Best solution found during the search
    """
    current_solution = clone_groups(initial_solution)
    current_cost = compute_grouping_structure_cost(current_solution, get_production_line_by_id, planning_horizon)
    
    best_solution = clone_groups(current_solution)
    best_cost = current_cost
    
    print(f"Initial cost: {current_cost:.2f}")
    
    # Main loop for the combined approach
    for iteration in range(max_iterations):
        print(f"Combined iteration {iteration + 1}/{max_iterations}")
        
        # Run ALNS for diversification
        print("  Running ALNS phase (diversification)")
        alns_solution = alns_scheme(
            current_solution,
            get_production_line_by_id,
            planning_horizon,
            max_iterations=alns_iterations,
            non_improving_iterations=alns_iterations,  # Allow full iterations
            initial_temperature=initial_temperature,
            cooling_rate=cooling_rate
        )
        
        # Evaluate ALNS solution
        alns_cost = compute_grouping_structure_cost(alns_solution, get_production_line_by_id, planning_horizon)
        
        # Apply local search for intensification if it's time
        if iteration % local_search_frequency == 0:
            print("  Running local search phase (intensification)")
            ls_solution = local_search_scheme(
                alns_solution, 
                get_production_line_by_id, 
                planning_horizon,
                max_iterations=local_search_iterations
            )
            
            # Evaluate local search solution
            ls_cost = compute_grouping_structure_cost(ls_solution, get_production_line_by_id, planning_horizon)
            
            # Compare with ALNS solution
            if ls_cost < alns_cost:
                print(f"  Local search improved the ALNS solution by {alns_cost - ls_cost:.2f}")
                current_solution = clone_groups(ls_solution)
                current_cost = ls_cost
            else:
                print(f"  Local search did not improve the ALNS solution")
                current_solution = clone_groups(alns_solution)
                current_cost = alns_cost
        else:
            # Use ALNS solution directly
            current_solution = clone_groups(alns_solution)
            current_cost = alns_cost
        
        # Check if we found a new best solution
        if current_cost < best_cost:
            best_solution = clone_groups(current_solution)
            best_cost = current_cost
            print(f"  New best solution found: {best_cost:.2f}")
        
        print(f"  Current solution cost: {current_cost:.2f}, Best: {best_cost:.2f}")
    
    print(f"Final best solution cost: {best_cost:.2f}")
    return best_solution