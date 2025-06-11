
import random
import numpy as np
import math
from group import Group
from group_analysis import (
    find_feasible_interval,
    find_non_intersecting_pairs,
    find_optimal_group_time,
    compute_group_economic_profit,
    compute_grouping_structure_cost
)

class DestroyOperator:
    def __init__(self, name, function):
        self.name = name
        self.function = function
        self.weight = 1.0
        self.score = 0
        self.num_calls = 0
    
    def apply(self, solution, level, get_production_line_by_id, planning_horizon):
        return self.function(solution, level, get_production_line_by_id, planning_horizon)
    
    def update_weight(self, reaction_factor):
        if self.num_calls > 0:
            avg_score = self.score / self.num_calls
            self.weight = (1 - reaction_factor) * self.weight + reaction_factor * avg_score
        # Keep current weight if no calls made
        
    def reset_score(self):
        self.score = 0
        self.num_calls = 0

class RepairOperator:
    def __init__(self, name, function):
        self.name = name
        self.function = function
        self.weight = 1.0
        self.score = 0
        self.num_calls = 0
    
    def apply(self, solution, removed_components, get_production_line_by_id, planning_horizon):
        return self.function(solution, removed_components, get_production_line_by_id, planning_horizon)
    
    def update_weight(self, reaction_factor):
        if self.num_calls > 0:
            avg_score = self.score / self.num_calls
            self.weight = (1 - reaction_factor) * self.weight + reaction_factor * avg_score
        # Keep current weight if no calls made
        
    def reset_score(self):
        self.score = 0
        self.num_calls = 0

# Destroy operators
def random_removal(solution, level, get_production_line_by_id, planning_horizon):
    """
    Randomly removes a percentage of components from their groups.
    
    Args:
        solution: Current solution (list of groups)
        level: Percentage of components to remove (0.0-1.0)
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        
    Returns:
        Modified solution and list of removed components
    """
    all_components = []
    for group in solution:
        all_components.extend(group.components)
    
    if not all_components:
        return [], []
    
    num_to_remove = max(1, min(len(all_components), int(len(all_components) * level)))
    components_to_remove = random.sample(all_components, num_to_remove)
    
    # Make a copy of the solution
    new_solution = []
    for group in solution:
        new_group = Group(group.id)
        new_group.production_line_id = group.production_line_id  # Preserve line ID
        for component in group.components:
            if component not in components_to_remove:
                new_group.add_component(component)
        if len(new_group.components) > 0:
            new_solution.append(new_group)
    
    return new_solution, components_to_remove

def worst_group_removal(solution, level, get_production_line_by_id, planning_horizon):
    """
    Removes components from groups with the lowest economic profit.
    
    Args:
        solution: Current solution (list of groups)
        level: Percentage of components to remove (0.0-1.0)
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        
    Returns:
        Modified solution and list of removed components
    """
    # Calculate total components
    all_components = []
    for group in solution:
        all_components.extend(group.components)
    
    if not all_components:
        return [], []
    
    # Calculate profit for each group with more than one component
    group_profits = []
    for group in solution:
        if len(group.components) > 1:
            try:
                group_time = find_optimal_group_time(group)[0]
                profit, _ = compute_group_economic_profit(group, group_time, get_production_line_by_id)
                group_profits.append((group, profit))
            except (IndexError, ValueError):
                # Handle case where group time calculation fails
                group_profits.append((group, float('-inf')))
    
    # If no groups with multiple components, fall back to random removal
    if not group_profits:
        return random_removal(solution, level, get_production_line_by_id, planning_horizon)
    
    # Sort groups by profit (ascending)
    group_profits.sort(key=lambda x: x[1])
    
    num_to_remove = max(1, min(len(all_components), int(len(all_components) * level)))
    
    # Select components from worst groups until we've removed enough
    components_to_remove = []
    for group, _ in group_profits:
        if len(components_to_remove) >= num_to_remove:
            break
        
        # Choose how many components to remove from this group (at least 1)
        num_from_group = min(len(group.components), num_to_remove - len(components_to_remove))
        
        # Select components to remove
        group_components = list(group.components)
        if num_from_group > 0:
            chosen = random.sample(group_components, num_from_group)
            components_to_remove.extend(chosen)
    
    # Make a copy of the solution without the removed components
    new_solution = []
    for group in solution:
        new_group = Group(group.id)
        new_group.production_line_id = group.production_line_id  # Preserve line ID
        for component in group.components:
            if component not in components_to_remove:
                new_group.add_component(component)
        if len(new_group.components) > 0:
            new_solution.append(new_group)
    
    return new_solution, components_to_remove

