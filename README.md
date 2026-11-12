# TreasureCache: Research Paper Analysis & Defense Simulation

> **Course Project**: Research Paper Analysis, Critical Evaluation & Experimental Validation  
> **Assigned Paper**: *"TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"* (IEEE Transactions on Dependable and Secure Computing, Vol. 21, No. 5, Sept./Oct. 2024 [1])  
> **Original Authors**: Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren  
> **Analysis Team**: Kontham Sripadha (Lead Analyst & Simulation Engineer), and Project Analysis Group 06  

---

## 📌 Project Overview

This repository contains the complete research deliverables for our critical analysis and architectural extension of **TreasureCache** [1].

TreasureCache addresses cross-core cache side-channel attacks (Prime+Probe, Evict+Time, Flush+Reload). Rather than preventing evictions through rigid hardware cache partitioning or high-overhead randomized indexing, it **permits evictions to occur naturally while shielding evicted lines inside a specialized Content-Addressable Memory (CAM) called the Eviction-Hidden Buffer (EHB)** with an access latency matched to LLC hits (~40 cycles), supplemented by **Constant-Time Flush (CT-Flush)**.

### Our Independent Contributions:
1. **Critical Vulnerability Discovery**: Identified that while TreasureCache's security domain ownership isolates strictly private memory lines, **shared-memory lines (with joint ownership `owners={0, 1}`) are vulnerable to adversarial buffer thrashing**, causing victim lines to be evicted to DRAM (0% retention, 201 cycles).
2. **Architectural Extension (Ada-EHB)**: Designed and implemented **Ada-EHB (Adaptive Frequency-Aware Eviction-Hidden Buffer)** featuring:
   - Dynamic retention scoring: $R(k) = \frac{S(k) \cdot (1 + 0.2 \cdot F(k))}{\ln(1 + \text{Age}(k) + 10^{-5})}$
   - Sticky residency for marked sensitive blocks (e.g., cryptographic S-boxes)
   - Token-bucket burst rate-limiting against adversarial flooding
3. **Rigorous Experimental Validation**: Built an inclusive multi-core cache hierarchy simulator, implemented 10 automated unit tests, and validated the system across 5 random seeds (101, 202, 303, 404, 505) under identical workloads.

---

## 📁 Repository Structure & Deliverables

```
├── TreasureCache_Research_Report.docx   # Comprehensive Technical Report (Word Native Style, IEEE format)
├── TreasureCache_Research_Report.pdf    # Technical Report (Exported PDF)
├── TreasureCache_Presentation.pptx     # 15-Slide Presentation Deck with Complete Speaker Notes
├── TreasureCache_Presentation.pdf      # Presentation Deck (Exported PDF)
├── Video_Explanation_Guide.md           # Slide-by-slide speaker script, timing, demo & Q&A guide
├── TreasureCache_Final_Submission.zip  # Consolidated submission zip archive
│
├── simulation/                          # Source Code for Cache Simulator & Attacks
│   ├── cache_model.py                   # Multi-core hierarchy, EHB, CT-Flush & Ada-EHB logic
│   ├── attacks.py                       # AES victim workload, forced eviction, residency & Evict+Time
│   ├── test_simulation.py               # 10 automated unit tests for placement, replacement & CT-Flush
│   ├── run_experiments.py               # Benchmark runner & publication plot generator (5 seeds)
│   ├── simulation_results.json          # Quantitative benchmark metrics (5 seeds)
│   ├── fig1_residency.png               # Domain-isolated residency benchmark (Capacities 8, 16, 32, 64)
│   ├── fig2_victim_latency.png          # Evict+Time victim latency distributions (Baseline vs TC vs Ada-EHB)
│   ├── fig3_shared_contention.png       # Shared-memory contention defense (TC 0/8 vs Ada-EHB 8/8)
│   └── README.md                        # Simulation documentation & reproduction steps
│
├── build_technical_report.py            # Automated generator for Word report (.docx)
├── build_presentation.py                # Automated generator for PowerPoint (.pptx)
├── package_submission.py                # Submission packaging script
├── 6_TreasureCache_Hiding_Cache_Evictions_Against_Side_Channel_Attacks.pdf # IEEE TDSC 2024 Paper
└── IS_ResearchAnalysis_Instructions.pdf  # Course project guidelines & evaluation rubrics
```

