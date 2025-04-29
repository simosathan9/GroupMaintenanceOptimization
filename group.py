class Group:
    def __init__(self, id):
        self.id = id
        self.components = [] # List of components in the group
        self.group_cost = 0 # Cost of the group
        self.group_begin_time = 0 # Time when the group begins
        self.group_end_time = 0 # Time when the group ends
        self.group_total_downtime = 0 # Total maintenance duration of the group
        self.economic_profit = 0
        
    def add_component(self, component):
        self.components.append(component)
        #self.group_cost += component.preventive_maintenance_cost
        #self.group_begin_time = min(self.group_begin_time, component.preventive_maintenance_duration) if self.group_begin_time else component.preventive_maintenance_duration
        #self.group_end_time = max(self.group_end_time, component.preventive_maintenance_duration) if self.group_end_time else component.preventive_maintenance_duration
    
    def remove_component(self, component):
        self.components.remove(component)
        #self.group_cost -= component.preventive_maintenance_cost
        #self.group_begin_time = min(self.group_begin_time, component.preventive_maintenance_duration) if self.group_begin_time else component.preventive_maintenance_duration
        #self.group_end_time = max(self.group_end_time, component.preventive_maintenance_duration) if self.group_end_time else component.preventive_maintenance_duration