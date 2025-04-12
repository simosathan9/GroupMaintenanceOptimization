# Start by reading the data
from instance_reader import InstanceReader
from component import Component
from production_line import ProductionLine
from solution import Solution
from group import Group
import scipy.special as sp  # for the Gamma function
from scipy.optimize import minimize_scalar
import numpy as np

reader = InstanceReader("synthetic_maintenance_data_with_duration.csv")
# for each row in the data, create a component object and add it to the components list
components = []
production_lines = []
solution = Solution()
data = reader.read_data_csv().rename(columns={
    'Line': 'Production Line',
    'Component': 'ID',
    'MTBF': 'MTBF',
    'λ': 'Weibull_Parameter',
    'cp': 'Preventive_Specific_Cost',
    'cc': 'Corrective_Specific_Cost',
    'PM_duration': 'Duration',
    'x*': 'Optimal_Execution_Time',
    'CR': 'Long_term_Cost_Rate',
})
for index, row in data.iterrows():
    production_line = ProductionLine(row['Production Line'], 5, 3, 5)
    production_lines.append(production_line)

def get_production_line_by_id(id):
    for production_line in production_lines:
        if production_line.id == id:
            return production_line
    return None

# Will keep all production lines in a list (DONE)
# Each production line will have its own components (DONE)
# Will organize components into groups (That is the goal)
# Each component has a production line id which is the id of the production line it belongs to (DONE)
# Each component has a group id which is the id of the group it belongs to (Will occur after the grouping)
# We will apply metaheuristics to add components to groups
# Set-up cost reduction will be calculated here as we will maintain the production_lines list in this file. (DONE)

# It is necessary to have the production lines list in this file so that when set-up cost reduction occurs
# due to a component being added to a group we can retrieve the production line to which the component belongs and that stores the set-up cost

# In the same way we will calculate the downtime cost reduction as each production line is accompanied with its downtime cost rate
maintenance_durations = data['Duration'].tolist()
optimal_execution_times = data['Optimal_Execution_Time'].tolist()
for index, row in data.iterrows():
    component = Component(row['ID'], row['Duration'], row['Corrective_Specific_Cost'], row['Preventive_Specific_Cost'], get_production_line_by_id(row['Production Line']), row['Weibull_Parameter'], row['MTBF'], row['Optimal_Execution_Time'], row['Long_term_Cost_Rate'])
    components.append(component)
    # Print the components
    print(component.__str__())

# Add components to the production lines
for component in components:
    production_line = get_production_line_by_id(component.production_line_id)
    production_line.components.append(component)

def calculate_group_setup_cost_PM(group):
    """
    Calculate the setup cost reduction for a group of components.
    Based on assumption 6 from the paper the setup cost is accounted only once for each production line.
    """
    setup_cost_delta = 0
    production_line_ids_accounted = []
    for component in group.components:
        production_line = get_production_line_by_id(component.production_line_id)
        setup_cost_delta += production_line.corrective_maintenance_set_up_cost
        if production_line.id in production_line_ids_accounted:
            setup_cost_delta -= production_line.corrective_maintenance_set_up_cost
        production_line_ids_accounted.append(production_line.id)
    return setup_cost_delta

def calculate_downtime_cost_savings(group): #NOTES: THIS CODE MIGHT HAVE LOGIC ERRORS CHECK AGAIN
    # Get all unique production lines in this group
    production_lines_in_group = set()
    total_duration_per_line = {}
    
    for component in group.components:
        production_line = get_production_line_by_id(component.production_line_id)
        production_lines_in_group.add(production_line)
        
        # Sum durations for each production line
        if production_line not in total_duration_per_line:
            total_duration_per_line[production_line] = 0
        total_duration_per_line[production_line] += component.duration
    
    # Calculate savings for each production line
    downtime_savings = 0
    for production_line in production_lines_in_group:
        total_duration = total_duration_per_line[production_line]
        savings = production_line.downtime_cost_rate * (total_duration - group.total_downtime)
        downtime_savings += savings
    
    return downtime_savings

# https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.gamma.html to verify that sp.gamma matches the integral described in the paper
def compute_phi_raw(cc, mtbf, lambd, x):
    gamma_val = sp.gamma(1 + 1 / lambd)
    base = (gamma_val / mtbf) ** lambd
    return cc * base * (1 / lambd) * x ** lambd # Described in the equation 10 of the paper

def cost_rate(x, cp, cc, mtbf, lambd, d): # THIS FUNCTION NEEDS TO BE CHECKED
    phi = compute_phi_raw(cc, mtbf, lambd, x)
    return (cp + phi) / (x + d)

def compute_optimal_x(cp, cc, mtbf, lambd, d): # THIS FUNCTION NEEDS TO BE CHECKED
    result = minimize_scalar(
        lambda x: cost_rate(x, cp, cc, mtbf, lambd, d),
        bounds=(1, 365),  # adjust based on your expected range
        method='bounded'
    )
    return result.x, result.fun  # x* and CR(x*)

for component in components:
    cc = component.corrective_maintenance_cost # includes production line setup cost
    cp = component.preventive_maintenance_cost # includes production line setup cost and downtime cost
    mtbf = component.mean_time_between_failures
    lambd = component.lamda_efr
    d = component.preventive_maintenance_duration  # duration of PM

    x_opt, cr_opt = compute_optimal_x(cp, cc, mtbf, lambd, d)
    component.optimal_execution_time = x_opt
    component.long_term_cost_rate = cr_opt

    print(f"Component {component.id}:")
    print(f"  Optimal x*: {x_opt:.2f}")
    print(f"  Cost Rate (CR): {cr_opt:.4f}")
    print(f"  Synthetic x*: {component.optimal_execution_time:.2f}")
    print(f"  Synthetic CR: {component.long_term_cost_rate_synthetic:.4f}")
    print("  Δ x*: {:.2f}, Δ CR: {:.4f}".format(x_opt - component.optimal_execution_time_synthetic, cr_opt - component.long_term_cost_rate_synthetic))
    print()