class ProductionLine:
    def __init__(self, id):
        self.id = id
        self.corrective_maintenance_set_up_cost = 0
        self.preventive_maintenance_set_up_cost = 0
        self.downtime_cost_rate = 0
        self.components = [] # List of components in the production line