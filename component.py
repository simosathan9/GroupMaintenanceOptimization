class Component:
    def __init__(self, id, duration, corrective_specific_cost, preventive_specific_cost, production_line, lamda_efr, mean_time_between_failures, optimal_execution_time, CR):
        self.id = id
        self.preventive_maintenance_duration = duration # Maintenance duration in minutes
        self.production_line_id = production_line.id
        self.downtime_cost = production_line.downtime_cost_rate * self.preventive_maintenance_duration
        self.corrective_maintenance_cost = production_line.corrective_maintenance_set_up_cost + corrective_specific_cost # For corrective maintenance downtime cost is considered negligible
        self.preventive_maintenance_cost = production_line.preventive_maintenance_set_up_cost + preventive_specific_cost + self.downtime_cost 
        self.lamda_efr = lamda_efr
        self.mean_time_between_failures = mean_time_between_failures
        self.optimal_execution_time_synthetic = optimal_execution_time
        self.long_term_cost_rate_synthetic = CR
    
    def __str__(self):
        return f"Component ID: {self.id}, Production Line ID: {self.production_line_id}, Preventive Maintenance Duration: {self.preventive_maintenance_duration}, Corrective Maintenance Cost: {self.corrective_maintenance_cost}, Preventive Maintenance Cost: {self.preventive_maintenance_cost}, Downtime Cost: {self.downtime_cost}, Lambda EFR: {self.lamda_efr}, MTBF: {self.mean_time_between_failures}, Optimal Execution Time: {self.optimal_execution_time_synthetic}"