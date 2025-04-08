class Component:
    """ Use them when we obtain the data
    self.preventive_maintenance_cost = #
    self.production_line_id = #
    self.corrective_maintenance_cost = #
    self.lamda_efr = #
    self.mean_time_between_failures = #
    self.optimal_execution_time = #
    
    """
    def __init__(self, id, duration, frequency, groupe_de_gamme, compteur_groupe_gamme):
        self.id = id
        self.preventive_maintenance_duration = duration # Maintenance duration in minutes
        self.frequency = frequency # Maintenance frequency in days
        self.groupe_de_gamme = groupe_de_gamme
        self.compteur_groupe_gamme = compteur_groupe_gamme
    
    def __str__(self):
        return f"Component {self.id} with maintenace duration {self.preventive_maintenance_duration} minute/s and frequency {self.frequency} day/s. Groupe de Gamme: {self.groupe_de_gamme}, Compteur Groupe Gamme: {self.compteur_groupe_gamme}"
        
        