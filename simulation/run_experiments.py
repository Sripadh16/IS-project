"""
run_experiments.py - Multi-Trial Benchmark Execution & Publication Graph Generation
Runs reproducible, multi-trial experiments across 5 independent random seeds (101, 202, 303, 404, 505):
  1. Domain-Isolated Contention Study (evaluating TreasureCache domain ownership protection)
  2. Shared-Memory Contention Study (evaluating Ada-EHB retention scoring under shared churn)
  3. Matched Evict+Time Timing Gap Study (evaluating timing channel closure)
Generates structured simulation_results.json and publication-quality figures from real simulator output.
"""

import json
import os
import statistics
import matplotlib.pyplot as plt
from typing import Dict, List
from attacks import run_residency_trial, run_shared_contention_trial, run_evict_and_time_simulation

SEEDS = [101, 202, 303, 404, 505]
MODES = ['none', 'treasure_cache', 'ada_ehb']
CAPACITIES = [8, 16, 32, 64]
CHURN_LEVELS = [0, 32, 128]


def summarize(values: List[float]) -> Dict:
    """Computes mean, standard deviation, and per-seed values."""
    mean_val = statistics.mean(values)
    std_val = statistics.stdev(values) if len(values) > 1 else 0.0
    return {
        'mean': round(mean_val, 3),
        'std_across_seeds': round(std_val, 3),
        'per_seed': [round(x, 3) for x in values]
    }


def setup_plot_style():
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


