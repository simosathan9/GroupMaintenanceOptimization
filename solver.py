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
for index, row in data.iterrows():
    component = Component(row['ID'], row['Duration'], row['Frequency'], row['Groupe de Gamme'], row['Compteur Groupe Gamme'])
    components.append(component)
    # Print the components
    print(component.__str__())

