class Solution:
    def __init__(self):
        self.solution = [] # List of Group objects. Group objects contain a list of components
        self.total_cost = 0 # Total cost of the solution
        self.total_time = 0 # Total time of the solution
        self.total_downtime = 0
        self.total_downtime_cost = 0
    
    def calculate_total_cost(self, get_production_line_by_id):
        """
        Calculate the total cost of the solution by summing the 
        economic profits of all groups and the base costs.
        """
        total_profit = 0
        total_setup_savings = 0
        total_increased_cost = 0
        
        # Sum up the profits for all non-singleton groups
        for group in self.solution:
            if len(group.components) > 1:
                # Find optimal group execution time
                from group_analysis import find_optimal_group_time, compute_group_economic_profit
                group_time = find_optimal_group_time(group)[0]
                
                # Calculate economic profit
                profit, details = compute_group_economic_profit(group, group_time, get_production_line_by_id)
                
                total_profit += profit
                total_setup_savings += details["setup_savings"]
                total_increased_cost += details["increased_CM_cost"]
                
                # Store the cost in the group for future reference
                group.group_cost = profit
        
        # Calculate total baseline cost (sum of individual optimal costs)
        baseline_cost = 0
        for group in self.solution:
            for component in group.components:
                baseline_cost += component.long_term_cost_rate * 365  # Annual cost
        
        # The total solution cost is the baseline minus the total profit from grouping
        self.total_cost = baseline_cost - total_profit
        
        return {
            "total_cost": self.total_cost,
            "baseline_cost": baseline_cost,
            "total_profit": total_profit,
            "total_setup_savings": total_setup_savings,
            "total_increased_cost": total_increased_cost
        }