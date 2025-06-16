# visualization.py
import random
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from cost_functions import cost_rate, compute_optimal_x, penalty_function
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

def plot_feasible_interval_penalty(component, get_production_line_by_id):
    """
    Visualizes how maintenance outside the feasible interval is not cost effective.
    Shows the penalty cost for deviating from optimal time and the setup cost threshold.
    """
    x_star = component.optimal_execution_time
    production_line = get_production_line_by_id(component.production_line_id)
    setup_cost = production_line.preventive_maintenance_set_up_cost
    
    # Calculate feasible interval
    interval = find_feasible_interval(component, get_production_line_by_id)
    if interval is None:
        print(f"Component {component.id} has no feasible interval for grouping")
        return
    
    interval_min, interval_max = interval
    
    # Create a range of delta values around the optimal point
    x_vals = np.linspace(max(0, x_star - 100), min(365, x_star + 100), 500)
    delta_vals = [x - x_star for x in x_vals]
    
    # Calculate penalty for each deviation
    penalty_vals = [penalty_function(delta, component) for delta in delta_vals]
    
    # Plot
    plt.figure(figsize=(12, 8))
    
    # Main plot - penalty function
    plt.plot(x_vals, penalty_vals, 'b-', linewidth=2.5, label='Penalty Cost')
    plt.axhline(y=setup_cost, color='red', linestyle='--', linewidth=2, 
               label=f'Setup Cost Threshold ({setup_cost:.2f})')
    
    # Mark the optimal time
    plt.axvline(x=x_star, color='green', linestyle='-', linewidth=2,
               label=f'Optimal Time x* ({x_star:.2f})')
    
    # Mark the feasible interval
    plt.axvspan(interval_min, interval_max, alpha=0.2, color='green', 
               label=f'Feasible Interval [{interval_min:.2f}, {interval_max:.2f}]')
    
    # Add points where penalty equals setup cost
    plt.plot([interval_min, interval_max], [setup_cost, setup_cost], 'ro', markersize=8)
    
    # Add a region showing unprofitable maintenance times
    plt.fill_between(x_vals, penalty_vals, setup_cost, 
                    where=(np.array(penalty_vals) > setup_cost),
                    color='red', alpha=0.3, interpolate=True,
                    label='Unprofitable Region (Penalty > Setup Cost)')
    
    # Annotations
    plt.annotate(f"Δt⁻ = {interval_min - x_star:.2f}", 
                xy=(interval_min, setup_cost), 
                xytext=(interval_min - 20, setup_cost + 10),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5),
                fontsize=10)
    
    plt.annotate(f"Δt⁺ = {interval_max - x_star:.2f}", 
                xy=(interval_max, setup_cost), 
                xytext=(interval_max + 20, setup_cost + 10),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5),
                fontsize=10)
    
    # Add title and labels
    plt.title(f"Penalty Cost vs. Maintenance Time - Component {component.id}", fontsize=14, fontweight='bold')
    plt.xlabel("Maintenance Time (days)", fontsize=12)
    plt.ylabel("Penalty Cost", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add explanatory text
    explanation = (
        f"• Optimal time (x*): {x_star:.2f} days\n"
        f"• Feasible interval: [{interval_min:.2f}, {interval_max:.2f}] days\n"
        f"• Setup cost: {setup_cost:.2f}\n"
        f"• Outside the feasible interval, the penalty cost exceeds the setup cost savings\n"
        f"• Maintenance is only economically beneficial within the green region"
    )
    
    plt.figtext(0.15, 0.02, explanation, fontsize=10, 
               bbox=dict(facecolor='lightyellow', alpha=0.8, boxstyle='round,pad=0.5'))
    
    plt.legend(loc='upper right', fontsize=10)
    plt.tight_layout(rect=[0, 0.08, 1, 0.98])  # Adjust layout to make room for text
    
    random.seed(42)
    id = random.randint(0, 100000)
    plt.savefig(f'feasible_interval_verification_{id}.png', dpi=300, bbox_inches='tight')
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

def plot_component_planning_horizon(components, get_production_line_by_id, planning_horizon=365):
    """
    Plots a timeline visualization showing each component's planning horizon,
    optimal execution time, and feasible interval for grouping decisions.
    
    Args:
        components: List of Component objects
        get_production_line_by_id: Function to get production line by ID
        planning_horizon: Total planning horizon in days (default 365)
    """
    plt.figure(figsize=(14, max(8, len(components) * 0.5)))
    
    # Sort components by optimal execution time for better visualization
    sorted_components = sorted(components, key=lambda c: c.optimal_execution_time)
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(sorted_components)))
    
    for i, component in enumerate(sorted_components):
        y_position = i
        
        # Plot the planning horizon as a background line
        plt.plot([0, planning_horizon], [y_position, y_position], 
                 color='lightgray', linewidth=2, alpha=0.5)
        
        # Get feasible interval
        interval = find_feasible_interval(component, get_production_line_by_id)
        
        # Plot feasible interval as a thick colored line
        if interval:
            plt.plot([interval[0], interval[1]], [y_position, y_position], 
                     color=colors[i], linewidth=6, alpha=0.7, solid_capstyle='round',
                     label=f'Component {int(component.id)} feasible interval')
            
            # Add interval bounds text
            plt.text(interval[0], y_position - 0.2, f'{interval[0]:.1f}', 
                     ha='center', va='top', fontsize=8, color=colors[i])
            plt.text(interval[1], y_position - 0.2, f'{interval[1]:.1f}', 
                     ha='center', va='top', fontsize=8, color=colors[i])
        
        # Plot optimal execution time as a black diamond
        plt.plot(component.optimal_execution_time, y_position, 'kD', 
                 markersize=8, markerfacecolor='black', markeredgecolor='white', 
                 markeredgewidth=1, zorder=5)
        
        # Add component ID and optimal time text
        plt.text(-15, y_position, f'C{int(component.id)}', 
                 ha='right', va='center', fontsize=10, fontweight='bold')
        plt.text(component.optimal_execution_time, y_position + 0.25, 
                 f'{component.optimal_execution_time:.1f}', 
                 ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # Add cost rate information
        plt.text(planning_horizon + 5, y_position, 
                 f'CR: {component.long_term_cost_rate:.3f}', 
                 ha='left', va='center', fontsize=8, color='gray')
    
    # Formatting
    plt.xlim(-30, planning_horizon + 50)
    plt.ylim(-0.5, len(sorted_components) - 0.5)
    plt.xlabel('Time (days)', fontsize=12)
    plt.ylabel('Components', fontsize=12)
    plt.title('Component Planning Horizon: Optimal Execution Times and Feasible Intervals', 
              fontsize=14, fontweight='bold')
    
    # Add grid for better readability
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)
    
    # Remove y-axis ticks since we have component labels
    plt.yticks([])
    
    # Add legend explaining the symbols
    legend_elements = [
        plt.Line2D([0], [0], color='lightgray', linewidth=2, alpha=0.5, label='Planning Horizon'),
        plt.Line2D([0], [0], color='blue', linewidth=6, alpha=0.7, label='Feasible Interval'),
        plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='black', 
                   markersize=8, label='Optimal Execution Time', linestyle='None')
    ]
    plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))
    
    # Add explanatory text
    explanation = (
        "This visualization shows:\n"
        "• Gray lines: Full planning horizon for each component\n"
        "• Colored thick lines: Feasible intervals for grouping\n"
        "• Black diamonds: Individual optimal execution times\n"
        "• CR: Long-term cost rate for each component"
    )
    
    plt.figtext(0.02, 0.02, explanation, fontsize=9, 
               bbox=dict(facecolor='lightyellow', alpha=0.8, boxstyle='round,pad=0.5'))
    
    plt.tight_layout(rect=[0, 0.08, 1, 0.98])
    
    # Save the figure
    random.seed(42)
    file_id = random.randint(0, 100000)
    plt.savefig(f'component_planning_horizon_{file_id}.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_cascading_effects_comparison(groups_by_line):
    """
    Visualizes the before/after comparison of group execution times for each production line.
    Shows planned execution times vs effective execution times after cascading delays as timeline.
    
    Args:
        groups_by_line: Dictionary with line_id as key and list of groups as value
    """
    num_lines = len(groups_by_line)
    if num_lines == 0:
        print("No groups to visualize")
        return
        
    fig, axes = plt.subplots(num_lines * 2, 1, figsize=(16, 3 * num_lines * 2))
    if num_lines == 1:
        axes = [axes] if len(axes.shape) == 1 else axes.flatten()
    else:
        axes = axes.flatten()
    
    colors = ['#2E86C1', '#E74C3C']  # Blue for planned, Red for effective
    
    for idx, (line_id, line_groups) in enumerate(groups_by_line.items()):
        # Filter groups with multiple components
        multi_component_groups = [g for g in line_groups if len(g.components) > 1]
        
        if not multi_component_groups:
            for i in range(2):
                ax = axes[idx * 2 + i]
                ax.text(0.5, 0.5, f'Production Line {int(line_id)}\nNo multi-component groups', 
                       ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.set_xlim(0, 365)
                ax.set_ylim(-0.5, 0.5)
            continue
            
        # Sort groups by planned execution time
        sorted_groups = sorted(multi_component_groups, key=lambda g: g.planned_execution_time)
        
        planned_times = [g.planned_execution_time for g in sorted_groups]
        effective_times = [getattr(g, 'effective_execution_time', g.planned_execution_time) for g in sorted_groups]
        
        # Create timeline plots
        for timeline_idx, (times, title_suffix, color) in enumerate([
            (planned_times, "Original Planning", colors[0]),
            (effective_times, "After Cascading Effects", colors[1])
        ]):
            ax = axes[idx * 2 + timeline_idx]
            
            # Plot timeline as horizontal line
            max_time = max(max(planned_times), max(effective_times))
            ax.plot([0, max_time], [0, 0], 'k-', linewidth=2, alpha=0.3)
            
            # Plot groups as points on timeline
            for i, (group, time) in enumerate(zip(sorted_groups, times)):
                # Main group point
                ax.plot(time, 0, 'o', color=color, markersize=12, alpha=0.8)
                
                # Group label
                components_str = ','.join([str(int(c.id)) for c in group.components])
                downtime = group.get_group_downtime()
                label = f'G{group.id}\n[{components_str}]\nDT:{downtime:.1f}d'
                
                # Alternate label positions above/below
                y_offset = 0.15 if i % 2 == 0 else -0.15
                ax.text(time, y_offset, label, ha='center', va='center' if i % 2 == 0 else 'top', 
                       fontsize=8, bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
                
                # Time annotation
                ax.text(time, -0.08 if i % 2 == 0 else 0.08, f'{time:.1f}d', 
                       ha='center', va='top' if i % 2 == 0 else 'bottom', 
                       fontsize=9, fontweight='bold', color=color)
            
            # Calculate and show gaps between consecutive groups
            if len(times) > 1:
                for i in range(len(times) - 1):
                    gap = times[i + 1] - times[i]
                    mid_point = (times[i] + times[i + 1]) / 2
                    ax.annotate('', xy=(times[i + 1], -0.05), xytext=(times[i], -0.05),
                               arrowprops=dict(arrowstyle='<->', color='gray', lw=1))
                    ax.text(mid_point, -0.05, f'{gap:.1f}d', ha='center', va='top', 
                           fontsize=8, color='gray', style='italic')
            
            ax.set_xlim(-10, max_time + 10)
            ax.set_ylim(-0.4, 0.4)
            ax.set_xlabel('Time (days)', fontsize=11)
            ax.set_title(f'Production Line {int(line_id)} - {title_suffix}', 
                        fontsize=12, fontweight='bold')
            ax.grid(True, axis='x', alpha=0.3)
            ax.set_yticks([])
            
            # Add timeline markers
            for i in range(0, int(max_time) + 50, 50):
                if i <= max_time:
                    ax.axvline(x=i, color='lightgray', linestyle=':', alpha=0.5)
                    ax.text(i, 0.35, f'{i}d', ha='center', va='bottom', fontsize=8, color='gray')
        
        # Add comparison summary between the two timelines
        if len(sorted_groups) > 1:
            total_delay = sum(effective_times) - sum(planned_times)
            original_span = max(planned_times) - min(planned_times)
            new_span = max(effective_times) - min(effective_times)
            span_change = new_span - original_span
            
            summary_text = (f'Total delay: {total_delay:.1f}d | '
                           f'Original span: {original_span:.1f}d | '
                           f'New span: {new_span:.1f}d | '
                           f'Span change: {span_change:+.1f}d')
            
            # Place summary between the two timelines
            fig.text(0.5, (2 * idx + 1.5) / (num_lines * 2), summary_text,
                    ha='center', va='center', fontsize=10, 
                    bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow', alpha=0.9))
    
    plt.tight_layout()
    
    # Save the figure
    random.seed(42)
    #file_id = random.randint(0, 100000)
    plt.savefig(f'visualizations/cascading_effects_timeline.png', dpi=300, bbox_inches='tight')
    plt.show()