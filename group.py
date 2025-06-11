
class Group:
    def __init__(self, id):
        self.id = id
        self.components = []  # List of components in the group
        self.group_cost = 0  # Cost of the group
        self.group_begin_time = 0  # Time when the group begins
        self.group_end_time = 0  # Time when the group ends
        self.group_total_downtime = 0  # Total maintenance duration of the group
        self.economic_profit = 0
        self.planned_execution_time = 0  # Original planned execution time
        self.effective_execution_time = 0  # Actual execution time after cascading delays
        self.production_line_id = None  # Production line ID for this group
        
    def add_component(self, component):
        # Check if this is the first component (sets the production line)
        if not self.components:
            self.production_line_id = component.production_line_id
        # Verify component belongs to the same production line
        elif self.production_line_id != component.production_line_id:
            raise ValueError(f"Cannot add component {component.id} from line {component.production_line_id} "
                           f"to group {self.id} which belongs to line {self.production_line_id}")
        
        self.components.append(component)
        
    def remove_component(self, component):
        if component not in self.components:
            raise ValueError(f"Component {component.id} not found in group {self.id}")
            
        self.components.remove(component)
        
        # If no components left, reset production line
        if not self.components:
            self.production_line_id = None
        
    def can_add_component(self, component):
        """Check if a component can be added to this group (same production line)"""
        if not self.components:
            return True  # Empty group can accept any component
        return self.production_line_id == component.production_line_id
        
    def get_group_downtime(self):
        """Calculate the total downtime this group adds to the production line"""
        if not self.components:
            return 0
        return max(c.preventive_maintenance_duration for c in self.components)


def apply_cascading_delays(groups_by_line, get_production_line_by_id):
    """
    Apply cascading delay effects to groups within each production line.
    Groups are executed in order of their planned execution time, and each group
    delays all subsequent groups by its downtime duration.
    """
    for line_id, line_groups in groups_by_line.items():
        # Sort groups by planned execution time
        sorted_groups = sorted(line_groups, key=lambda g: g.planned_execution_time)
                 
        cumulative_delay = 0
        for group in sorted_groups:
            # Set effective execution time = planned time + cumulative delay
            group.effective_execution_time = group.planned_execution_time + cumulative_delay
                         
            # Add this group's downtime to cumulative delay for subsequent groups
            cumulative_delay += group.get_group_downtime()


def group_components_by_line(groups):
    """Group components by production line for cascading delay calculation"""
    groups_by_line = {}
    for group in groups:
        if group.components:  # Only process groups with components
            line_id = group.production_line_id
            if line_id not in groups_by_line:
                groups_by_line[line_id] = []
            if group not in groups_by_line[line_id]:
                groups_by_line[line_id].append(group)
    return groups_by_line