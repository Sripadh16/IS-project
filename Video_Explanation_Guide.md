# Explanation Video Guide & Script
## TreasureCache & Ada-EHB / Ada-EHB+: Research Analysis, Critical Assessment, and Architectural Extension

> **Course**: Information Security / Hardware Security Capstone  
> **Topic**: Critical Analysis and Extension of *"TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"* (Mengming Li et al., IEEE TDSC Sept/Oct 2024)  
> **Extensions**: Ada-EHB (Dynamic Retention Scoring) & Ada-EHB+ (Ada-EHB 2.0 with Elastic Cloud Quotas & Shannon Profiling)  
> **Target Duration**: 12–15 Minutes (20 Slides)  
> **Format**: Slide Presentation + Live Code & Experimental Verification Walkthrough + Webcam Face Overlay  
> **Speaking Format**: **Two Structured Rounds per Presenter**  
> **Speaker Order**: **Kontham Sripadha (Intro)** &rarr; **Sreekar Tirumala** &rarr; **A Venu Vivek** &rarr; **Kontham Sripadha** &rarr; **Sreekar Tirumala** &rarr; **A Venu Vivek**  
> **Full Spoken Script**: See [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md) for word-for-word spoken narration for each slide.

---

## 1. Video Recording Protocol & Evaluator Checklist

To achieve maximum marks according to the course rubric, strictly adhere to the following setup checklist:

- [ ] **Webcam & Lighting**: Face clearly visible in the corner throughout the presentation and code demo. Do not block slide content or code terminal text.
- [ ] **Identity Banner**: Display your full name, student ID, and role title in an introductory overlay or persistent bottom corner tag.
- [ ] **Audio Quality**: Clear microphone input without background noise or heavy reverberation.
- [ ] **Resolution**: Record at 1080p (1920x1080) at 30 or 60 fps (OBS Studio, Zoom, or Teams).
- [ ] **Screen Allocation**:
  - *Part 1 (Slides 1–10)*: Full-screen presentation (`TreasureCache_Presentation.pptx` or `TreasureCache_Presentation.pdf`).
  - *Part 2 (Slides 11–16 & Code Demo)*: Alternating view showing the slide figures, terminal running `python simulation/run_experiments.py`, and test verification `python simulation/test_advanced_suite.py`.
  - *Part 3 (Slides 17–20)*: Full-screen presentation for verification, comparative matrix, contributions, conclusion, and Q&A.
- [ ] **No "Black Box" Claims**: Clearly articulate the mathematical formulas, microarchitectural mechanisms, and state machines behind both TreasureCache and Ada-EHB / Ada-EHB+.

---

## 2. 2-Round Timing Breakdown & Slide Allocation

| Round | Speaker | Roll No. | Core Technical Focus | Slides Covered | Target Time |
| :---: | :--- | :---: | :--- | :---: | :---: |
| **Round 1 (Part 1)** | **Kontham Sripadha** | `CS23I1018` | Introduction, Memory Hierarchy Timing Disparities, Attack Taxonomy & Prior Defenses | **Slides 1 – 4** | ~3.0 mins |
| **Round 1 (Part 2)** | **Sreekar Tirumala** | `CS23I1034` | TreasureCache Paradigm, EHB Architecture, Dual Insertion Logic & Formal Proofs | **Slides 5 – 7** | ~2.5 mins |
| **Round 1 (Part 3)** | **A Venu Vivek** | `CS23I1015` | Hardware Feasibility, Silicon Limits, Gaps in Paper & Proposed Upgrades (Ada-EHB/+) | **Slides 8 – 10** | ~2.5 mins |
| **Round 2 (Part 1)** | **Kontham Sripadha** | `CS23I1018` | Simulation Testbench, Domain-Isolated Residency & Evict+Time Latency Neutralization | **Slides 11 – 13** | ~2.2 mins |
| **Round 2 (Part 2)** | **Sreekar Tirumala** | `CS23I1034` | Shared-Memory Attack Discovery, Multi-Vector Attack Suite & Hardware RTL Breakdown | **Slides 14 – 16** | ~2.5 mins |
| **Round 2 (Part 3)** | **A Venu Vivek** | `CS23I1015` | 20/20 Test Verification, Comprehensive Comparative Matrix, Roles & Final Conclusion | **Slides 17 – 20** | ~2.5 mins |

---

## 3. High-Level Speaker Guide by Slide

### ROUND 1: Foundations, Architecture, Mathematical Proofs & Critical Flaws

#### Slide 1: Title & Project Overview
- **Speaker**: **Kontham Sripadha** (CS23I1018)
- **Time**: ~45s
- **Key Points**: Introduce yourself and team members; establish research topic: IEEE TDSC 2024 TreasureCache analysis and Ada-EHB/Ada-EHB+ extensions.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-1-title--project-overview).*

