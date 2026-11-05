# TreasureCache: Research Paper Analysis & Defense Simulation

> **Course Project**: Research Paper Analysis & Experimental Validation  
> **Assigned Paper**: *"TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"* (IEEE Transactions on Dependable and Secure Computing, Vol. 21, No. 5, Sept/Oct 2024)  
> **Authors**: Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren  

---

## 📌 Project Overview

This repository contains the comprehensive research study, technical documentation, presentation, and experimental simulation deliverables for the analysis of **TreasureCache**. 

TreasureCache introduces a paradigm shift against cross-core cache side-channel attacks (Prime+Probe, Evict+Time, Flush+Reload): rather than attempting to prevent cache evictions using expensive randomized mapping or rigid cache partitioning, it **allows evictions to occur naturally but hides exploitable evictions in a specialized Eviction-Hidden Buffer (EHB)** with an access latency matched to LLC hits (~40 cycles), supplemented by **Constant-Time Flush (CT-Flush)**.

In addition to critically evaluating the original paper, our team:
1. Identified a critical vulnerability under **adversarial buffer thrashing**.
2. Designed and modeled an architectural improvement: **Ada-EHB (Adaptive Frequency-Aware Eviction-Hidden Buffer)**.
3. Implemented a cycle-accurate multi-core cache hierarchy simulator validating the timing gap closure and defense efficacy.

---

## 📁 Repository Structure & Deliverables

```
├── TreasureCache_Research_Report.docx   # Comprehensive Technical Report (Word Native Style)
├── TreasureCache_Research_Report.pdf    # Technical Report (Exported PDF, 9 pages)
├── TreasureCache_Presentation.pptx     # 14-Slide Presentation Deck with Speaker Notes
├── TreasureCache_Presentation.pdf      # Presentation Deck (Exported PDF)
├── Video_Explanation_Guide.md           # Slide-by-slide speaker script, timing & recording guide
├── TreasureCache_Final_Submission.zip  # Consolidated submission zip archive
│
├── simulation/                          # Source Code for Cache Simulator & Attacks
│   ├── cache_model.py                   # Multi-core inclusive hierarchy, EHB & Ada-EHB logic
│   ├── attacks.py                       # Prime+Probe & Evict+Time attack models against AES
│   ├── run_experiments.py               # Benchmark runner & publication plot generator
│   ├── simulation_results.json          # Quantitative benchmark metrics
│   ├── fig1_latency_distribution.png    # Timing gap elimination plot
│   ├── fig2_attack_success_rate.png     # Side-channel accuracy across defenses
│   ├── fig3_performance_tradeoff.png    # Buffer hit ratio scaling plot
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

Simulation performed across 300 rounds of Prime+Probe and 200 rounds of Evict+Time on an inclusive multi-core cache hierarchy:

| Defense Architecture | Prime+Probe Accuracy (Normal) | Prime+Probe Accuracy (Thrashed) | Evict+Time Timing Gap | Security Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **Unprotected (LRU)** | **100.0%** | **100.0%** | **197.7 cycles** | Vulnerable (Severe Leakage) |
| **Static Partitioning** | 6.7% | 6.7% | 1.0 cycle | Protected (High Capacity Waste) |
| **TreasureCache (Standard)** | 6.0% | 4.3% | 1.0 cycle | Protected (Clean); Buffer Pressure under Thrashing |
| **Ada-EHB (Proposed)** | **5.7%** | **5.0%** | **1.0 cycle** | Robustly Protected Across All Scenarios |
| *Theoretical Random Floor* | *6.25% (1/16)* | *6.25% (1/16)* | *0.0 cycles* | *Ideal Security Bound* |

---

## 🚀 Quickstart: Running the Simulation

### Prerequisites
- Python 3.8+
- Required packages: `numpy`, `matplotlib` (for DOCX/PPTX generation: `python-docx`, `python-pptx`)

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
- **Original Research**: Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren (IEEE TDSC 2024).
- **Analysis, Simulator & Ada-EHB Extension**: Course Research Analysis Team 06.