def related_removal(solution, level, get_production_line_by_id, planning_horizon):
    """
    Removes components that are similar in terms of feasible intervals.
    
    Args:
        solution: Current solution (list of groups)
        level: Percentage of components to remove (0.0-1.0)
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        
    Returns:
        Modified solution and list of removed components
    """
    all_components = []
    for group in solution:
        all_components.extend(group.components)
    
    num_to_remove = max(1, int(len(all_components) * level))
    
    # Calculate feasible intervals for all components
    intervals = {}
    for component in all_components:
        interval = find_feasible_interval(component, get_production_line_by_id)
        if interval:
            intervals[component] = interval
    
    # Choose a random seed component
    if len(intervals) == 0:
        # Fall back to random if no intervals found
        return random_removal(solution, level, get_production_line_by_id, planning_horizon)
    
    seed_component = random.choice(list(intervals.keys()))
    components_to_remove = [seed_component]
    
    # Compute the interval similarity (inverse of the distance between interval midpoints)
    seed_midpoint = (intervals[seed_component][0] + intervals[seed_component][1]) / 2
    similarity = []
    for component, interval in intervals.items():
        if component == seed_component:
            continue
        midpoint = (interval[0] + interval[1]) / 2
        distance = abs(midpoint - seed_midpoint)
        similarity.append((component, distance))
    
    # Sort by similarity (closest intervals first)
    similarity.sort(key=lambda x: x[1])
    
    # Add the most similar components until we have enough
    for component, _ in similarity:
        if len(components_to_remove) >= num_to_remove:
            break
        components_to_remove.append(component)
    
    # Make a copy of the solution without the removed components
    new_solution = []
    for group in solution:
        new_group = Group(group.id)
        new_group.production_line_id = group.production_line_id  # Preserve line ID
        for component in group.components:
            if component not in components_to_remove:
                new_group.add_component(component)
        if len(new_group.components) > 0:
            new_solution.append(new_group)
    
    return new_solution, components_to_remove

def production_line_removal(solution, level, get_production_line_by_id, planning_horizon):
    """
    Removes components from a randomly selected production line.
    
    Args:
        solution: Current solution (list of groups)
        level: Percentage of components to remove (0.0-1.0)
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        
    Returns:
        Modified solution and list of removed components
    """
    # Calculate total components
    all_components = []
    for group in solution:
        all_components.extend(group.components)
    
    if not all_components:
        return [], []
    
    # Identify all production lines in the solution
    production_lines = set()
    for group in solution:
        if group.production_line_id is not None:
            production_lines.add(group.production_line_id)
    
    # If there are no production lines, fall back to random removal
    if not production_lines:
        return random_removal(solution, level, get_production_line_by_id, planning_horizon)
    
    # Select a random production line
    target_line = random.choice(list(production_lines))
    
    # Collect all components from the selected production line
    line_components = []
    for group in solution:
        if group.production_line_id == target_line:
            line_components.extend(group.components)
    
    if not line_components:
        return random_removal(solution, level, get_production_line_by_id, planning_horizon)
    
    # Calculate how many components to remove
    max_to_remove = min(len(line_components), int(len(all_components) * level))
    num_to_remove = max(1, max_to_remove)
    
    # Select components to remove
    components_to_remove = random.sample(line_components, num_to_remove)
    
    # Make a copy of the solution without the removed components
    new_solution = []
    for group in solution:
        new_group = Group(group.id)
        new_group.production_line_id = group.production_line_id  # Preserve line ID
        for component in group.components:
            if component not in components_to_remove:
                new_group.add_component(component)
        if len(new_group.components) > 0:
            new_solution.append(new_group)
    
    return new_solution, components_to_remove

