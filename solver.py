# Start by reading the data
from instance_reader import InstanceReader
from component import Component

reader = InstanceReader("Data_JPR.xlsx")
data = reader.read_data().rename(columns={
    'Maintenance duration [minutes]': 'Duration',
    'Maintenance frequency [days]': 'Frequency',
    'Groupe de Gamme': 'Groupe de Gamme',
    'Compteur Groupe Gamme': 'Compteur Groupe Gamme'
})
# for each row in the data, create a component object and add it to the components list
components = []
production_lines = []
# Will keep all production lines in a list
# Each production line will have its own components
# Will organize components into groups
# Each component has a production line id which is the id of the production line it belongs to
# Each component has a group id which is the id of the group it belongs to
# We will apply metaheuristics to add components to groups
# Set-up cost reduction will be calculated here as we will maintain the production_lines list in this file.

# It is necessary to have the production lines list in this file so that when set-up cost reduction occurs
# due to a component being added to a group we can retrieve the production line to which the component belongs and that stores the set-up cost

# In the same way we will calculate the downtime cost reduction as each production line is accompanied with its downtime cost rate
for index, row in data.iterrows():
    component = Component(row['ID'], row['Duration'], row['Frequency'], row['Groupe de Gamme'], row['Compteur Groupe Gamme'])
    components.append(component)
    # Print the components
    print(component.__str__())

#def calculate_setup_cost_reduction(group)
#def calculate_downtime_cost_reduction(group)