#### Slide 2: Memory Hierarchy Timing Disparities
- **Speaker**: **Kontham Sripadha** (CS23I1018)
- **Time**: ~45s
- **Key Points**: Contrast private L1/L2 caches with shared LLC and DRAM; explain the 160-cycle timing disparity and why inclusive cache back-invalidation creates the exploitation lever.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-2-the-root-problem-memory-hierarchy-timing-disparities).*

#### Slide 3: Threat Model & Side-Channel Attack Taxonomy
- **Speaker**: **Kontham Sripadha** (CS23I1018)
- **Time**: ~45s
- **Key Points**: Conflict-based vectors (Prime+Probe, Evict+Time) without shared memory vs. Flush-based vectors (Flush+Reload, Flush+Flush) with shared memory.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-3-threat-model--side-channel-attack-taxonomy).*

#### Slide 4: Why Existing Hardware Defenses Fall Short
- **Speaker**: **Kontham Sripadha** (CS23I1018)
- **Time**: ~45s
- **Key Points**: Breakdown of Partitioning (CAT/PLCache capacity waste), Randomization (CEASER attackable by eviction sets), and Invalidation-Delaying (SHARP leaking in PRP). Handoff to Sreekar.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-4-why-existing-hardware-defenses-fall-short).*

---

#### Slide 5: The TreasureCache Defense Paradigm
- **Speaker**: **Sreekar Tirumala** (CS23I1034)
- **Time**: ~50s
- **Key Points**: Core insight: cache eviction is safe if victim subsequent access does not incur DRAM latency; introduce the Eviction-Holding Buffer (EHB), CAM tag store, and domain ownership registers.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-5-the-treasurecache-defense-paradigm).*

#### Slide 6: Dual Insertion Logic: Condition 1 vs Condition 2
- **Speaker**: **Sreekar Tirumala** (CS23I1034)
- **Time**: ~50s
- **Key Points**: Explain Condition 1 (victim LLC eviction) and Condition 2 (reload displacement `from_ehb`); explain constant-time flush (70 cycles) against Flush+Flush.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-6-dual-insertion-logic-condition-1-vs-condition-2).*

#### Slide 7: Mathematical Modeling & Security Boundary Proofs
- **Speaker**: **Sreekar Tirumala** (CS23I1034)
- **Time**: ~50s
- **Key Points**: Walk through paper formulas (Eq. 1–4, $P_i$, binomial eviction $c$); proof of $k \ge 89$ defense threshold; proof of 1,000x epoch dilation ($9.89 \times 10^6$ cycles). Handoff to Venu.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-7-mathematical-modeling--security-boundary-proofs).*

---

#### Slide 8: Hardware Realization & Silicon Feasibility
- **Speaker**: **A Venu Vivek** (CS23I1015)
- **Time**: ~45s
- **Key Points**: TSMC 28nm/7nm synthesis metrics: 78,583 GE, 380 ps search delay (<400 ps @ 2.5 GHz), 0.335% area, and <0.028% dynamic power via microarchitectural filtering.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-8-hardware-realization--silicon-feasibility).*

#### Slide 9: Gaps & Critical Limitations in TreasureCache
- **Speaker**: **A Venu Vivek** (CS23I1015)
- **Time**: ~50s
- **Key Points**: Expose the 3 major flaws: Shared-Memory Contention Vulnerability (`owners={0,1}` drops retention to 0%), Static Partition Inefficiency in cloud servers, and lack of threat awareness under algorithmic thrashing.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-9-gaps--critical-limitations-in-treasurecache).*

#### Slide 10: Proposed Extensions: Ada-EHB & Ada-EHB+
- **Speaker**: **A Venu Vivek** (CS23I1015)
- **Time**: ~50s
- **Key Points**: Introduce Dynamic Retention Scoring $R(k)$, Dynamic Elastic Domain Quota (DEDQ) with Instant Revocation Floor, Shannon Entropy Profiler ($W=32$, $H \ge 0.85$), and multi-tier sensitivity. Handoff back to Sripadha.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-10-proposed-extensions-ada-ehb--ada-ehb-ada-ehb-20).*

---

### ROUND 2: Benchmarking, Breakthrough Results, RTL & Verification

#### Slide 11: Simulation Methodology & Testbench Architecture
- **Speaker**: **Kontham Sripadha** (CS23I1018)
- **Time**: ~45s
- **Key Points**: Microarchitectural simulator design; 5 independent random seeds; multi-level parameters (L1 4c, L2 14c, LLC 40c, DRAM 200c); cross-validation with 50,000 Monte Carlo runs.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-11-simulation-methodology--testbench-architecture).*