# Repair operators
def greedy_repair(solution, removed_components, get_production_line_by_id, planning_horizon):
    """
    Re-inserts components greedily, choosing the best group for each component.
    Ensures components are only added to groups from the same production line.
    
    Args:
        solution: Current solution (list of groups)
        removed_components: List of components to reinsert
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        
    Returns:
        Modified solution
    """
    # Make sure solution is a list
    new_solution = list(solution)
    if not new_solution and not removed_components:
        return new_solution
        
    # Generate unique group ID
    existing_ids = {group.id for group in new_solution}
    next_group_id = max(existing_ids, default=0) + 1
    
    # Calculate non-intersecting pairs for constraint checking
    all_components = []
    for group in solution:
        all_components.extend(group.components)
    all_components.extend(removed_components)
    
    if not all_components:
        return new_solution
    
    non_intersecting_pairs = find_non_intersecting_pairs(all_components, find_feasible_interval, get_production_line_by_id)
    non_intersecting_set = set()
    for comp1, comp2 in non_intersecting_pairs:
        non_intersecting_set.add((comp1.id, comp2.id))
        non_intersecting_set.add((comp2.id, comp1.id))
    
    # Cache for group costs to avoid redundant calculations
    group_cost_cache = {}
    
    # Process each component
    for component in removed_components:
        # Try adding to each existing group from the same production line
        best_group = None
        best_cost_increase = float('inf')
        
        # Calculate baseline cost - if the component were in its own group
        baseline_group = Group(-1)  # Temporary group just for calculation
        baseline_group.add_component(component)
        # Ensure group has valid timing before cost calculation
        find_optimal_group_time(baseline_group)
        baseline_cost = compute_grouping_structure_cost([baseline_group], get_production_line_by_id, planning_horizon)
        
        for group in new_solution:
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
            
            # Use cached cost or calculate it
            group_key = tuple(sorted([c.id for c in group.components]))
            if group_key not in group_cost_cache:
                find_optimal_group_time(group)
                group_cost_cache[group_key] = compute_grouping_structure_cost([group], get_production_line_by_id, planning_horizon)
            old_group_cost = group_cost_cache[group_key]
            
            # Make a temporary copy of the group with the new component
            temp_group = Group(group.id)
            temp_group.production_line_id = group.production_line_id
            for c in group.components:
                temp_group.add_component(c)
            temp_group.add_component(component)
            
            # Ensure temp group has valid timing before cost calculation
            find_optimal_group_time(temp_group)
            
            # Calculate new cost of this group with the component added
            new_group_cost = compute_grouping_structure_cost([temp_group], get_production_line_by_id, planning_horizon)
            
            # Calculate cost increase
            cost_increase = new_group_cost - old_group_cost
            
            # If this is better than our current best option, update it
            if cost_increase < best_cost_increase:
                best_cost_increase = cost_increase
                best_group = group
        
        # Check if creating a new group is better than adding to an existing group
        new_group_cost_increase = baseline_cost
        
        if best_group is None or new_group_cost_increase <= best_cost_increase:
            # Create a new group for this component
            new_group = Group(next_group_id)
            new_group.add_component(component)
            new_solution.append(new_group)
            next_group_id += 1
        else:
            # Add to the best existing group
            best_group.add_component(component)
            find_optimal_group_time(best_group)
    
    # Final update of all groups' properties
    for group in new_solution:
        find_optimal_group_time(group)
    
    return new_solution

