# visualization.py
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from solver import cost_rate, compute_optimal_x

def plot_cost_rate_function(cp, cc, mtbf, lambd, d, synthetic_x=None, synthetic_cr=None, component_id=None):
    x_vals = np.linspace(1, 365, 1000)
    y_vals = [cost_rate(x, cp, cc, mtbf, lambd, d) for x in x_vals]

    x_opt, cr_opt = compute_optimal_x(cp, cc, mtbf, lambd, d)

    plt.figure(figsize=(10, 6))
    plt.plot(x_vals, y_vals, label='Cost Rate Function', color='blue')
    plt.axvline(x_opt, color='green', linestyle='--', label=f'Optimal x*: {x_opt:.2f}')
    plt.scatter([x_opt], [cr_opt], color='green')

    if synthetic_x is not None and synthetic_cr is not None:
        plt.scatter([synthetic_x], [synthetic_cr], color='red', label='Synthetic x*', zorder=5)
        plt.axvline(synthetic_x, color='red', linestyle=':', label=f'Synthetic x*: {synthetic_x:.2f}')

    plt.title(f"Cost Rate vs. Execution Time (Component {component_id})")
    plt.xlabel("Execution Time (x)")
    plt.ylabel("Cost Rate (CR)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def visualize_optimal_execution_time_distribution(components, bins=30, show_cr_distribution=False):
    x_values = [component.optimal_execution_time for component in components]
    cr_values = [component.long_term_cost_rate for component in components]

    plt.figure(figsize=(12, 6))
    sns.histplot(x_values, bins=bins, kde=True, color='skyblue', edgecolor='black')
    plt.axvline(np.mean(x_values), color='red', linestyle='--', label=f'Mean: {np.mean(x_values):.2f}')
    plt.axvline(np.median(x_values), color='purple', linestyle=':', label=f'Median: {np.median(x_values):.2f}')
    plt.title("Distribution of Optimal Execution Times (x*)")
    plt.xlabel("Optimal Execution Time (x*)")
    plt.ylabel("Number of Components")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    if show_cr_distribution:
        plt.figure(figsize=(12, 6))
        sns.histplot(cr_values, bins=bins, kde=True, color='lightgreen', edgecolor='black')
        plt.axvline(np.mean(cr_values), color='red', linestyle='--', label=f'Mean: {np.mean(cr_values):.4f}')
        plt.axvline(np.median(cr_values), color='purple', linestyle=':', label=f'Median: {np.median(cr_values):.4f}')
        plt.title("Distribution of Long-Term Cost Rates (CR)")
        plt.xlabel("Cost Rate (CR)")
        plt.ylabel("Number of Components")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
