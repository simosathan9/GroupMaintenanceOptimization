class ProductionLine:
    def __init__(self, id, corrective_maintenance_set_up_cost, preventive_maintenance_set_up_cost, downtime_cost_rate):
        self.id = id
        self.corrective_maintenance_set_up_cost = corrective_maintenance_set_up_cost
        self.preventive_maintenance_set_up_cost = preventive_maintenance_set_up_cost
        self.downtime_cost_rate = downtime_cost_rate
        self.components = [] # List of components in the production line
        