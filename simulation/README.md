# TreasureCache & Ada-EHB Simulation Model (Integrated & Verified)

## 1. Overview & Architectural Scope

This directory contains the sequential synthetic cache-event simulation codebase used for the research analysis of:
**"TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"** (IEEE TDSC 2024 [1]), along with our proposed extension: **Ada-EHB (Adaptive Frequency-Aware Eviction-Hidden Buffer)**.

### Model Scope & Limitations
- **Educational Sequential Cache-Event Model**: This simulator models sequential cache operations and access latencies across a multi-level hierarchy (Private L1/L2, Shared Inclusive LLC, and DRAM).
- **Not Full-System gem5**: It is NOT a full-system gem5 cycle-accurate simulator, does not execute full x86-64 out-of-order execution pipelines, and does not claim hardware-level silicon area or power measurements.
- **Physical Memory Model**: Shared memory is explicitly represented through multi-domain ownership sets (`owners: Set[int]`), and private-cache residency is tracked per core (`sharers: Set[int]`).
- **Cryptographic Model**: Emulates cryptographic table lookup patterns (e.g. AES S-Box / T-tables) and measures access latency distributions rather than attacking full mathematical key schedules.

---

## 2. Directory Structure

```
simulation/
├── cache_model.py           # Core multi-level inclusive cache hierarchy, EHB, & Ada-EHB logic
├── attacks.py               # Targeted LLC eviction, residency trials, & Evict+Time models
├── run_experiments.py       # Multi-trial benchmarking runner across 5 random seeds (101..505)
├── test_simulation.py       # 10 automated behavioral regression tests
├── simulation_results.json  # Fresh structured JSON metrics generated from simulator
├── fig1_residency.png       # Victim buffer residency under domain-isolated churn
├── fig2_victim_latency.png  # Mean victim access latency after LLC eviction
├── fig3_shared_contention.png # Shared-memory contention study comparing TC vs Ada-EHB
└── README.md                # Documentation & execution guide
```

---

## 3. Key Architectural Mechanisms Implemented

### A. Dual-Condition Secure Placement (TreasureCache Baseline)
An evicted LLC block is admitted to the EHB if and only if:
1. **Condition 1 (Private Sharers)**: The evicted block has active copies resident in private L1/L2 caches (`had_sharers == True`).
2. **Condition 2 (EHB Reload Replacement)**: The evicted block was replaced in the LLC by a block loaded from the EHB (`from_ehb == True`).
All other evictions bypass directly to main memory (DRAM).

### B. Domain-Isolated Replacement (TreasureCache Baseline)
- Every line tracks physical ownership (`owners: Set[int]`).
- **Eligibility Rule**: An incoming block can ONLY replace an entry whose owners are a subset of the incoming block's owners (`e.owners.issubset(incoming_owners)`).
- **Domain Quotas**: A conservative cap (`quota = capacity // num_domains`) prevents an attacker domain from ever displacing victim-owned lines in disjoint memory.

### C. Ada-EHB Extension (Proposed Improvement)
1. **Retention Score**:
   $$R(k) = \frac{S(k) \cdot (1 + \alpha \cdot F(k))}{\ln(1 + \text{Age}(k) + \epsilon)}$$
   - $S(k)$: Sensitivity Weight (3.0 for sensitive lines, 1.0 for normal).
   - $F(k)$: 4-bit Saturating Frequency Counter ($0 \le F(k) \le 15$), incremented on access.
   - $\alpha = 0.2$: Frequency weighting factor.
   - $\text{Age}(k)$: Elapsed cycles since last reference.
   - $\epsilon = 10^{-5}$: Regularization constant preventing division by zero.
2. **Replacement & Sticky Residency**:
   - Evicts candidate with minimum retention score: $\arg\min R(k)$.
   - Sensitive entries are strictly protected while eligible non-sensitive entries exist.
   - If all eligible entries are sensitive and incoming is non-sensitive, the incoming block bypasses to DRAM.
3. **Token-Bucket Burst Rate-Limiting**:
   - Bucket capacity $M = 8$ burst tokens per domain; refill rate = 1 token per 125 cycles. Non-sensitive burst evictions exceeding available tokens bypass to DRAM.

---

## 4. How to Run the Tests and Experiments

### Prerequisites
- Python 3.8+ (Python 3.10+ recommended)
- `matplotlib`

```bash
pip install matplotlib
```

### Running the Automated Test Suite (10 Tests):
```bash
python simulation/test_simulation.py
```
*Expected output: `Ran 10 tests in 0.005s ... OK`*

### Running the Full Multi-Trial Experiments:
```bash
python simulation/run_experiments.py
```
This runs 5 random seeds (`101`, `202`, `303`, `404`, `505`), logs metrics to the terminal, updates `simulation_results.json`, and regenerates `fig1_residency.png`, `fig2_victim_latency.png`, and `fig3_shared_contention.png`.

---

## 5. Experimental Findings & Interpretation

1. **Domain-Isolated Workload (Figure 1 & Figure 2)**:
   - When the attacker accesses disjoint private memory (`owners = {1}`) and the victim accesses private memory (`owners = {0}`), TreasureCache's domain-isolated ownership rule completely prevents cross-domain displacement.
   - At capacity 8 (with 2 domains, quota = 4 lines), 4 victim lines remain buffered and 4 are displaced within quota; at capacities 16, 32, and 64, all 8 victim lines remain buffered for **both** TreasureCache and Ada-EHB.
   - **Honest Research Finding**: Under purely domain-isolated traffic, Ada-EHB provides identical security to TreasureCache because TreasureCache's baseline ownership mechanism is already sufficient.
2. **Shared-Memory Contention (Figure 3)**:
   - When blocks have joint ownership (`owners = {0, 1}`, such as shared libraries like `libcrypto.so`), an attacker generating high-volume shared churn forces evictions that are eligible for replacement under the ownership rule.
   - Standard TreasureCache's unweighted LRU displaces victim lines to DRAM (0 / 8 retained).
   - In contrast, Ada-EHB leverages retention scoring ($S=3.0$, $F \ge 1$) and burst rate-limiting to retain victim lines (8 / 8 retained at capacities $\ge 16$).