def regret_repair(solution, removed_components, get_production_line_by_id, planning_horizon):
    """
    Re-inserts components based on a regret measure.
    Ensures components are only added to groups from the same production line.
    
    Args:
        solution: Current solution (list of groups)
        removed_components: List of components to reinsert
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        
    Returns:
        Modified solution
    """
    # Make sure solution is a list
    new_solution = list(solution)
    if not new_solution and not removed_components:
        return new_solution
        
    # Generate unique group ID
    existing_ids = {group.id for group in new_solution}
    next_group_id = max(existing_ids, default=0) + 1
    
    # Calculate non-intersecting pairs for constraint checking
    all_components = []
    for group in solution:
        all_components.extend(group.components)
    all_components.extend(removed_components)
    
    non_intersecting_pairs = find_non_intersecting_pairs(all_components, find_feasible_interval, get_production_line_by_id)
    non_intersecting_set = set()
    for comp1, comp2 in non_intersecting_pairs:
        non_intersecting_set.add((comp1.id, comp2.id))
        non_intersecting_set.add((comp2.id, comp1.id))
    
    # Calculate costs for all possible insertions
    component_costs = []
    for component in removed_components:
        # Check each existing group from the same production line
        group_costs = []
        for group in new_solution:
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
            
            # Ensure both groups have valid timing before cost calculation
            find_optimal_group_time(temp_group)
            find_optimal_group_time(group)
            
            # Calculate new cost of this group with the component added
            new_group_cost = compute_grouping_structure_cost([temp_group], get_production_line_by_id, planning_horizon)
            
            # Calculate cost increase (new_group_cost - old_group_cost)
            old_group_cost = compute_grouping_structure_cost([group], get_production_line_by_id, planning_horizon)
            cost_increase = new_group_cost - old_group_cost
            
            group_costs.append((group, cost_increase))
        
        # Calculate cost for new group
        baseline_group = Group(-1)  # Temporary group just for calculation
        baseline_group.add_component(component)
        find_optimal_group_time(baseline_group)
        new_group_cost = compute_grouping_structure_cost([baseline_group], get_production_line_by_id, planning_horizon)
        
        # Sort costs and compute regret
        group_costs.sort(key=lambda x: x[1])
        
        # Calculate regret (difference between best and second best)
        if len(group_costs) >= 2:
            regret = group_costs[1][1] - group_costs[0][1]
        elif len(group_costs) == 1:
            regret = new_group_cost - group_costs[0][1]
        else:
            regret = 0
        
        component_costs.append((component, group_costs, regret, new_group_cost))
    
    # Sort components by regret (descending)
    component_costs.sort(key=lambda x: x[2], reverse=True)
    
    # Process components in order of regret
    for component, group_costs, _, new_group_cost in component_costs:
        # Check if any groups are still valid
        valid_groups = []
        for group, cost in group_costs:
            # Verify the component can still be added (constraints might have changed)
            if not group.can_add_component(component):
                continue
                
            can_be_added = True
            for existing_comp in group.components:
                if (component.id, existing_comp.id) in non_intersecting_set:
                    can_be_added = False
                    break
            
            if can_be_added:
                valid_groups.append((group, cost))
        
        if valid_groups:
            # Find the best group
            best_group, _ = min(valid_groups, key=lambda x: x[1])
            
            # Add to the best group
            best_group.add_component(component)
            find_optimal_group_time(best_group)
        else:
            # Create a new group
            new_group = Group(next_group_id)
            new_group.add_component(component)
            new_solution.append(new_group)
            next_group_id += 1
    
    # Final update of all groups' properties
    for group in new_solution:
        find_optimal_group_time(group)
    
    return new_solution

