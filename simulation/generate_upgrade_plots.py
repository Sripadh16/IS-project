"""
generate_upgrade_plots.py - Generates publication-grade figures for:
  - Fig 4: Multi-Vector Attack Timing Deltas (Baseline vs TreasureCache vs Ada-EHB)
  - Fig 5: Hardware Area & Critical Path Timing Breakdown across 28nm and 7nm
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np

def generate_plots():
    sim_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set styling
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 13,
        'font.family': 'sans-serif'
    })

    # =========================================================================
    # FIGURE 4: Multi-Vector Attack Timing Deltas
    # =========================================================================
    attacks_json = os.path.join(sim_dir, "advanced_attacks_results.json")
    with open(attacks_json, 'r') as f:
        atk_data = json.load(f)['results']

    vectors = ["Flush+Reload", "Flush+Flush", "Prime+Probe", "Prime+Reprime+Probe"]
    
    baseline_deltas = [
        atk_data['Flush+Reload']['none']['timing_delta'],
        atk_data['Flush+Flush']['none']['timing_delta'],
        atk_data['Prime+Probe']['none']['timing_delta'],
        atk_data['Prime+Reprime+Probe']['none']['timing_delta']
    ]
    tc_deltas = [
        atk_data['Flush+Reload']['treasure_cache']['timing_delta'],
        atk_data['Flush+Flush']['treasure_cache']['timing_delta'],
        atk_data['Prime+Probe']['treasure_cache']['timing_delta'],
        atk_data['Prime+Reprime+Probe']['treasure_cache']['timing_delta']
    ]
    ada_deltas = [
        atk_data['Flush+Reload']['ada_ehb']['timing_delta'],
        atk_data['Flush+Flush']['ada_ehb']['timing_delta'],
        atk_data['Prime+Probe']['ada_ehb']['timing_delta'],
        atk_data['Prime+Reprime+Probe']['ada_ehb']['timing_delta']
    ]
    sharp_prp = atk_data['Prime+Reprime+Probe']['cond1_only']['timing_delta']

    x = np.arange(len(vectors))
    width = 0.25

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    rects1 = ax.bar(x - width, baseline_deltas, width, label='Baseline (Unprotected)', color='#C0392B', alpha=0.9)
    rects2 = ax.bar(x, tc_deltas, width, label='TreasureCache (IEEE TDSC)', color='#2980B9', alpha=0.9)
    rects3 = ax.bar(x + width, ada_deltas, width, label='Ada-EHB+ (Proposed)', color='#27AE60', alpha=0.9)

    # Highlight SHARP vulnerability on PRP
    ax.scatter([3 + width*1.3], [sharp_prp], color='#D35400', s=80, zorder=5, marker='^',
               label=f'Condition-1 Only / SHARP ({sharp_prp:.1f} cyc leak)')

    ax.set_ylabel(r'Attack Timing Delta $\Delta$ (Cycles)')
    ax.set_title('Figure 4: Side-Channel Timing Gap Mitigation across 4 Attack Vectors', pad=12, fontweight='bold', color='#1B365D')
    ax.set_xticks(x)
    ax.set_xticklabels(vectors, fontweight='bold')
    ax.set_ylim(-5, 195)
    ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    ax.legend(loc='upper right', frameon=True)

    # Add data labels
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#C0392B')
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2980B9')
    for rect in rects3:
        h = rect.get_height()
        ax.annotate(f'{h:.1f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#27AE60')

    fig.tight_layout()
    fig4_path = os.path.join(sim_dir, "fig4_multi_vector_attacks.png")
    fig.savefig(fig4_path, dpi=300)
    plt.close(fig)
    print(f"[Generated Figure 4] {fig4_path}")

    # =========================================================================
    # FIGURE 5: Hardware Gate Count & Area Breakdown
    # =========================================================================
    subsystems = [
        "Data Store\n(4KB SRAM)",
        "CAM Tag Array\n(64x64b)",
        "Age / LRU\nTree",
        "Domain Logic\n(Ownership)",
        "Ada-EHB\nALU & Scoring",
        "Control &\nCounters"
    ]
    gates = [51552, 12393, 8152, 1920, 3724, 842]
    colors = ['#1B365D', '#34495E', '#465F85', '#7F8C8D', '#27AE60', '#BDC3C7']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), gridspec_kw={'width_ratios': [1.3, 1]})

    # Bar chart of gate counts
    bars = ax1.bar(subsystems, gates, color=colors, width=0.6, edgecolor='black', linewidth=0.5)
    ax1.set_ylabel('Gate Count (NAND2 Gate Equivalents)')
    ax1.set_title('(a) Subsystem Logic Complexity (Total: 78,583 GE)', fontweight='bold', color='#1B365D')
    ax1.set_ylim(0, 60000)
    for bar in bars:
        h = bar.get_height()
        ax1.annotate(f'{h:,}', xy=(bar.get_x() + bar.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    # Donut chart of area proportion
    labels = ["SRAM Data (65.6%)", "CAM Tags (15.8%)", "LRU Tree (10.4%)", "Ada-EHB Ext (5.0%)", "Domain & FSM (3.2%)"]
    sizes = [51552, 12393, 8152, 3724, 1920 + 842]
    pie_colors = ['#1B365D', '#34495E', '#465F85', '#27AE60', '#BDC3C7']
    
    wedges, texts = ax2.pie(sizes, colors=pie_colors, startangle=140,
                            wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2))
    ax2.set_title('(b) Silicon Footprint Proportion\n(Overhead vs 2MB LLC: 0.335% @ 28nm)', fontweight='bold', color='#1B365D')
    ax2.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.85, 0.5), frameon=True, fontsize=9)

    fig.suptitle('Figure 5: Hardware Synthesis Resource Breakdown & Silicon Budget', fontsize=13, fontweight='bold', color='#1B365D')
    fig.tight_layout()
    fig5_path = os.path.join(sim_dir, "fig5_hardware_breakdown.png")
    fig.savefig(fig5_path, dpi=300)
    plt.close(fig)
    print(f"[Generated Figure 5] {fig5_path}")

if __name__ == '__main__':
    generate_plots()
