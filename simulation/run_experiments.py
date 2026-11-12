"""
run_experiments.py - Multi-Trial Benchmark Execution & Publication Graph Generation
Runs multi-core cache side-channel simulations across 5 random seeds,
computes statistical means and standard deviations, evaluates Ada-EHB under thrashing,
and generates publication-quality figures with explicit attribution and error bars.
"""

import os
import json
import random
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
from attacks import AESVictimWorkload, AttackerPrimeAndProbe, run_evict_and_time_simulation
from cache_model import MultiCoreCacheSystem


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


def run_prime_and_probe_trial(mode: str, rounds: int, thrash_lines: int, seed: int) -> float:
    random.seed(seed)
    np.random.seed(seed)
    
    cache_sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=64)
    victim = AESVictimWorkload()
    attacker = AttackerPrimeAndProbe(target_set_indices=list(range(16)), ways_to_prime=16)

    correct_detections = 0

    for r in range(rounds):
        p_byte = random.randint(0, 255)
        expected_line = victim.get_line_for_byte(p_byte ^ victim.secret_key)
        
        # 1. Attacker primes all 16 target sets
        for s in range(16):
            attacker.prime(cache_sys, s)

        # 2. Adversarial Thrashing Injection:
        if thrash_lines > 0:
            for n in range(thrash_lines):
                cache_sys.tick(5)
                churn_set = n % 16
                churn_addr = ((n + 50) << 17) | (churn_set << 6)
                cache_sys.read_address(core_id=1, addr=churn_addr, domain_id=1, is_sensitive=False)

        # 3. Victim executes encryption round
        v_lat, _ = victim.execute_encryption_round(cache_sys, p_byte)

        # 4. Attacker probes all sets
        probe_results = {}
        for s in range(16):
            total_lat, misses = attacker.probe(cache_sys, s)
            probe_results[s] = total_lat

        max_lat = max(probe_results.values())
        candidates = [k for k, v in probe_results.items() if v == max_lat]
        predicted_line = random.choice(candidates)

        if predicted_line == expected_line:
            correct_detections += 1

    return (correct_detections / rounds) * 100.0


def evaluate_buffer_hit_ratio_curve(mode: str, capacity: int, trials: int = 30, seed: int = 42) -> float:
    random.seed(seed)
    np.random.seed(seed)
    
    ehb_hits = 0
    dram_misses = 0

    for trial in range(trials):
        cs = MultiCoreCacheSystem(mode=mode, ehb_capacity=capacity)
        
        # 1. Victim warms 24 sensitive crypto lines (simulating AES T-tables and key schedule)
        for i in range(24):
            cs.tick(10)
            addr = 0x100000 + (i * 64)
            cs.read_address(0, addr, 0, is_sensitive=True)

        # 2. Attacker causes conflict evictions of victim lines into EHB
        for i in range(24):
            set_idx = ((0x100000 + i * 64) >> 6) & 2047
            for w in range(16):
                cs.tick(5)
                evict_addr = ((w + 100) << 17) | (set_idx << 6)
                cs.read_address(1, evict_addr, 1, is_sensitive=False)

        # 3. Attacker injects 48 churn lines of shared library evictions into EHB
        for n in range(48):
            cs.tick(10)
            shared_addr = 0x600000 + (n * 64)
            cs.read_address(0, shared_addr, 0, is_sensitive=False)
            set_idx = (shared_addr >> 6) & 2047
            for w in range(16):
                cs.tick(5)
                evict_shared = ((w + 200) << 17) | (set_idx << 6)
                cs.read_address(1, evict_shared, 1, is_sensitive=False)

        # 4. Victim re-accesses its 24 sensitive lines
        for i in range(24):
            cs.tick(10)
            addr = 0x100000 + (i * 64)
            lat, lvl = cs.read_address(0, addr, 0, is_sensitive=True)
            if lvl == "EHB_HIT":
                ehb_hits += 1
            elif lvl == "DRAM_MISS":
                dram_misses += 1

    total = ehb_hits + dram_misses
    return (ehb_hits / total * 100.0) if total > 0 else 0.0