def random_repair(solution, removed_components, get_production_line_by_id, planning_horizon):
    """
    Re-inserts components randomly, respecting feasibility and production line constraints.
    
    Args:
        solution: Current solution (list of groups)
        removed_components: List of components to reinsert
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        
    Returns:
        Modified solution
    """
    # Make sure solution is a list
    new_solution = list(solution)
    if not new_solution and not removed_components:
        return new_solution
        
    # Generate unique group ID
    existing_ids = {group.id for group in new_solution}
    next_group_id = max(existing_ids, default=0) + 1
    
    # Calculate non-intersecting pairs for constraint checking
    all_components = []
    for group in solution:
        all_components.extend(group.components)
    all_components.extend(removed_components)
    
    non_intersecting_pairs = find_non_intersecting_pairs(all_components, find_feasible_interval, get_production_line_by_id)
    non_intersecting_set = set()
    for comp1, comp2 in non_intersecting_pairs:
        non_intersecting_set.add((comp1.id, comp2.id))
        non_intersecting_set.add((comp2.id, comp1.id))
    
    # Shuffle components for random insertion order
    random.shuffle(removed_components)
    
    # Process each component
    for component in removed_components:
        # Get all valid groups from the same production line
        valid_groups = []
        for group in new_solution:
            # Check if component can be added to this group (same production line)
            if not group.can_add_component(component):
                continue
                
            # Check if component can be added (no non-intersecting intervals)
            can_be_added = True
            for existing_comp in group.components:
                if (component.id, existing_comp.id) in non_intersecting_set:
                    can_be_added = False
                    break
            
            if can_be_added:
                valid_groups.append(group)
        
        # Also consider option to create a new group
        valid_groups.append(None)
        
        # Choose a group randomly
        chosen_group = random.choice(valid_groups)
        
        if chosen_group is None:
            # Create a new group
            new_group = Group(next_group_id)
            new_group.add_component(component)
            new_solution.append(new_group)
            next_group_id += 1
        else:
            # Add to the chosen group
            chosen_group.add_component(component)
    
    return new_solution

def regret_k_repair(solution, removed_components, get_production_line_by_id, planning_horizon, k=3):
    """
    Re-inserts components based on a k-regret measure.
    Ensures components are only added to groups from the same production line.
    
    Args:
        solution: Current solution (list of groups)
        removed_components: List of components to reinsert
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        k: Regret parameter (default 3)
        
    Returns:
        Modified solution
    """
    # Make sure solution is a list
    new_solution = list(solution)
    if not new_solution and not removed_components:
        return new_solution
        
    # Generate unique group ID
    existing_ids = {group.id for group in new_solution}
    next_group_id = max(existing_ids, default=0) + 1
    
    # Calculate non-intersecting pairs for constraint checking
    all_components = []
    for group in solution:
        all_components.extend(group.components)
    all_components.extend(removed_components)
    
    non_intersecting_pairs = find_non_intersecting_pairs(all_components, find_feasible_interval, get_production_line_by_id)
    non_intersecting_set = set()
    for comp1, comp2 in non_intersecting_pairs:
        non_intersecting_set.add((comp1.id, comp2.id))
        non_intersecting_set.add((comp2.id, comp1.id))
    
    while removed_components:
        # Calculate costs for all possible insertions
        component_costs = []
        for component in removed_components:
            # Check each existing group from the same production line
            group_costs = []
            for group in new_solution:
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
                
                # Calculate new cost of this group with the component added
                new_group_cost = compute_grouping_structure_cost([temp_group], get_production_line_by_id, planning_horizon)
                
                # Calculate cost increase (new_group_cost - old_group_cost)
                old_group_cost = compute_grouping_structure_cost([group], get_production_line_by_id, planning_horizon)
                cost_increase = new_group_cost - old_group_cost
                
                group_costs.append((group, cost_increase))
            
            # Calculate cost for new group
            baseline_group = Group(-1)  # Temporary group just for calculation
            baseline_group.add_component(component)
            new_group_cost = compute_grouping_structure_cost([baseline_group], get_production_line_by_id, planning_horizon)
            
            # Sort costs and compute k-regret
            group_costs.sort(key=lambda x: x[1])
            
            # Calculate k-regret (difference between best and k-th best)
            k_regret = 0
            if len(group_costs) >= k:
                k_regret = group_costs[k-1][1] - group_costs[0][1]
            elif len(group_costs) > 0:
                k_regret = new_group_cost - group_costs[0][1]
            
            component_costs.append((component, group_costs, k_regret, new_group_cost))
        
        # Sort components by k-regret (descending)
        component_costs.sort(key=lambda x: x[2], reverse=True)
        
        if not component_costs:
            break
            
        # Take the component with the highest k-regret
        component, group_costs, _, new_group_cost = component_costs[0]
        
        # Remove it from the list
        removed_components.remove(component)
        
        # Check if any groups are still valid
        valid_groups = []
        for group, cost in group_costs:
            # Verify the component can still be added
            if not group.can_add_component(component):
                continue
                
            can_be_added = True
            for existing_comp in group.components:
                if (component.id, existing_comp.id) in non_intersecting_set:
                    can_be_added = False
                    break
            
            if can_be_added:
                valid_groups.append((group, cost))
        
        if valid_groups:
            # Find the best group
            best_group, _ = min(valid_groups, key=lambda x: x[1])
            
            # Add to the best group
            best_group.add_component(component)
            find_optimal_group_time(best_group)
        else:
            # Create a new group
            new_group = Group(next_group_id)
            new_group.add_component(component)
            new_solution.append(new_group)
            next_group_id += 1
    
    return new_solution