---

## 🔬 Experimental Validation & Results Summary

Simulations evaluated across 5 random seeds (`101`, `202`, `303`, `404`, `505`) with 100 trials per configuration on a cycle-calibrated multi-core cache hierarchy (L1 hit: 4 cyc; LLC hit / EHB hit: 40 cyc; DRAM miss: 200 cyc):

### 1. Evict+Time Side-Channel Mitigation

| Architecture | Evicted Set Latency (cyc) | Non-Evicted Set Latency (cyc) | Timing Gap ($\Delta$) | Attack Feasibility |
| :--- | :---: | :---: | :---: | :--- |
| **Baseline (Unprotected)** | **204.45 ± 0.23** | **40.00 ± 0.00** | **164.45 ± 0.23 cyc** | **High (Full Key Recovery)** |
| **TreasureCache [1]** | 42.00 ± 0.00 | 40.00 ± 0.00 | 2.00 ± 0.00 cyc | Neutralized (Within Noise) |
| **Ada-EHB (Proposed)** | 42.00 ± 0.00 | 40.00 ± 0.00 | **2.00 ± 0.00 cyc** | **Neutralized (Within Noise)** |

### 2. Domain-Isolated Residency Benchmark (Victim Lines Retained / 8)

| EHB Capacity ($N_{\text{lines}}$) | Domain Quota ($N_{\text{quota}}$) | TreasureCache Retained | Ada-EHB Retained | Victim Latency |
| :---: | :---: | :---: | :---: | :---: |
| **8 lines** | 4 lines | 4.0 / 8 lines | 4.0 / 8 lines | 120.5 cycles |
| **16 lines** | 8 lines | 8.0 / 8 lines | 8.0 / 8 lines | 40.0 cycles |
| **32 lines** | 16 lines | 8.0 / 8 lines | 8.0 / 8 lines | 40.0 cycles |
| **64 lines** | 32 lines | 8.0 / 8 lines | 8.0 / 8 lines | 40.0 cycles |

*Finding*: In domain-isolated traffic (`owners={1}` vs `{0}`), TreasureCache's domain ownership strictly isolates victim lines; Ada-EHB produces identical, verified results.

### 3. Shared-Memory Contention Defense (`owners={0, 1}`)

| Architecture | Sensitive Lines Retained (/8) | Mean Victim Latency (cyc) | Buffer State Under Thrashing |
| :--- | :---: | :---: | :--- |
| **TreasureCache (LRU) [1]** | **0.0 / 8 lines (0.0%)** | **201.00 cycles** | **Displaced to DRAM by attacker traffic** |
| **Ada-EHB (Proposed)** | **8.0 / 8 lines (100.0%)** | **40.00 cycles** | **100% Protected (Sticky Residency & Retention Score)** |

---

## 🚀 Quickstart: Reproduction Instructions

### 1. Run Automated Unit Tests (10/10)
```powershell
python simulation/test_simulation.py
```
*Expected Output*: `Ran 10 tests in 0.005s - OK`

### 2. Run Benchmarks & Re-generate Figures (5 Seeds)
```powershell
python simulation/run_experiments.py
```
*Outputs*: `simulation_results.json`, `fig1_residency.png`, `fig2_victim_latency.png`, `fig3_shared_contention.png`.

### 3. Build Word Report & PowerPoint Presentation
```powershell
python build_technical_report.py
python build_presentation.py
```

### 4. Build Submission ZIP Package
```powershell
python package_submission.py
```
*Outputs*: `TreasureCache_Final_Submission.zip` (contains all mandatory project artifacts).

---

## 👥 Authors & Attribution
- **Original Research**: Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren (*IEEE Transactions on Dependable and Secure Computing*, Vol. 21, No. 5, Sept./Oct. 2024 [1]).
- **Research Analysis, Independent Critical Evaluation & Ada-EHB Extension**: Kontham Sripadha and Course Analysis Team 06.