def main():
    print("=" * 75)
    print("Executing TreasureCache & Ada-EHB Multi-Trial Benchmarks (5 Random Seeds)")
    print("=" * 75)
    
    results = {
        'model_description': 'Sequential synthetic cache-event simulator (educational model; not full-system gem5).',
        'seeds': SEEDS,
        'scope_and_limitations': (
            'Demonstrates microarchitectural event flow, dual-condition placement, domain ownership isolation, '
            'and retention scoring under controlled workloads. Does not claim full-system gem5 cycle-accuracy or key recovery.'
        ),
        'residency_isolated': {},
        'residency_shared': {},
        'timing_evict_and_time': {}
    }

    # -------------------------------------------------------------
    # 1. Domain-Isolated Contention Study
    # -------------------------------------------------------------
    print("\n[1/3] Running Domain-Isolated Contention Experiments...")
    for mode in MODES:
        for cap in CAPACITIES:
            for churn in CHURN_LEVELS:
                samples = [run_residency_trial(mode=mode, capacity=cap, churn=churn, seed=s) for s in SEEDS]
                key = f"{mode}_cap{cap}_churn{churn}"
                results['residency_isolated'][key] = {
                    'buffered_before_churn': summarize([s['initial_buffered'] for s in samples]),
                    'buffered_after_churn': summarize([s['retained'] for s in samples]),
                    'ehb_hits': summarize([s['ehb_hits'] for s in samples]),
                    'dram_misses': summarize([s['dram_misses'] for s in samples]),
                    'mean_victim_latency': summarize([s['mean_latency'] for s in samples]),
                    'bypasses': summarize([s['bypasses'] for s in samples])
                }
                print(f"  -> {key:<28}: Retained = {results['residency_isolated'][key]['buffered_after_churn']['mean']:.2f} / 8 lines | Latency = {results['residency_isolated'][key]['mean_victim_latency']['mean']:.1f} cyc")

    # -------------------------------------------------------------
    # 2. Shared-Memory Contention Study
    # -------------------------------------------------------------
    print("\n[2/3] Running Shared-Memory Contention Experiments (Joint Ownership {0, 1})...")
    for mode in ['treasure_cache', 'ada_ehb']:
        for cap in CAPACITIES:
            for churn in [16, 48]:
                samples = [run_shared_contention_trial(mode=mode, capacity=cap, shared_churn=churn, seed=s) for s in SEEDS]
                key = f"{mode}_cap{cap}_sharedchurn{churn}"
                results['residency_shared'][key] = {
                    'buffered_before_churn': summarize([s['initial_buffered'] for s in samples]),
                    'buffered_after_churn': summarize([s['retained'] for s in samples]),
                    'ehb_hits': summarize([s['ehb_hits'] for s in samples]),
                    'dram_misses': summarize([s['dram_misses'] for s in samples]),
                    'mean_victim_latency': summarize([s['mean_latency'] for s in samples]),
                    'bypasses': summarize([s['bypasses'] for s in samples])
                }
                print(f"  -> {key:<32}: Retained = {results['residency_shared'][key]['buffered_after_churn']['mean']:.2f} / 8 lines | Latency = {results['residency_shared'][key]['mean_victim_latency']['mean']:.1f} cyc")

    # -------------------------------------------------------------
    # 3. Matched Evict+Time Experiments
    # -------------------------------------------------------------
    print("\n[3/3] Running Matched Evict+Time Timing Gap Experiments...")
    for mode in MODES:
        for churn in [0, 64]:
            runs = [run_evict_and_time_simulation(mode=mode, rounds=40, seed=s, thrash_intensity=churn) for s in SEEDS]
            key = f"{mode}_churn{churn}"
            results['timing_evict_and_time'][key] = {
                'timing_gap': summarize([x['timing_gap'] for x in runs]),
                'mean_evicted': summarize([x['mean_evicted'] for x in runs]),
                'mean_cached': summarize([x['mean_cached'] for x in runs]),
                'ehb_hit_fraction': summarize([x['ehb_hit_fraction'] for x in runs]),
                'levels_seed_101': runs[0]['levels']
            }
            print(f"  -> {key:<24}: Timing Gap = {results['timing_evict_and_time'][key]['timing_gap']['mean']:6.2f} +/- {results['timing_evict_and_time'][key]['timing_gap']['std_across_seeds']:4.2f} cycles")

    # Save JSON results
    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, 'simulation_results.json')
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n[Generated JSON] {json_path}")

    # -------------------------------------------------------------
    # 4. Generate Publication-Quality Figures from Actual Simulator Output
    # -------------------------------------------------------------
    setup_plot_style()

    # FIGURE 1: Victim Buffer Residency across Capacities (Domain-Isolated Churn)
    fig1, ax1 = plt.subplots(figsize=(8, 4.8))
    for mode, color, marker, label in [
        ('treasure_cache', '#e67e22', 'o', 'TreasureCache (Ownership / LRU)'),
        ('ada_ehb', '#2980b9', 's', 'Ada-EHB (Retention Scoring)')
    ]:
        xs = CAPACITIES
        ys = [results['residency_isolated'][f"{mode}_cap{c}_churn128"]['buffered_after_churn']['mean'] for c in xs]
        yerrs = [results['residency_isolated'][f"{mode}_cap{c}_churn128"]['buffered_after_churn']['std_across_seeds'] for c in xs]
        ax1.errorbar(xs, ys, yerr=yerrs, marker=marker, color=color, linewidth=2, markersize=7, capsize=4, label=label)

    ax1.axhline(y=8, color='gray', linestyle='--', linewidth=1.2, label='Total Victim Working Set (8 lines)')
    ax1.set_xlabel('EHB Buffer Capacity (Lines)', fontweight='bold')
    ax1.set_ylabel('Victim Lines Retained in Buffer', fontweight='bold')
    ax1.set_title('Victim Buffer Residency Under Domain-Isolated Churn (128 Churn Lines, 5 Seeds)\n(Demonstrates TreasureCache Ownership Quota Isolation)', fontweight='bold')
    ax1.set_xticks(CAPACITIES)
    ax1.set_ylim(-0.5, 9.5)
    ax1.legend(loc='lower right', frameon=True)
    plt.tight_layout()
    fig1_path = os.path.join(output_dir, 'fig1_residency.png')
    plt.savefig(fig1_path, dpi=200, bbox_inches='tight')
    plt.close(fig1)
    print(f"[Generated Figure 1] {fig1_path}")

    # FIGURE 2: Mean Victim Access Latency across Capacities
    fig2, ax2 = plt.subplots(figsize=(8, 4.8))
    # Unprotected baseline line
    unprot_latency = results['residency_isolated']['none_cap64_churn128']['mean_victim_latency']['mean']
    ax2.axhline(y=unprot_latency, color='#c0392b', linestyle='--', linewidth=2, label=f'Unprotected Baseline (~{unprot_latency:.0f} cyc, DRAM Misses)')

    for mode, color, marker, label in [
        ('treasure_cache', '#e67e22', 'o', 'TreasureCache (Protected ~40 cyc)'),
        ('ada_ehb', '#2980b9', 's', 'Ada-EHB (Protected ~40 cyc)')
    ]:
        xs = CAPACITIES
        ys = [results['residency_isolated'][f"{mode}_cap{c}_churn128"]['mean_victim_latency']['mean'] for c in xs]
        yerrs = [results['residency_isolated'][f"{mode}_cap{c}_churn128"]['mean_victim_latency']['std_across_seeds'] for c in xs]
        ax2.errorbar(xs, ys, yerr=yerrs, marker=marker, color=color, linewidth=2, markersize=7, capsize=4, label=label)

    ax2.set_xlabel('EHB Buffer Capacity (Lines)', fontweight='bold')
    ax2.set_ylabel('Mean Victim Access Latency (Cycles)', fontweight='bold')
    ax2.set_title('Victim Access Latency After LLC Eviction (128 Churn Lines, 5 Seeds)\n(Closing the Timing Gap from 200 cycles to ~40 cycles)', fontweight='bold')
    ax2.set_xticks(CAPACITIES)
    ax2.set_ylim(20, 220)
    ax2.legend(loc='upper right', frameon=True)
    plt.tight_layout()
    fig2_path = os.path.join(output_dir, 'fig2_victim_latency.png')
    plt.savefig(fig2_path, dpi=200, bbox_inches='tight')
    plt.close(fig2)
    print(f"[Generated Figure 2] {fig2_path}")

    # FIGURE 3: Shared-Memory Contention Study (Where Ada-EHB Differentiates)
    fig3, ax3 = plt.subplots(figsize=(8, 4.8))
    xs = CAPACITIES
    ys_tc = [results['residency_shared'][f"treasure_cache_cap{c}_sharedchurn48"]['buffered_after_churn']['mean'] for c in xs]
    ys_ada = [results['residency_shared'][f"ada_ehb_cap{c}_sharedchurn48"]['buffered_after_churn']['mean'] for c in xs]
    
    width = 2.0
    ax3.bar([x - width/2 for x in xs], ys_tc, width=width, label='Standard TreasureCache (Unweighted LRU)', color='#e67e22', edgecolor='black')
    ax3.bar([x + width/2 for x in xs], ys_ada, width=width, label='Proposed Ada-EHB (Retention Scoring & Rate-Limiting)', color='#2980b9', edgecolor='black')
    
    ax3.axhline(y=8, color='gray', linestyle='--', linewidth=1.2, label='Total Victim Working Set (8 lines)')
    ax3.set_xlabel('EHB Buffer Capacity (Lines)', fontweight='bold')
    ax3.set_ylabel('Victim Lines Retained in Buffer', fontweight='bold')
    ax3.set_title('Shared-Memory Contention Study (Joint Ownership {0, 1}, 48 Shared Churn Lines)\n(Demonstrates Ada-EHB Protection under Shared Library Churn)', fontweight='bold')
    ax3.set_xticks(xs)
    ax3.set_ylim(0, 9.5)
    ax3.legend(loc='lower right', frameon=True)
    plt.tight_layout()
    fig3_path = os.path.join(output_dir, 'fig3_shared_contention.png')
    plt.savefig(fig3_path, dpi=200, bbox_inches='tight')
    plt.close(fig3)
    print(f"[Generated Figure 3] {fig3_path}")

    print("\nAll experiments, JSON outputs, and publication plots generated successfully!\n")


if __name__ == '__main__':
    main()
