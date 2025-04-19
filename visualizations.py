# visualization.py
import random
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from cost_functions import cost_rate, compute_optimal_x
from group_analysis import compute_group_economic_profit, find_feasible_interval

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

def plot_group_economic_profit(example_group, get_production_line_by_id, find_optimal_group_time):
    import matplotlib.pyplot as plt
    import numpy as np
    import mplcursors  # For interactive labels
    
    # Define a range of group execution times
    t_values = np.linspace(0, 365, 500)
    profits = []
    for t in t_values:
        profit, _ = compute_group_economic_profit(example_group, t, get_production_line_by_id)
        profits.append(profit)

    # Group optimal execution time
    group_time_opt, _ = find_optimal_group_time(example_group)
    profit_at_opt, details_at_opt = compute_group_economic_profit(example_group, group_time_opt, get_production_line_by_id)

    # Create a figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[3, 1], gridspec_kw={'hspace': 0.3})

    # Main plot - Economic profit vs group execution time
    main_line, = ax1.plot(t_values, profits, label="Group Economic Profit", color='darkblue', linewidth=2)
    opt_line = ax1.axvline(x=group_time_opt, color='red', linestyle='--', linewidth=1.5, 
                          label=f"Optimal Group Time: {group_time_opt:.2f}")
    opt_point = ax1.plot(group_time_opt, profit_at_opt, 'ro', markersize=8, 
                        label=f"Max Profit: {profit_at_opt:.2f}")[0]

    # Plot key points (component optimal times and some additional points)
    key_points = []
    for comp in example_group.components:
        key_points.append(comp.optimal_execution_time)

    additional_points = [
        group_time_opt - 30, 
        group_time_opt - 15,
        group_time_opt + 15, 
        group_time_opt + 30
    ]
    key_points.extend(additional_points)

    key_lines = []
    for point in key_points:
        if 0 <= point <= 365:
            profit_at_point, _ = compute_group_economic_profit(example_group, point, get_production_line_by_id)
            line = ax1.plot(point, profit_at_point, 'ko', markersize=5)[0]
            key_lines.append(line)

    # Setup profit breakdown at optimal time
    breakdown_text = (f"At optimal time ({group_time_opt:.2f}):\n"
                     f"Setup savings: {details_at_opt['setup_savings']:.2f}\n"
                     f"Downtime savings: {details_at_opt['downtime_savings']:.2f}\n"
                     f"Increased CM cost: {details_at_opt['increased_CM_cost']:.2f}")
                     
    ax1.text(0.02, 0.02, breakdown_text,
            transform=ax1.transAxes,
            bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", ec="orange", alpha=0.8),
            fontsize=9, verticalalignment='bottom')

    # Finalize main plot
    ax1.set_title("Group Economic Profit vs Execution Time (Click on points for details)", fontsize=14, fontweight='bold')
    ax1.set_xlabel("Group Execution Time (days)", fontsize=12)
    ax1.set_ylabel("Economic Profit", fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='upper right')

    # Second subplot - Component intervals visualization
    colors = plt.cm.tab10(np.linspace(0, 1, len(example_group.components)))
    component_y_positions = np.linspace(0.2, 0.8, len(example_group.components))

    for i, comp in enumerate(example_group.components):
        y_pos = component_y_positions[i]
        x_star = comp.optimal_execution_time
        interval = find_feasible_interval(comp, get_production_line_by_id)
        
        ax2.text(-10, y_pos, f"Component {int(comp.id)}", va='center', ha='right', fontsize=10)
        
        if interval:
            ax2.plot([interval[0], interval[1]], [y_pos, y_pos], '-', 
                    linewidth=6, solid_capstyle='butt', alpha=0.7, color=colors[i],
                    label=f"Component {int(comp.id)} interval")
            
            ax2.text(interval[0], y_pos-0.05, f"{interval[0]:.1f}", ha='center', va='top', fontsize=8)
            ax2.text(interval[1], y_pos-0.05, f"{interval[1]:.1f}", ha='center', va='top', fontsize=8)
        
        ax2.plot(x_star, y_pos, 'ko', markersize=8)
        ax2.text(x_star, y_pos+0.05, f"x*={x_star:.1f}", ha='center', va='bottom', fontsize=9)

    ax2.axvline(x=group_time_opt, color='red', linestyle='--', linewidth=1.5)
    ax2.text(group_time_opt, 0.1, f"Group optimal: {group_time_opt:.1f}", 
             color='red', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax2.set_xlim([0, 365])
    ax2.set_ylim([0, 1])
    ax2.set_title("Component Feasible Intervals and Optimal Times", fontsize=12)
    ax2.set_xlabel("Time (days)", fontsize=10)
    ax2.get_yaxis().set_visible(False)
    ax2.grid(True, axis='x', linestyle='--', alpha=0.5)

    # Add interactive labels using mplcursors
    cursor = mplcursors.cursor([main_line] + key_lines, hover=True)
    
    @cursor.connect("add")
    def on_add(sel):
        x, y = sel.target
        if sel.artist == main_line:
            # For points on the main line
            sel.annotation.set_text(f"t = {x:.1f}\nProfit = {y:.2f}")
        else:
            # For key points
            comp_id = None
            for comp in example_group.components:
                if abs(comp.optimal_execution_time - x) < 0.1:
                    comp_id = int(comp.id)
                    break
            
            if comp_id is not None:
                sel.annotation.set_text(f"Component {comp_id}\nt = {x:.1f}\nProfit = {y:.2f}")
            else:
                sel.annotation.set_text(f"t = {x:.1f}\nProfit = {y:.2f}")
        
        sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
        sel.annotation.set_fontsize(10)

    plt.tight_layout()
    random.seed(42)
    id = random.randint(0, 100000)
    #plt.savefig('group_maintenance_analysis.png', dpi=300, bbox_inches='tight')
    # save the figure as group_maintenance_analysis_{i}.png
    plt.savefig(f'group_maintenance_analysis_{id}.png', dpi=300, bbox_inches='tight')
    plt.show()