def run_all_benchmarks():
    print("=" * 75)
    print("Executing Rigorous Multi-Trial Benchmarks (TreasureCache & Ada-EHB)")
    print("=" * 75)
    
    seeds = [101, 202, 303, 404, 505]
    
    # 1. Multi-trial Prime+Probe Evaluation
    print("\n[1/3] Running Multi-Trial Prime+Probe Simulations (5 Seeds, 300 rounds each)...")
    configs = [
        ("unprotected", "none", 0),
        ("partitioned", "partitioned", 0),
        ("treasure_cache_clean", "treasure_cache", 0),
        ("treasure_cache_thrashed", "treasure_cache", 48),
        ("ada_ehb_thrashed", "ada_ehb", 48)
    ]
    
    pp_stats = {}
    for name, mode, thrash in configs:
        accuracies = []
        for s in seeds:
            acc = run_prime_and_probe_trial(mode=mode, rounds=300, thrash_lines=thrash, seed=s)
            accuracies.append(acc)
        mean_acc = float(np.mean(accuracies))
        std_acc = float(np.std(accuracies))
        pp_stats[name] = {
            "mean": round(mean_acc, 2),
            "std": round(std_acc, 2),
            "samples": [round(x, 2) for x in accuracies]
        }
        print(f"  -> {name:<26}: Mean = {mean_acc:5.2f}% | Std = {std_acc:4.2f}% | Runs = {accuracies}")

    # 2. Evict+Time Evaluation
    print("\n[2/3] Running Evict+Time Simulations (5 Seeds, 200 rounds each)...")
    et_stats = {}
    for name, mode in [("unprotected", "none"), ("partitioned", "partitioned"), ("treasure_cache", "treasure_cache"), ("ada_ehb", "ada_ehb")]:
        gaps = []
        evicted_samples_all = []
        cached_samples_all = []
        for s in seeds:
            res = run_evict_and_time_simulation(mode=mode, rounds=200, seed=s)
            gaps.append(res['timing_gap'])
            if s == seeds[0]:
                evicted_samples_all = res['evicted_samples']
                cached_samples_all = res['cached_samples']
        mean_gap = float(np.mean(gaps))
        std_gap = float(np.std(gaps))
        et_stats[name] = {
            "mean_gap": round(mean_gap, 2),
            "std_gap": round(std_gap, 2),
            "evicted_samples": evicted_samples_all,
            "cached_samples": cached_samples_all
        }
        print(f"  -> {name:<26}: Timing Gap = {mean_gap:5.2f} +/- {std_gap:4.2f} cycles")

    # 3. Buffer Capacity Scaling Study Under Adversarial Thrashing
    print("\n[3/3] Evaluating EHB Capacity Scaling (Buffer Hit Ratio under Adversarial Thrashing)...")
    capacities = [16, 32, 64, 128, 256]
    tc_hit_ratios = []
    tc_hit_stds = []
    ada_hit_ratios = []
    ada_hit_stds = []
    
    for cap in capacities:
        tc_runs = [evaluate_buffer_hit_ratio_curve('treasure_cache', cap, trials=25, seed=s) for s in seeds]
        ada_runs = [evaluate_buffer_hit_ratio_curve('ada_ehb', cap, trials=25, seed=s) for s in seeds]
        
        tc_m = float(np.mean(tc_runs))
        tc_s = float(np.std(tc_runs))
        ada_m = float(np.mean(ada_runs))
        ada_s = float(np.std(ada_runs))
        
        tc_hit_ratios.append(round(tc_m, 1))
        tc_hit_stds.append(round(tc_s, 1))
        ada_hit_ratios.append(round(ada_m, 1))
        ada_hit_stds.append(round(ada_s, 1))
        
        print(f"  Capacity {cap:3d} lines: Standard TC = {tc_m:5.1f}% (+/- {tc_s:3.1f}%) | Ada-EHB = {ada_m:5.1f}% (+/- {ada_s:3.1f}%)")

    # -------------------------------------------------------------
    # Generate Publication Figures
    # -------------------------------------------------------------
    setup_plot_style()
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # FIGURE 1: Latency Distribution with Explicit Attribution
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
    
    unprot_evicted = et_stats['unprotected']['evicted_samples']
    unprot_cached = et_stats['unprotected']['cached_samples']
    ax1.hist(unprot_cached, bins=15, alpha=0.75, label='Cached Access (LLC Hit ~38 cyc)', color='#2b5c8f')
    ax1.hist(unprot_evicted, bins=15, alpha=0.75, label='Evicted Access (DRAM Miss ~200 cyc)', color='#c0392b')
    ax1.set_title('Unprotected Inclusive Cache\n(Exploitable 198-cycle Timing Disparity)', fontweight='bold')
    ax1.set_xlabel('Access Latency (Cycles, Modeled Hierarchy)')
    ax1.set_ylabel('Sample Frequency (N=200)')
    ax1.legend(loc='upper right', frameon=True)
    ax1.set_xlim(20, 240)
    
    tc_evicted = et_stats['treasure_cache']['evicted_samples']
    tc_cached = et_stats['treasure_cache']['cached_samples']
    ax2.hist(tc_cached, bins=15, alpha=0.75, label='Cached Access (LLC Hit ~38 cyc)', color='#2b5c8f')
    ax2.hist(tc_evicted, bins=15, alpha=0.75, label='Evicted Access (EHB Hit ~40 cyc)', color='#27ae60')
    ax2.set_title('TreasureCache Architecture\n(Timing Gap Closed via EHB at ~40 cyc)', fontweight='bold')
    ax2.set_xlabel('Access Latency (Cycles, Modeled Hierarchy)')
    ax2.legend(loc='upper right', frameon=True)
    ax2.set_xlim(20, 240)
    
    fig1.suptitle('Simulation Evaluation: Memory Access Latency Distributions (Team Model Calibration)', fontsize=13, y=1.02)
    plt.tight_layout()
    fig1_path = os.path.join(output_dir, 'fig1_latency_distribution.png')
    plt.savefig(fig1_path, dpi=300, bbox_inches='tight')
    plt.close(fig1)
    print(f"\n[Generated] {fig1_path}")

    # FIGURE 2: Attacker Side-Channel Success Rate with Error Bars
    fig2, ax = plt.subplots(figsize=(9.5, 5.2))
    labels = [
        'Unprotected\n(LRU Baseline)',
        'Static\nPartitioning',
        'TreasureCache\n(Clean)',
        'TreasureCache\n(Thrashed)',
        'Proposed Ada-EHB\n(Thrashed)'
    ]
    means = [
        pp_stats['unprotected']['mean'],
        pp_stats['partitioned']['mean'],
        pp_stats['treasure_cache_clean']['mean'],
        pp_stats['treasure_cache_thrashed']['mean'],
        pp_stats['ada_ehb_thrashed']['mean']
    ]
    stds = [
        pp_stats['unprotected']['std'],
        pp_stats['partitioned']['std'],
        pp_stats['treasure_cache_clean']['std'],
        pp_stats['treasure_cache_thrashed']['std'],
        pp_stats['ada_ehb_thrashed']['std']
    ]
    colors = ['#c0392b', '#7f8c8d', '#27ae60', '#e67e22', '#2980b9']
    
    bars = ax.bar(labels, means, yerr=stds, capsize=5, color=colors, width=0.55, edgecolor='black', linewidth=0.9)
    ax.axhline(y=6.25, color='#444444', linestyle='--', linewidth=1.3, label='Theoretical Random-Guess Expectation (1/16 = 6.25%)')
    
    for bar, m, s in zip(bars, means, stds):
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + s + 1.8, f"{m:.1f}% ± {s:.1f}%", ha='center', va='bottom', fontweight='bold', fontsize=9.5)
        
    ax.set_ylim(0, 115)
    ax.set_ylabel('Attacker Secret Identification Accuracy (%)', fontweight='bold')
    ax.set_title('Prime+Probe Attacker Success Rate Across Defenses (5 Independent Seeds, N=300 Rounds)\n(Attacker predicts which of 16 LLC sets was accessed)', fontweight='bold')
    ax.legend(loc='upper right', frameon=True)
    
    plt.tight_layout()
    fig2_path = os.path.join(output_dir, 'fig2_attack_success_rate.png')
    plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print(f"[Generated] {fig2_path}")

    # FIGURE 3: Buffer Capacity vs Hit Ratio Under Adversarial Thrashing
    fig3, ax = plt.subplots(figsize=(8.5, 5.0))
    x_indices = np.arange(len(capacities))
    width = 0.35
    
    ax.bar(x_indices - width/2, tc_hit_ratios, width, yerr=tc_hit_stds, capsize=4, label='Standard TreasureCache EHB (Ownership/LRU)', color='#e67e22', edgecolor='black')
    ax.bar(x_indices + width/2, ada_hit_ratios, width, yerr=ada_hit_stds, capsize=4, label='Proposed Ada-EHB (Retention Score & Rate Limiting)', color='#2980b9', edgecolor='black')
    
    ax.set_xlabel('Buffer Capacity (Cache Lines / Kilobytes)', fontweight='bold')
    ax.set_ylabel('Eviction Buffer Hit Ratio (%)', fontweight='bold')
    ax.set_title('Eviction-Hidden Buffer Hit Ratio Under Adversarial Thrashing\n(Attacker Injects Sustained Shared Churn into Monitored Sets)', fontweight='bold')
    ax.set_xticks(x_indices)
    ax.set_xticklabels([f"{c} lines\n({(c*64)/1024:.1f} KB)" for c in capacities])
    ax.set_ylim(0, 115)
    ax.legend(loc='lower right', frameon=True)
    
    for i in range(len(capacities)):
        ax.text(x_indices[i] - width/2, tc_hit_ratios[i] + tc_hit_stds[i] + 1.8, f"{tc_hit_ratios[i]:.1f}%", ha='center', fontsize=9)
        ax.text(x_indices[i] + width/2, ada_hit_ratios[i] + ada_hit_stds[i] + 1.8, f"{ada_hit_ratios[i]:.1f}%", ha='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    fig3_path = os.path.join(output_dir, 'fig3_performance_tradeoff.png')
    plt.savefig(fig3_path, dpi=300, bbox_inches='tight')
    plt.close(fig3)
    print(f"[Generated] {fig3_path}")

    # Save summary json
    summary_data = {
        "simulation_parameters": {
            "l1_hit_latency_cycles": 4,
            "l2_hit_latency_cycles": 12,
            "llc_hit_latency_cycles": 38,
            "ehb_hit_latency_cycles": 40,
            "dram_latency_cycles": 200,
            "ct_flush_latency_cycles": 70,
            "random_guess_expectation_percent": 6.25,
            "num_seeds": len(seeds),
            "seeds": seeds,
            "rounds_per_seed": 300
        },
        "prime_and_probe": pp_stats,
        "evict_and_time": {
            k: {"mean_gap": v["mean_gap"], "std_gap": v["std_gap"]} for k, v in et_stats.items()
        },
        "capacity_study": {
            "capacities_lines": capacities,
            "capacities_kb": [(c*64)/1024 for c in capacities],
            "tc_hit_ratios_mean": tc_hit_ratios,
            "tc_hit_ratios_std": tc_hit_stds,
            "ada_hit_ratios_mean": ada_hit_ratios,
            "ada_hit_ratios_std": ada_hit_stds
        }
    }
    
    json_path = os.path.join(output_dir, 'simulation_results.json')
    with open(json_path, 'w') as f:
        json.dump(summary_data, f, indent=4)
    print(f"[Generated] {json_path}")
    print("\nAll multi-trial benchmarks and plots completed successfully!\n")


if __name__ == '__main__':
    run_all_benchmarks()