def clone_groups(groups):
    """
    Efficiently clone groups, preserving production line constraints.
    Keep the same component references for performance.
    """
    if not groups:
        return []
    
    cloned_groups = []
    for group in groups:
        new_group = Group(group.id)
        new_group.production_line_id = group.production_line_id  # Preserve production line ID
        # Use list comprehension for better performance
        new_group.components = list(group.components)
        cloned_groups.append(new_group)
    return cloned_groups

def alns_scheme(initial_solution, get_production_line_by_id, planning_horizon, 
                max_iterations=100, non_improving_iterations=20,
                destroy_operators=None, repair_operators=None,
                sigma1=33, sigma2=9, sigma3=3, rho=0.5,
                initial_temperature=100, cooling_rate=0.95):
    """
    Adaptive Large Neighborhood Search for the Group Maintenance Problem.
    
    Args:
        initial_solution: Initial grouping solution
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Planning horizon in days
        max_iterations: Maximum number of iterations
        non_improving_iterations: Maximum number of non-improving iterations
        destroy_operators: List of destroy operators (optional)
        repair_operators: List of repair operators (optional)
        sigma1: Score for new global best solution
        sigma2: Score for new better solution
        sigma3: Score for accepted worse solution
        rho: Reaction factor for weight updates
        initial_temperature: Initial temperature for simulated annealing
        cooling_rate: Cooling rate for temperature
        
    Returns:
        Best solution found during the search
    """
    # Input validation
    if not initial_solution:
        raise ValueError("Initial solution cannot be empty")
    
    if max_iterations <= 0:
        raise ValueError("max_iterations must be positive")
    
    if non_improving_iterations <= 0:
        raise ValueError("non_improving_iterations must be positive")
    
    if not (0 < rho <= 1):
        raise ValueError("rho must be between 0 and 1")
    
    if initial_temperature <= 0:
        raise ValueError("initial_temperature must be positive")
    
    if not (0 < cooling_rate < 1):
        raise ValueError("cooling_rate must be between 0 and 1")
    
    if planning_horizon <= 0:
        raise ValueError("planning_horizon must be positive")
    
    # Set up destroy and repair operators if not provided
    if destroy_operators is None:
        destroy_operators = [
            DestroyOperator("random_removal", random_removal),
            DestroyOperator("worst_group_removal", worst_group_removal),
            DestroyOperator("related_removal", related_removal),
            DestroyOperator("production_line_removal", production_line_removal)
        ]
    
    if repair_operators is None:
        repair_operators = [
            RepairOperator("greedy_repair", greedy_repair),
            RepairOperator("regret_repair", regret_repair),
            RepairOperator("random_repair", random_repair),
            RepairOperator("regret_k_repair", lambda s, r, g, p: regret_k_repair(s, r, g, p, k=3))
        ]
    
    # Initialize solutions and costs
    try:
        current_solution = clone_groups(initial_solution)
        current_cost = compute_grouping_structure_cost(current_solution, get_production_line_by_id, planning_horizon)
        
        best_solution = clone_groups(current_solution)
        best_cost = current_cost
    except Exception as e:
        raise ValueError(f"Failed to evaluate initial solution: {str(e)}")
    
    # Simulated annealing parameters
    temperature = initial_temperature
    
    # Counter for non-improving iterations
    non_improving_count = 0
    
    print(f"Initial cost: {current_cost:.2f}")
    print(f"{'Iter':<6} {'Best Cost':<12} {'Current Cost':<15} {'Destroy Op':<20} {'Repair Op':<20}")
    print("-" * 73)
    
    # Main ALNS loop
    for iteration in range(max_iterations):
        if non_improving_count >= non_improving_iterations:
            print(f"Stopping: {non_improving_count} iterations without improvement")
            break
        
        # Select destroy operator based on weights
        destroy_weights = [op.weight for op in destroy_operators]
        destroy_sum = sum(destroy_weights)
        destroy_probs = [w / destroy_sum for w in destroy_weights]
        destroy_op = np.random.choice(destroy_operators, p=destroy_probs)
        
        # Select repair operator based on weights
        repair_weights = [op.weight for op in repair_operators]
        repair_sum = sum(repair_weights)
        repair_probs = [w / repair_sum for w in repair_weights]
        repair_op = np.random.choice(repair_operators, p=repair_probs)
        
        # Apply destroy operator (determine destroy percentage randomly)
        destroy_level = random.uniform(0.05, 0.30)  # Remove 5% to 30% of components
        new_solution, removed_components = destroy_op.apply(current_solution, destroy_level, get_production_line_by_id, planning_horizon)
        
        # Apply repair operator
        new_solution = repair_op.apply(new_solution, removed_components, get_production_line_by_id, planning_horizon)
        
        # Evaluate new solution
        new_cost = compute_grouping_structure_cost(new_solution, get_production_line_by_id, planning_horizon)
        
        # Print iteration information
        print(f"{iteration + 1:<6} {best_cost:<12.2f} {new_cost:<15.2f} {destroy_op.name:<20} {repair_op.name:<20}")
        
        # Update operator counts
        destroy_op.num_calls += 1
        repair_op.num_calls += 1
        
        # Determine whether to accept the new solution
        accept = False
        score = 0
        
        # New global best
        if new_cost < best_cost:
            best_solution = clone_groups(new_solution)
            best_cost = new_cost
            score = sigma1
            accept = True
            non_improving_count = 0
        
        # Better than current
        elif new_cost < current_cost:
            score = sigma2
            accept = True
            non_improving_count = 0
        
        # Worse than current - accept based on simulated annealing
        else:
            # Simulate annealing acceptance probability
            delta = new_cost - current_cost
            if temperature > 1e-10:  # Avoid division by zero
                p = math.exp(-delta / temperature)
                if random.random() < p:
                    accept = True
                    score = sigma3
            non_improving_count += 1
        
        # Update solution if accepted
        if accept:
            current_solution = clone_groups(new_solution)
            current_cost = new_cost
            
            # Update scores
            destroy_op.score += score
            repair_op.score += score
        
        # Update weights every 10 iterations
        if iteration % 10 == 0 and iteration > 0:
            for op in destroy_operators:
                op.update_weight(rho)
                
            for op in repair_operators:
                op.update_weight(rho)
                
            # Reset scores
            for op in destroy_operators + repair_operators:
                op.reset_score()
        
        # Cool down temperature
        temperature *= cooling_rate
    
    print(f"Best solution cost: {best_cost:.2f}")
    return best_solution