#### Slide 12: Experimental Results: Domain-Isolated Residency
- **Speaker**: **Kontham Sripadha** (CS23I1018)
- **Time**: ~45s
- **Key Points**: Walk through Figure 1: Unprotected baseline retains 0.0/8 lines; TreasureCache and Ada-EHB achieve 100% (8.0/8 lines) at capacities $\ge 16$.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-12-experimental-results-domain-isolated-residency).*

#### Slide 13: Experimental Results: Evict+Time Latency Neutralization
- **Speaker**: **Kontham Sripadha** (CS23I1018)
- **Time**: ~45s
- **Key Points**: Walk through Figure 2: Baseline exhibits 164.5-cycle timing leak (201.5 cyc miss); TreasureCache and Ada-EHB drop latency to 40.0 cycles and reduce timing gap to 2.0 cycles. Handoff to Sreekar.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-13-experimental-results-evicttime-latency-neutralization).*

---

#### Slide 14: Critical Finding: Shared-Memory Contention Defense
- **Speaker**: **Sreekar Tirumala** (CS23I1034)
- **Time**: ~50s
- **Key Points**: Highlight Figure 3: TreasureCache drops to 0.0/8 lines (201 cyc) due to unweighted LRU eviction of jointly-owned lines; Ada-EHB retains 8.0/8 lines (40 cyc) via dynamic retention scoring.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-14-critical-finding-shared-memory-contention-defense).*

#### Slide 15: Comprehensive Attack Suite Evaluation
- **Speaker**: **Sreekar Tirumala** (CS23I1034)
- **Time**: ~50s
- **Key Points**: Walk through Figure 4: Mitigation across Flush+Reload, Flush+Flush, and Prime+Probe. Empirically prove why Condition 1 alone leaks 167.8 cycles in Prime+Reprime+Probe, and how Condition 2 neutralizes it to 2.0 cycles.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-15-comprehensive-attack-suite-evaluation).*

#### Slide 16: Hardware RTL & TSMC 28nm/7nm Synthesis Breakdown
- **Speaker**: **Sreekar Tirumala** (CS23I1034)
- **Time**: ~50s
- **Key Points**: Walk through Figure 5 and Verilog modules: `cam_tag_cell.v`, `retention_alu.v` shift-and-add logic, and `token_bucket_limiter.v`. Total overhead is only 78,583 GE. Handoff to Venu.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-16-hardware-rtl--tsmc-28nm7nm-synthesis-breakdown).*

---

#### Slide 17: Master QA Verification Suite: 20/20 Tests Passed
- **Speaker**: **A Venu Vivek** (CS23I1015)
- **Time**: ~40s
- **Key Points**: Overview of 20 automated unit and verification tests in `test_advanced_suite.py`, validating CAM logic, dual conditions, all 4 attacks, and hardware bounds in 0.04s.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-17-master-qa-verification-suite-2020-tests-passed).*

#### Slide 18: Comprehensive Comparative Assessment
- **Speaker**: **A Venu Vivek** (CS23I1015)
- **Time**: ~45s
- **Key Points**: Multi-dimensional trade-off matrix: Baseline vs. PLCache vs. SHARP vs. TreasureCache vs. Ada-EHB vs. Ada-EHB+.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-18-comprehensive-comparative-assessment).*

#### Slide 19: Team Roles & Individual Contributions
- **Speaker**: **A Venu Vivek** (CS23I1015)
- **Time**: ~30s
- **Key Points**: Explicit role attribution for Sreekar Tirumala, Kontham Sripadha, and A Venu Vivek.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-19-team-roles--individual-contributions).*

#### Slide 20: Conclusion, Future Work & Q&A
- **Speaker**: **A Venu Vivek** (CS23I1015)
- **Time**: ~40s
- **Key Points**: Recap of contributions; open-source GitHub repository invitation; formal closing and opening of the floor to questions.
- *Full script available in [PRESENTATION_SCRIPT.md](file:///c:/Users/Sreekar_Tirumala/Documents/College/IS/IS-project/PRESENTATION_SCRIPT.md#slide-20-conclusion-future-work--qa).*

---

## 4. Live Code Demonstration Script (For Video Recording)

When transitioning to the live terminal demonstration (e.g., during Slide 11 or Slide 17), execute the following commands in order:

```powershell
# 1. Run all 40 unit and verification tests (completes in < 1 second)
python -m unittest discover simulation

# 2. Run the full experimental benchmarks and generate JSON results
python simulation/run_experiments.py

# 3. Run the multi-vector attack suite (Flush+Reload, Flush+Flush, Prime+Probe, PRP)
python simulation/advanced_attacks.py

# 4. Run the synthesizable hardware evaluation (TSMC 28nm/7nm)
python simulation/hardware_evaluation.py
```
