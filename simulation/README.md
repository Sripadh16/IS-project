# Multi-Core Cache Side-Channel & TreasureCache Simulator

This repository contains the simulation source code accompanying the research analysis of the paper:
**"TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"** (IEEE TDSC 2024).

---

## 1. Overview of Architecture

The simulator models a multi-core processor hierarchy with inclusive caching:
- **Private L1 Data Cache**: 32 KB, 8-way set-associative per core (4-cycle hit latency).
- **Private L2 Cache**: 256 KB, 8-way set-associative per core (12-cycle hit latency).
- **Shared Last-Level Cache (LLC)**: 2 MB, 16-way set-associative shared inclusive cache (38-cycle hit latency).
- **Main Memory (DRAM)**: ~200-cycle access latency.

### Defense Architectures Implemented:
1. **Unprotected Baseline**: Standard inclusive LLC vulnerable to cross-core eviction monitoring.
2. **Static Cache Partitioning**: Way-partitioning baseline separating security domains.
3. **TreasureCache**:
   - Fully-associative **Eviction-Hidden Buffer (EHB)** serving hits with LLC-equivalent latency (~40 cycles).
   - **Secure Placement Policy**: selectively buffers lines evicted from LLC that reside in private caches (exploitable due to inclusiveness).
   - **Constant-Time Flush (CT-Flush)**: Normalizes execution latency across cached and uncached lines.
4. **Proposed Extension: Ada-EHB (Adaptive Frequency-Aware EHB)**:
   - Dynamic sensitivity scoring and entropy-aware replacement to mitigate buffer exhaustion under aggressive adversarial thrashing.

---

## 2. Directory Structure

- `cache_model.py`: Core hardware cache modeling, multi-level hierarchy, EHB, and Ada-EHB logic.
- `attacks.py`: Implementation of cryptographic victim workload (AES S-Box lookup table) and side-channel attack models (`Prime+Probe`, `Evict+Time`).
- `run_experiments.py`: Experiment runner evaluating security and performance metrics, generating quantitative plots.
- `simulation_results.json`: Quantitative simulation output metrics.
- Generated plots:
  - `fig1_latency_distribution.png`: Elimination of the hit/miss timing gap under TreasureCache.
  - `fig2_attack_success_rate.png`: Attacker secret deduction accuracy across defenses.
  - `fig3_performance_tradeoff.png`: Buffer hit ratio vs capacity scaling.

---

## 3. How to Run the Experiments

### Requirements
- Python 3.8+
- `numpy`, `matplotlib`

### Execution
From the project root or simulation folder, run:
```bash
python simulation/run_experiments.py
```

The script runs 300 rounds of Prime+Probe and 200 rounds of Evict+Time across all configurations, logs statistics to the terminal, and regenerates the figures.

