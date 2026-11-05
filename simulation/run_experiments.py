"""
run_experiments.py - Benchmark Execution & Result Generation
Runs multi-core cache side-channel simulations, prints summary statistics,
and generates publication-quality figures for documentation and presentation.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
from attacks import run_prime_and_probe_simulation, run_evict_and_time_simulation
from cache_model import MultiCoreCacheSystem


def setup_plot_style():
    """Sets a clean, professional academic aesthetic for plots."""
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 14,
        'font.family': 'sans-serif'
    })


def run_all_benchmarks():
    print("=" * 70)
    print("Starting TreasureCache & Side-Channel Defense Simulation Benchmarks")
    print("=" * 70)
    
    modes = ['none', 'partitioned', 'treasure_cache', 'ada_ehb']
    mode_labels = {
        'none': 'Unprotected (LRU)',
        'partitioned': 'Static Partitioning',
        'treasure_cache': 'TreasureCache (Standard)',
        'ada_ehb': 'Ada-EHB (Proposed Improvement)'
    }
    
    # 1. Prime + Probe Attack Evaluation (Normal Scenario)
    print("\n[1/3] Running Prime+Probe Simulations (Normal Scenario)...")
    pp_results = {}
    for m in modes:
        res = run_prime_and_probe_simulation(mode=m, rounds=300, thrash_noise=False)
        pp_results[m] = res
        print(f"  -> Mode: {mode_labels[m]:<32} | Attacker Accuracy: {res['accuracy']*100:.1f}%")

    # Prime + Probe Attack Evaluation (Adversarial Thrashing Scenario)
    print("\n[1b/3] Running Prime+Probe Under Adversarial Thrashing Scenario...")
    pp_thrash_results = {}
    for m in ['treasure_cache', 'ada_ehb']:
        res = run_prime_and_probe_simulation(mode=m, rounds=300, thrash_noise=True)
        pp_thrash_results[m] = res
        print(f"  -> Mode: {mode_labels[m]:<32} (Thrashed) | Attacker Accuracy: {res['accuracy']*100:.1f}%")

    # 2. Evict + Time Attack Evaluation
    print("\n[2/3] Running Evict+Time Simulations...")
    et_results = {}
    for m in modes:
        res = run_evict_and_time_simulation(mode=m, rounds=200)
        et_results[m] = res
        print(f"  -> Mode: {mode_labels[m]:<32} | Timing Gap: {res['timing_gap']:.1f} cycles")

    # 3. Buffer Capacity Scaling Study (16, 32, 64, 128, 256 lines)
    print("\n[3/3] Evaluating EHB Capacity Scaling (Buffer Hit Ratio & Footprint)...")
    capacities = [16, 32, 64, 128, 256]
    tc_hit_ratios = []
    ada_hit_ratios = []
    
    for cap in capacities:
        # Standard TC
        cache_tc = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=cap)
        for i in range(200):
            cache_tc.read_address(core_id=0, addr=0x100000 + (i % 32) * 64, domain_id=0, is_sensitive=True)
            # interleave attacker accesses causing evictions
            cache_tc.read_address(core_id=1, addr=0x400000 + (i % 64) * 64, domain_id=1)
        tc_hr = cache_tc.ehb.hits / max(1, cache_tc.ehb.hits + cache_tc.ehb.misses)
        tc_hit_ratios.append(tc_hr * 100)
        
        # Ada-EHB
        cache_ada = MultiCoreCacheSystem(mode='ada_ehb', ehb_capacity=cap)
        for i in range(200):
            cache_ada.read_address(core_id=0, addr=0x100000 + (i % 32) * 64, domain_id=0, is_sensitive=True)
            cache_ada.read_address(core_id=1, addr=0x400000 + (i % 64) * 64, domain_id=1)
        ada_hr = cache_ada.ehb.hits / max(1, cache_ada.ehb.hits + cache_ada.ehb.misses)
        ada_hit_ratios.append(ada_hr * 100)

    # -------------------------------------------------------------
    # Generate Figures
    # -------------------------------------------------------------
    setup_plot_style()
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # FIGURE 1: Access Latency Distribution (Closing the Timing Gap)
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    
    # Left subplot: Unprotected
    unprotected_evicted = et_results['none']['evicted_samples']
    unprotected_cached = et_results['none']['cached_samples']
    ax1.hist(unprotected_cached, bins=15, alpha=0.7, label='Cached Access (LLC Hit ~38 cyc)', color='#2b5c8f')
    ax1.hist(unprotected_evicted, bins=15, alpha=0.7, label='Evicted Access (DRAM Miss ~200 cyc)', color='#c0392b')
    ax1.set_title('Unprotected Cache: Wide Timing Gap\n(Exploitable by Evict+Time / Prime+Probe)', fontweight='bold')
    ax1.set_xlabel('Access Latency (CPU Cycles)')
    ax1.set_ylabel('Sample Count')
    ax1.legend(loc='upper right', frameon=True)
    ax1.set_xlim(20, 240)
    
    # Right subplot: TreasureCache
    tc_evicted = et_results['treasure_cache']['evicted_samples']
    tc_cached = et_results['treasure_cache']['cached_samples']
    ax2.hist(tc_cached, bins=15, alpha=0.7, label='Cached Access (LLC Hit ~38 cyc)', color='#2b5c8f')
    ax2.hist(tc_evicted, bins=15, alpha=0.7, label='Evicted Access (EHB Hit ~40 cyc)', color='#27ae60')
    ax2.set_title('TreasureCache: Timing Gap Closed\n(Evicted Blocks Buffered in EHB)', fontweight='bold')
    ax2.set_xlabel('Access Latency (CPU Cycles)')
    ax2.legend(loc='upper right', frameon=True)
    ax2.set_xlim(20, 240)
    
    plt.tight_layout()
    fig1_path = os.path.join(output_dir, 'fig1_latency_distribution.png')
    plt.savefig(fig1_path, dpi=300)
    plt.close(fig1)
    print(f"\n[Generated] {fig1_path}")

    # FIGURE 2: Attacker Side-Channel Success Rate
    fig2, ax = plt.subplots(figsize=(9, 5))
    categories = ['Unprotected\n(Baseline)', 'Static\nPartitioning', 'TreasureCache\n(Clean)', 'TreasureCache\n(Thrashed)', 'Proposed Ada-EHB\n(Thrashed)']
    accuracies = [
        pp_results['none']['accuracy'] * 100,
        pp_results['partitioned']['accuracy'] * 100,
        pp_results['treasure_cache']['accuracy'] * 100,
        pp_thrash_results['treasure_cache']['accuracy'] * 100,
        pp_thrash_results['ada_ehb']['accuracy'] * 100
    ]
    colors = ['#c0392b', '#7f8c8d', '#27ae60', '#e67e22', '#2980b9']
    
    bars = ax.bar(categories, accuracies, color=colors, width=0.55, edgecolor='black', linewidth=0.8)
    ax.axhline(y=6.25, color='gray', linestyle='--', linewidth=1.2, label='Theoretical Random Guess Baseline (1/16 = 6.25%)')
    
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1.5, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold', fontsize=10)
        
    ax.set_ylim(0, 105)
    ax.set_ylabel('Attacker Secret Identification Accuracy (%)', fontweight='bold')
    ax.set_title('Side-Channel Attack Success Rate Across Defense Architectures\n(Prime+Probe on Cryptographic Table Lookups)', fontweight='bold')
    ax.legend(loc='upper right', frameon=True)
    
    plt.tight_layout()
    fig2_path = os.path.join(output_dir, 'fig2_attack_success_rate.png')
    plt.savefig(fig2_path, dpi=300)
    plt.close(fig2)
    print(f"[Generated] {fig2_path}")

    # FIGURE 3: Buffer Capacity vs Hit Ratio & Security Stability
    fig3, ax = plt.subplots(figsize=(8, 4.8))
    x_indices = np.arange(len(capacities))
    width = 0.35
    
    ax.bar(x_indices - width/2, tc_hit_ratios, width, label='Standard TreasureCache EHB', color='#27ae60', edgecolor='black')
    ax.bar(x_indices + width/2, ada_hit_ratios, width, label='Proposed Ada-EHB (Sensitivity-Aware)', color='#2980b9', edgecolor='black')
    
    ax.set_xlabel('Buffer Capacity (Cache Lines)', fontweight='bold')
    ax.set_ylabel('Eviction Buffer Hit Ratio (%)', fontweight='bold')
    ax.set_title('Eviction-Hidden Buffer Hit Ratio vs Capacity Scaling', fontweight='bold')
    ax.set_xticks(x_indices)
    ax.set_xticklabels([f"{c} lines\n({(c*64)/1024:.1f} KB)" for c in capacities])
    ax.set_ylim(0, 100)
    ax.legend(loc='lower right', frameon=True)
    
    for i in range(len(capacities)):
        ax.text(x_indices[i] - width/2, tc_hit_ratios[i] + 1.5, f"{tc_hit_ratios[i]:.1f}%", ha='center', fontsize=9)
        ax.text(x_indices[i] + width/2, ada_hit_ratios[i] + 1.5, f"{ada_hit_ratios[i]:.1f}%", ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    fig3_path = os.path.join(output_dir, 'fig3_performance_tradeoff.png')
    plt.savefig(fig3_path, dpi=300)
    plt.close(fig3)
    print(f"[Generated] {fig3_path}")

    # Save summary json
    summary_data = {
        "prime_and_probe": {
            "unprotected_accuracy": pp_results['none']['accuracy'],
            "partitioned_accuracy": pp_results['partitioned']['accuracy'],
            "treasure_cache_clean_accuracy": pp_results['treasure_cache']['accuracy'],
            "treasure_cache_thrashed_accuracy": pp_thrash_results['treasure_cache']['accuracy'],
            "ada_ehb_thrashed_accuracy": pp_thrash_results['ada_ehb']['accuracy'],
            "random_guess_baseline": 0.0625
        },
        "evict_and_time": {
            "unprotected_gap_cycles": et_results['none']['timing_gap'],
            "partitioned_gap_cycles": et_results['partitioned']['timing_gap'],
            "treasure_cache_gap_cycles": et_results['treasure_cache']['timing_gap'],
            "ada_ehb_gap_cycles": et_results['ada_ehb']['timing_gap']
        },
        "capacity_study": {
            "capacities": capacities,
            "tc_hit_ratios": tc_hit_ratios,
            "ada_hit_ratios": ada_hit_ratios
        }
    }
    
    json_path = os.path.join(output_dir, 'simulation_results.json')
    with open(json_path, 'w') as f:
        json.dump(summary_data, f, indent=4)
    print(f"[Generated] {json_path}")
    print("\nAll simulation benchmarks completed successfully!\n")


if __name__ == '__main__':
    run_all_benchmarks()

