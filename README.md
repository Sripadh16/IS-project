# TreasureCache: Research Paper Analysis & Defense Simulation

> **Course Project**: Research Paper Analysis & Experimental Validation  
> **Assigned Paper**: *"TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"* (IEEE Transactions on Dependable and Secure Computing, Vol. 21, No. 5, Sept./Oct. 2024 [1])  
> **Authors**: Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren  
> **Analysis Team**: Kontham Sripadha (Lead Analyst & Simulation Engineer), and Project Analysis Group 06  

---

## 📌 Project Overview

This repository contains the research analysis, technical documentation, presentation deck, and experimental simulation deliverables for the analysis of **TreasureCache** [1].

TreasureCache introduces a paradigm shift against cross-core cache side-channel attacks (Prime+Probe, Evict+Time, Flush+Reload): rather than attempting to prevent cache evictions using expensive randomized mapping or rigid cache partitioning, it **allows evictions to occur naturally but hides exploitable evictions in a specialized Eviction-Hidden Buffer (EHB)** with an access latency matched to LLC hits (~40 cycles), supplemented by **Constant-Time Flush (CT-Flush)**.

In addition to critically evaluating the original paper, our team:
1. Identified a critical vulnerability under **adversarial buffer thrashing**.
2. Designed and modeled an architectural improvement: **Ada-EHB (Adaptive Frequency-Aware Eviction-Hidden Buffer)** with a formal retention scoring function, 4-bit saturating frequency counters, and token-bucket burst rate-limiting.
3. Implemented a cycle-calibrated multi-core cache hierarchy simulator validating timing gap closure, attacker accuracy reduction to the random-guess expectation (6.25%), and buffer hit-ratio preservation.

---

## 📁 Repository Structure & Deliverables

```
├── TreasureCache_Research_Report.docx   # Comprehensive Technical Report (Word Native Style, 12 pages)
├── TreasureCache_Research_Report.pdf    # Technical Report (Exported PDF, 12 pages)
├── TreasureCache_Presentation.pptx     # 15-Slide Presentation Deck with Speaker Notes
├── TreasureCache_Presentation.pdf      # Presentation Deck (Exported PDF, 15 slides)
├── Video_Explanation_Guide.md           # Slide-by-slide speaker script, timing & recording guide
├── TreasureCache_Final_Submission.zip  # Consolidated submission zip archive
│
├── simulation/                          # Source Code for Cache Simulator & Attacks
│   ├── cache_model.py                   # Multi-core inclusive hierarchy, EHB & Ada-EHB logic
│   ├── attacks.py                       # Prime+Probe & Evict+Time attack models against AES
│   ├── run_experiments.py               # Benchmark runner & publication plot generator
│   ├── simulation_results.json          # Quantitative benchmark metrics (5 seeds)
│   ├── fig1_latency_distribution.png    # Timing gap elimination plot
│   ├── fig2_attack_success_rate.png     # Side-channel accuracy across defenses (with error bars)
│   ├── fig3_performance_tradeoff.png    # Buffer hit ratio scaling plot under thrashing
│   └── README.md                        # Simulation documentation & reproduction steps
│
├── build_technical_report.py            # Automated generator for Word report (.docx)
├── build_presentation.py                # Automated generator for PowerPoint (.pptx)
├── package_submission.py                # Submission packaging script
├── 6_TreasureCache_...pdf               # Original IEEE TDSC 2024 Research Paper
└── IS_ResearchAnalysis_Instructions.pdf  # Course project guidelines & evaluation rubrics
```

---

## 🔬 Experimental Validation & Results Summary

Simulation evaluated across 5 random seeds (101, 202, 303, 404, 505) with 300 rounds of Prime+Probe and 200 rounds of Evict+Time on a cycle-calibrated inclusive multi-core cache hierarchy:

| Defense Architecture | Prime+Probe Accuracy (Mean ± Std) | Evict+Time Timing Gap | Buffer Hit Ratio (32 lines / Thrash) | Security Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **Unprotected (LRU Baseline)** | **100.0% ± 0.0%** | **197.80 ± 0.24 cyc** | N/A | Vulnerable (100% Secret Leakage) |
| **Static Partitioning** | 6.27% ± 0.83% | 0.99 ± 0.01 cyc | N/A | Protected (High Capacity Waste) |
| **TreasureCache (Clean) [1]** | 11.20% ± 0.72% | 1.17 ± 0.02 cyc | 100.0% | Protected Under Nominal Traffic |
| **TreasureCache (Thrashed) [1]** | 6.27% ± 1.48% | 1.17 ± 0.02 cyc | **0.0%** | Degraded (LRU Evicts Sensitive Lines) |
| **Ada-EHB (Proposed Improvement)** | **6.27% ± 1.48%** | **1.17 ± 0.02 cyc** | **100.0%** | **Robustly Protected (Retention Score Preserves Lines)** |
| *Theoretical Random Floor* | *6.25% (1/16 sets)* | *0.00 cyc* | *100.0%* | *Ideal Security Bound* |

---

## 🚀 Quickstart: Running the Simulation

### Prerequisites
- Python 3.8+
- Required packages: `numpy`, `matplotlib`, `python-docx`, `python-pptx`

```bash
pip install numpy matplotlib python-docx python-pptx
```

### Run Benchmarks & Re-generate Plots:
```bash
python simulation/run_experiments.py
```

### Re-generate Report, Slides & Zip Package:
```bash
python build_technical_report.py
python build_presentation.py
python package_submission.py
```

---

## 👥 Authors & Attribution
- **Original Research**: Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren (*IEEE TDSC*, Vol. 21, No. 5, Sept./Oct. 2024 [1]).
- **Research Analysis, Simulator & Ada-EHB Extension**: Kontham Sripadha and Course Analysis Team 06.
