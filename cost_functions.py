import scipy.special as sp  # for the Gamma function
from scipy.optimize import minimize_scalar

def compute_phi_raw(cc, mtbf, lambd, x):
    gamma_val = sp.gamma(1 + 1 / lambd)
    x_safe = max(0, x) # Despite the bounds minimize_scalar() can evaluate points slightly outside the bounds due to numerical precision
    base = (gamma_val / mtbf) ** lambd
    return cc * base * (1 / lambd) * x_safe ** lambd # Described in the equation 10 of the paper

def cost_rate(x, cp, cc, mtbf, lambd, d):
    phi = compute_phi_raw(cc, mtbf, lambd, x)
    return (cp + phi) / (x + d)

def compute_optimal_x(cp, cc, mtbf, lambd, d):
    result = minimize_scalar(
        lambda x: cost_rate(x, cp, cc, mtbf, lambd, d),
        bounds=(0, 365),  # ENSURE THAT x* IS BETWEEN 0 AND 365
        method='bounded'
    )
    return result.x, result.fun  # x* and CR(x*)

def penalty_function(delta_t, component):
    x_star = component.optimal_execution_time
    cc = component.corrective_maintenance_cost
    mtbf = component.mean_time_between_failures
    lambd = component.lamda_efr
    phi_plus = compute_phi_raw(cc, mtbf, lambd, x_star + delta_t)
    phi_star = compute_phi_raw(cc, mtbf, lambd, x_star)
    return phi_plus - phi_star - delta_t * component.long_term_cost_rate