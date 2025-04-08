class Group:
    def __init__(self, id):
        self.id = id
        self.components = [] # List of components in the group
        self.group_cost = 0 # Cost of the group
        self.group_begin_time = 0 # Time when the group begins
        self.group_end_time = 0 # Time when the group ends