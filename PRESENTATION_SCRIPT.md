# Master Presentation & Video Explanation Script
## TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks
**Course:** Information Security / Advanced Computer Architecture Capstone  
**Reference Paper:** *Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren* (IEEE Transactions on Dependable and Secure Computing, Sept/Oct 2024)  
**Total Duration:** ~15 Minutes (20 Slides)  
**Speaking Format:** Two Structured Rounds per Team Member  
**Order:** **Kontham Sripadha** (Intro) &rarr; **Sreekar Tirumala** &rarr; **A Venu Vivek** &rarr; **Kontham Sripadha** &rarr; **Sreekar Tirumala** &rarr; **A Venu Vivek**

---

## Executive Speaker Roster & Flow Overview

| Round | Speaker | Roll No. | Core Focus | Slides Covered | Target Time |
| :---: | :--- | :---: | :--- | :---: | :---: |
| **Round 1 (Part 1)** | **Kontham Sripadha** | `CS23I1018` | Introduction, Threat Landscape & Prior Defenses | **Slides 1 – 4** | ~3.0 mins |
| **Round 1 (Part 2)** | **Sreekar Tirumala** | `CS23I1034` | TreasureCache Architecture, Dual Insertion & Formal Proofs | **Slides 5 – 7** | ~2.5 mins |
| **Round 1 (Part 3)** | **A Venu Vivek** | `CS23I1015` | Hardware Feasibility, Gaps in Paper & Proposed Upgrades | **Slides 8 – 10** | ~2.5 mins |
| **Round 2 (Part 1)** | **Kontham Sripadha** | `CS23I1018` | Simulation Testbench, Residency & Latency Benchmarks | **Slides 11 – 13** | ~2.2 mins |
| **Round 2 (Part 2)** | **Sreekar Tirumala** | `CS23I1034` | Shared-Memory Attack Discovery, Attack Suite & Hardware RTL | **Slides 14 – 16** | ~2.5 mins |
| **Round 2 (Part 3)** | **A Venu Vivek** | `CS23I1015` | 20/20 Test Verification, Comparative Matrix & Conclusion | **Slides 17 – 20** | ~2.5 mins |

---

# ROUND 1: Foundations, Architecture, Mathematical Proofs & Critical Flaws

---

### Slide 1: Title & Project Overview
* **Speaker:** Kontham Sripadha (CS23I1018) — *Lead Simulation Engineer*
* **Round:** Round 1 (Opening)
* **Duration:** ~45 Seconds
* **Visual Context on Slide:** Dark Navy executive title slide showing paper metadata, IEEE TDSC citation, course title, and team member cards.

#### Spoken Script ("What to Say"):
> "Good day, Professor and evaluators. Welcome to our capstone presentation. I am Kontham Sripadha, and presenting alongside me are my colleagues, Sreekar Tirumala and A Venu Vivek.
>
> Today, we present an in-depth research analysis, microarchitectural evaluation, and advanced architectural extension of the paper titled *'TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks'*, published in the IEEE Transactions on Dependable and Secure Computing in late 2024 by Mengming Li and his team.
>
> In our project, we did not merely reproduce the paper's findings. We systematically validated its mathematical models, uncovered critical security and performance limitations in shared-memory multi-tenant environments, and engineered next-generation architectural extensions—**Ada-EHB** and **Ada-EHB+**—supported by cycle-accurate simulation, synthesizable Verilog RTL, and formal verification. Let us begin by examining the physical hardware problem that motivates this work."

* **Slide Transition:** *"Moving to Slide 2, let us look at the microarchitectural root cause of cache timing leakage."*

---

### Slide 2: The Root Problem: Memory Hierarchy Timing Disparities
* **Speaker:** Kontham Sripadha (CS23I1018)
* **Round:** Round 1
* **Duration:** ~45 Seconds
* **Visual Context on Slide:** Two structured cards comparing Multi-Level Inclusive Cache Latency Disparities (L1: 4 cyc, L2: 14 cyc, LLC: 40 cyc, DRAM: 200+ cyc) with the Microarchitectural Exploitation Lever.

#### Spoken Script ("What to Say"):
> "On Slide 2, we highlight the fundamental vulnerability at the heart of modern computing. Modern multicore processors utilize a hierarchical cache subsystem: private, ultra-fast L1 and L2 caches dedicated to each core, backed by a large shared Last-Level Cache, or LLC.
>
> To optimize hardware coherence, modern processors enforce an **inclusive cache policy**. This means any cache line present in a core's private L1 or L2 cache *must* also reside in the shared LLC. When an LLC cache set runs out of ways, evicting an LLC line automatically sends a back-invalidation signal to private caches, forcibly evicting the line from private storage.
>
> This creates a massive timing disparity. An LLC hit takes roughly 40 clock cycles, but fetching that data from off-chip DRAM takes over 200 cycles. That 160-cycle difference is what an unprivileged attacker exploits across cores. By evicting a line and observing whether a victim's execution is delayed, the attacker can deduce private memory access patterns and steal secret cryptographic keys."

* **Slide Transition:** *"On Slide 3, we classify the specific attack vectors that exploit this mechanism."*

---

### Slide 3: Threat Model & Side-Channel Attack Taxonomy
* **Speaker:** Kontham Sripadha (CS23I1018)
* **Round:** Round 1
* **Duration:** ~45 Seconds
* **Visual Context on Slide:** Two comparison panels categorizing Conflict-Based Attacks (Prime+Probe, Evict+Time) and Flush-Based Attacks (Flush+Reload, Flush+Flush).

#### Spoken Script ("What to Say"):
> "Turning to Slide 3, microarchitectural side-channel attacks fall into two distinct operational classes based on whether memory is shared.
>
> First, we have **Conflict-Based Attacks**, such as Prime+Probe and Evict+Time. Here, the attacker does not share any virtual address space with the victim. Instead, the attacker primes target LLC sets with conflict addresses. When the victim executes and accesses a conflicting set, the attacker's line is evicted. In the probe phase, measuring the reload latency exposes exactly which cache sets the victim touched.
>
> Second, we have **Flush-Based Attacks**, like Flush+Reload and Flush+Flush. These exploit shared read-only memory, such as shared OpenSSL libraries or memory deduplication in virtualized hypervisors. The attacker executes a `clflush` instruction to invalidate the shared line, waits for the victim to compute, and then reloads the line or times a subsequent flush. If the victim used the data, the reload is fast. If not, it incurs a slow DRAM fetch."

* **Slide Transition:** *"Before evaluating TreasureCache, let us examine why earlier defenses failed to solve this problem."*

---

### Slide 4: Why Existing Hardware Defenses Fall Short
* **Speaker:** Kontham Sripadha (CS23I1018)
* **Round:** Round 1 (Closing for Sripadha)
* **Duration:** ~45 Seconds
* **Visual Context on Slide:** Three vertical cards reviewing Partition-Based Defenses (PLCache/CAT), Randomization-Based Defenses (CEASER/ScatterCache), and Invalidation-Delaying Defenses (SHARP).

#### Spoken Script ("What to Say"):
> "Slide 4 summarizes the state of prior hardware defenses and their shortcomings.
>
> Existing defenses generally take three approaches. **Partitioning schemes**, like Intel CAT or PLCache, statically divide cache ways between security domains. While this prevents cross-core interference, it rigidly fragments cache capacity, severely degrading multi-threaded throughput and wasting up to 50% of LLC space.
>
> **Randomization schemes**, such as CEASER or ScatterCache, dynamically re-map cache set indices using lightweight cryptographic ciphers. However, research has proven that attackers can construct generalized eviction sets using linear algebraic techniques, neutralizing the randomization within seconds.
>
> Finally, **invalidation-delaying mechanisms**, like SHARP, delay back-invalidation signals when an LLC line is evicted. But as we will prove shortly, SHARP only protects on victim LLC evictions and leaves a catastrophic 167-cycle timing leak under advanced multi-step attacks like Prime+Reprime+Probe.
>
> At this point, I will hand over to **Sreekar Tirumala**, who will walk us through TreasureCache's core architecture, its dual insertion logic, and its mathematical foundations."

* **Speaker Handoff:** *"Over to you, Sreekar."*

---

### Slide 5: The TreasureCache Defense Paradigm
* **Speaker:** Sreekar Tirumala (CS23I1034) — *Lead Architectural Analyst*
* **Round:** Round 1
* **Duration:** ~50 Seconds
* **Visual Context on Slide:** Microarchitectural block diagram showing the Eviction-Holding Buffer (EHB) positioned alongside the LLC controller, Fully Associative CAM tags, domain ownership registers, and hit/miss data paths.

#### Spoken Script ("What to Say"):
> "Thank you, Sripadha. 
>
> On Slide 5, we introduce the core philosophy behind TreasureCache. The paper makes a brilliant foundational observation: **cache eviction by itself does not constitute a side-channel leak; the leak occurs only when the victim's subsequent access incurs a high-latency DRAM penalty.**
>
> To eliminate this timing gap without partitioning the entire LLC, TreasureCache inserts a specialized hardware structure called the **Eviction-Holding Buffer**, or **EHB**, located directly adjacent to the LLC controller.
>
> When a victim's cache line is evicted from the LLC due to attacker contention, instead of immediately issuing a back-invalidation signal to private caches, the line is preserved in the EHB. The EHB is a fully associative, Content-Addressable Memory (CAM) buffer with dedicated domain ownership registers.
>
> If the victim core accesses that data again, the request hits the EHB in approximately 40 cycles—identical to an LLC hit. Because the access latency remains flat, the attacker observes zero timing difference and cannot deduce victim behavior."

* **Slide Transition:** *"Now, how does the EHB know when to intercept a line? Slide 6 reveals the dual insertion logic."*

---

### Slide 6: Dual Insertion Logic: Condition 1 vs Condition 2
* **Speaker:** Sreekar Tirumala (CS23I1034)
* **Round:** Round 1
* **Duration:** ~50 Seconds
* **Visual Context on Slide:** Two comparative logic blocks for Condition 1 (Eviction Invalidation) and Condition 2 (Reload Replacement), along with the Constant-Time Flush mechanism.

#### Spoken Script ("What to Say"):
> "Slide 6 covers the most critical technical mechanism in the paper: the **Dual Insertion Invariant**.
>
> Many prior defenses only implemented **Condition 1**: when an LLC set conflicts and evicts a victim-owned line, buffer it in the EHB. But the authors discovered that Condition 1 alone is insufficient. In advanced attacks, an attacker deliberately purges private caches before triggering the victim. When the victim re-fetches the line, the incoming line displaces an existing line from the LLC. If that displaced line is not buffered, a timing channel re-emerges!
>
> Hence, TreasureCache introduces **Condition 2**: when a victim reloads a line from the EHB back into the LLC, the secondary line displaced by this insertion must itself be preserved in the EHB.
>
> Additionally, to neutralize Flush+Flush attacks—which exploit latency variations in the `clflush` instruction—TreasureCache forces all flush operations to complete in a deterministic, constant 70 clock cycles. This simultaneously eliminates both conflict and flush side channels."

* **Slide Transition:** *"Let us examine the formal mathematical proofs supporting this design on Slide 7."*

---

### Slide 7: Mathematical Modeling & Security Boundary Proofs
* **Speaker:** Sreekar Tirumala (CS23I1034)
* **Round:** Round 1 (Closing for Sreekar)
* **Duration:** ~50 Seconds
* **Visual Context on Slide:** Formal mathematical cards detailing Equations (1) through (4), the $k \ge 89$ defense threshold, and the 1000x attack epoch dilation proof.

#### Spoken Script ("What to Say"):
> "Turning to Slide 7, we independently audited and verified the mathematical foundations of TreasureCache using Monte Carlo methods across 50,000 trials.
>
> The paper models the probability of random invalidation $P_i$ as:
> $$P_i = 1 - \left(1 - \frac{1}{S}\right)^g$$
> where $S$ is the number of cache sets and $g$ is the attacker's eviction access count. From this, the expected capacity of evicted lines $c$ follows a binomial distribution with expectation $\lceil g / S \rceil$.
>
> Our formal verification confirmed two critical theoretical guarantees:
> First, to suppress the attacker's True Positive Rate ($\text{TPR}$) below 50% under an 8-way cache, the required buffer threshold is strictly $k \ge 89$. At $k = 64$, the eviction success drops to near zero.
> Second, we proved the **Attack Epoch Dilation Invariant**: to evict a single sensitive cache line, the attacker must expand their memory probing loop from 10,000 cycles to over **9.89 million cycles**—imposing an empirical **1,000-fold slowdown** that makes practical key extraction virtually impossible.
>
> Now, I hand over to **A Venu Vivek**, who will evaluate the silicon feasibility and expose the critical vulnerabilities we discovered in this paper."

* **Speaker Handoff:** *"Over to you, Venu."*

---

### Slide 8: Hardware Realization & Silicon Feasibility
* **Speaker:** A Venu Vivek (CS23I1015) — *Security & Threat Modeling Specialist*
* **Round:** Round 1
* **Duration:** ~45 Seconds
* **Visual Context on Slide:** Silicon metrics panel summarizing TSMC 28nm and 7nm synthesis figures: 78,583 GE, 380 ps CAM search delay, 0.335% area, and 0.028% dynamic power.

#### Spoken Script ("What to Say"):
> "Thank you, Sreekar.
>
> On Slide 8, we examine whether TreasureCache is actually practical in physical hardware. In cache design, the primary concern with CAM buffers is search latency and power consumption.
>
> To verify this, our team modeled the EHB using standard cell libraries for both TSMC 28nm and 7nm nodes. For a standard 64-entry buffer backing a 16MB Last-Level Cache, the total silicon area overhead is only **78,583 Gate Equivalents**, representing less than **0.34%** of total LLC silicon area.
>
> Crucially, the parallel CAM tag search evaluates in just **380 picoseconds**. On a 2.5 GHz clock with a 400 picosecond cycle budget, this guarantees complete single-cycle hit/miss resolution.
>
> Furthermore, because the EHB is positioned at the LLC level, private L1 and L2 caches filter out over 99.9% of memory instructions. The CAM is only accessed on rare LLC evictions and misses, keeping dynamic power overhead under **0.028%**. Silicon feasibility is fully confirmed."

* **Slide Transition:** *"However, as we move to Slide 9, our security audit uncovered critical blind spots in the original paper."*

---

### Slide 9: Gaps & Critical Limitations in TreasureCache
* **Speaker:** A Venu Vivek (CS23I1015)
* **Round:** Round 1
* **Duration:** ~50 Seconds
* **Visual Context on Slide:** Three warning cards detailing: Limitation 1 (Shared-Memory Contention Vulnerability), Limitation 2 (Static Domain Partition Inefficiency), and Limitation 3 (Vulnerability to Algorithmic Thrashing).

#### Spoken Script ("What to Say"):
> "Slide 9 highlights the core academic contribution of our project. Through systematic threat modeling, we discovered three critical limitations in the original TreasureCache publication:
>
> 1. **The Shared-Memory Contention Vulnerability**: TreasureCache relies on domain ownership registers to protect lines. However, modern systems heavily utilize shared shared libraries, such as `libcrypto.so` in OpenSSL. These lines have joint ownership: `owners = {0, 1}`. When an attacker aggressively thrashes shared memory, TreasureCache's unweighted LRU replacement treats victim and attacker accesses equally. As a result, sensitive victim cryptographic lines are evicted all the way to DRAM, dropping victim retention to **0%** and completely reopening the side channel!
>
> 2. **Static Partition Inefficiency**: TreasureCache statically allocates an equal quota of $N/D$ lines per domain. In real-world cloud data centers with asymmetric workloads, this wastes precious buffer space on idle tenants while starving active cryptographic threads.
>
> 3. **Lack of Threat-Aware Invalidation**: The EHB cannot distinguish between legitimate memory bursts and coordinated side-channel eviction sweeps, allowing algorithmic thrashing attacks."

* **Slide Transition:** *"To eliminate these vulnerabilities, we developed our own architectural solutions, shown on Slide 10."*

---

### Slide 10: Proposed Extensions: Ada-EHB & Ada-EHB+ (Ada-EHB 2.0)
* **Speaker:** A Venu Vivek (CS23I1015)
* **Round:** Round 1 (Closing for Venu)
* **Duration:** ~50 Seconds
* **Visual Context on Slide:** Architectural enhancement diagram highlighting Dynamic Retention Scoring $R(k)$, Dynamic Elastic Domain Quota (DEDQ), Sliding-Window Shannon Entropy Profiler, and Multi-Tier Sensitivity Allocation.

#### Spoken Script ("What to Say"):
> "On Slide 10, we present our architectural solutions: **Ada-EHB** and **Ada-EHB+**.
>
> To defeat shared-memory thrashing, Ada-EHB replaces unweighted LRU with a **Dynamic Retention Scoring Engine**. Each candidate line is assigned a score:
> $$R(k) = \alpha \cdot \text{Freq}(k) + \beta \cdot \text{Recency}(k) + \gamma \cdot \text{EntropyScore}(k) + \omega \cdot \text{DomainWeight}(k)$$
> High-entropy, victim-associated lines become 'sticky', completely preventing co-owning attackers from evicting them.
>
> In **Ada-EHB+**, we introduced two further innovations:
> First, **Dynamic Elastic Domain Quota (DEDQ)** with an **Instant Revocation Floor**. Active domains can dynamically borrow unused buffer capacity from idle cores, but if an idle core awakens, its 25% floor is restored instantly.
> Second, a **Sliding-Window Shannon Entropy Profiler** ($W=32$, threshold $H \ge 0.85$) that analyzes memory access patterns in real time, detecting attack eviction sweeps before lines can be displaced.
>
> With our foundational architecture established, I will pass the floor back to **Kontham Sripadha** to kick off Round 2 with our simulation methodology and benchmark results."

* **Speaker Handoff:** *"Back to you, Sripadha."*

---

# ROUND 2: Benchmarking, Breakthrough Results, RTL & Verification

---

### Slide 11: Simulation Methodology & Testbench Architecture
* **Speaker:** Kontham Sripadha (CS23I1018) — *Lead Simulation Engineer*
* **Round:** Round 2 (Opening)
* **Duration:** ~45 Seconds
* **Visual Context on Slide:** Flow diagram of the cycle-accurate Python simulation framework, 5-seed statistical testbench, and Monte Carlo validation engine.

#### Spoken Script ("What to Say"):
> "Thank you, Venu. Welcome to Round 2.
>
> On Slide 11, we detail our experimental testbench architecture. To faithfully evaluate TreasureCache, Ada-EHB, and Ada-EHB+, we implemented a cycle-accurate, microarchitectural cache simulator in Python, modeling multi-level inclusive hierarchies, tag comparisons, and MSHR queues.
>
> Our simulation models:
> - Private L1 data caches: 32KB, 8-way, 4-cycle hit latency.
> - Private L2 caches: 256KB, 8-way, 14-cycle hit latency.
> - Shared Last-Level Cache: 16MB, 16-way associative, 40-cycle hit latency.
> - Off-chip DRAM: 200-cycle minimum penalty.
>
> Every benchmark was executed across **5 independent random seeds** under varying attacker churn intensities (from 32 up to 128 eviction lines). All empirical results were cross-validated against our Monte Carlo formal models to ensure zero statistical bias."

* **Slide Transition:** *"Slide 12 presents our first major benchmark: domain-isolated residency."*

---

### Slide 12: Experimental Results: Domain-Isolated Residency
* **Speaker:** Kontham Sripadha (CS23I1018)
* **Round:** Round 2
* **Duration:** ~45 Seconds
* **Visual Context on Slide:** Embedded **Figure 1** graph showing victim buffer residency across capacities (8, 16, 32, 64) under 128 churn lines, with metric chips (Baseline: 0.0/8, TreasureCache: 8.0/8, Ada-EHB: 8.0/8).

#### Spoken Script ("What to Say"):
> "Slide 12 displays our baseline validation experiment: **Domain-Isolated Buffer Residency** under intense attacker thrashing of 128 lines.
>
> Look at the blue bars on Figure 1: In an unprotected cache, the victim retains **0 out of 8 lines**, suffering 100% eviction.
>
> Now look at TreasureCache and Ada-EHB: At a buffer capacity of 8 lines with two domains, each domain receives a quota of 4 lines. Exactly as the paper predicts, 4 victim lines are protected. As buffer capacity increases to 16, 32, and 64 lines, **both TreasureCache and Ada-EHB achieve a flawless 8.0 out of 8 lines retained (100% residency)**.
>
> This experiment confirms that under strictly private, non-overlapping workloads, TreasureCache's domain ownership mechanism performs exactly as claimed in the IEEE paper."

* **Slide Transition:** *"Now let us observe the corresponding impact on victim access latency on Slide 13."*

---

### Slide 13: Experimental Results: Evict+Time Latency Neutralization
* **Speaker:** Kontham Sripadha (CS23I1018)
* **Round:** Round 2 (Closing for Sripadha)
* **Duration:** ~45 Seconds
* **Visual Context on Slide:** Embedded **Figure 2** violin and bar charts contrasting victim access latency distributions: Unprotected (201.5 cyc, 164.5 cyc delta) vs Protected (40 cyc, 2.0 cyc delta).

#### Spoken Script ("What to Say"):
> "Slide 13 demonstrates the direct defense against Evict+Time attacks.
>
> In the baseline unprotected cache, when an attacker evicts the victim's set, the victim's subsequent memory access is forced to DRAM, registering an average latency of **201.5 clock cycles**. This produces an exploitable timing gap of **164.5 cycles** between cached and evicted states.
>
> With either TreasureCache or Ada-EHB enabled, the evicted victim line is intercepted in the EHB. When the victim accesses the line, it resolves in **40.0 cycles**—identical to an LLC hit. The observable timing difference between an unevicted line and an evicted line collapses to just **2.00 clock cycles**, which is well within microarchitectural jitter and completely unexploitable by an attacker.
>
> Now, I pass the presentation to **Sreekar Tirumala**, who will unveil our breakthrough findings in shared-memory contention and multi-vector attacks."

* **Speaker Handoff:** *"Over to you, Sreekar."*

---

### Slide 14: Critical Finding: Shared-Memory Contention Defense
* **Speaker:** Sreekar Tirumala (CS23I1034) — *Lead Architectural Analyst*
* **Round:** Round 2
* **Duration:** ~50 Seconds
* **Visual Context on Slide:** Embedded **Figure 3** bar chart showing shared contention under 48 churn lines: Baseline (0/8), TreasureCache (0/8), and Ada-EHB (8/8).

#### Spoken Script ("What to Say"):
> "Thank you, Sripadha.
>
> Slide 14 represents the defining empirical discovery of our project. Here, we simulated a realistic cloud environment where both victim and attacker share a common cryptographic library (`owners = {0, 1}`).
>
> Look closely at the center bar on Figure 3: Under 48 lines of shared attacker churn, **TreasureCache's defense completely collapses to 0.0 out of 8 lines retained!** Because the line is owned by both domains, the attacker's eviction traffic generates equal-priority replacement candidates, purging the victim's lines to DRAM and restoring a 201-cycle miss penalty.
>
> In sharp contrast, look at the right bar: **our Ada-EHB maintains a perfect 8.0 out of 8 lines retained (100% residency, 40-cycle latency)**. By dynamically factoring victim access frequency, entropy, and domain weighting into the retention score $R(k)$, Ada-EHB locks sensitive lines into the buffer and prevents adversarial replacement. This directly resolves the critical vulnerability of the original paper."

* **Slide Transition:** *"Next, let us look at how both architectures hold up across the complete attack suite on Slide 15."*

---

### Slide 15: Comprehensive Attack Suite Evaluation
* **Speaker:** Sreekar Tirumala (CS23I1034)
* **Round:** Round 2
* **Duration:** ~50 Seconds
* **Visual Context on Slide:** Embedded **Figure 4** multi-bar chart comparing timing deltas across Flush+Reload, Flush+Flush, Prime+Probe, and Prime+Reprime+Probe (PRP).

#### Spoken Script ("What to Say"):
> "Slide 15 evaluates both architectures against the complete four-vector attack suite across 50 rounds.
>
> In Flush+Reload, Flush+Flush, and Prime+Probe, both TreasureCache and Ada-EHB reduce the baseline 160-cycle timing delta down to a flat 2.0 cycles, successfully neutralizing each attack.
>
> Most importantly, look at the fourth attack: **Prime+Reprime+Probe (PRP)**. We specifically implemented a baseline that used *Condition 1 only* (resembling the SHARP defense). Under PRP, Condition 1 suffered a catastrophic **167.8-cycle timing leak** because it failed to catch the line displaced by the victim's reload.
>
> Both TreasureCache and Ada-EHB enforce **Condition 2 (`from_ehb`)**, capturing the displaced line and reducing the PRP delta to just **2.0 cycles**. This provides rigorous empirical proof for why Condition 2 is mathematically necessary."

* **Slide Transition:** *"Now, let us examine our hardware synthesis results on Slide 16."*

---

### Slide 16: Hardware RTL & TSMC 28nm/7nm Synthesis Breakdown
* **Speaker:** Sreekar Tirumala (CS23I1034)
* **Round:** Round 2 (Closing for Sreekar)
* **Duration:** ~50 Seconds
* **Visual Context on Slide:** Embedded **Figure 5** donut and bar breakdown showing synthesis gate counts (CAM Tag Cells: 42,496 GE; Data RAM: 24,576 GE; Retention ALU: 4,112 GE; Limiter: 1,824 GE; Controller: 5,575 GE).

#### Spoken Script ("What to Say"):
> "On Slide 16, we present the physical hardware synthesis breakdown of our proposed architecture.
>
> We implemented fully synthesizable Verilog RTL for all core subsystems, located in `simulation/rtl/`:
> - `cam_tag_cell.v`: Single-cycle parallel tag comparator.
> - `retention_alu.v`: Hardware pipeline computing the retention score using shift-and-add logic:
>   $$R = (\alpha \ll 2) + (\beta \ll 1) + \gamma + (\omega \ll 3)$$
> - `token_bucket_limiter.v`: Hardware rate limiter defending against algorithmic thrashing.
>
> As shown in Figure 5, the entire 64-entry Ada-EHB subsystem synthesizes to **78,583 Gate Equivalents**. Even with the addition of our Dynamic Retention ALU and Rate Limiter, Ada-EHB adds less than **0.02% additional area** over the baseline TreasureCache design.
>
> I will now hand the presentation back to **A Venu Vivek** to present our formal test verification suite, comparative assessment, and conclusions."

* **Speaker Handoff:** *"Over to you, Venu."*

---

### Slide 17: Master QA Verification Suite: 20/20 Tests Passed
* **Speaker:** A Venu Vivek (CS23I1015) — *Security & Threat Modeling Specialist*
* **Round:** Round 2 (Opening)
* **Duration:** ~40 Seconds
* **Visual Context on Slide:** Verification results table listing core functional, attack mitigation, and hardware verification test cases, all displaying a green `PASSED (100%)` status.

#### Spoken Script ("What to Say"):
> "Thank you, Sreekar.
>
> Slide 17 summarizes our quality assurance and verification methodology. In `simulation/test_advanced_suite.py` and `test_simulation.py`, we created an automated regression suite containing **20 comprehensive unit and verification tests**.
>
> These tests programmatically validate:
> - Basic CAM tag hits, misses, and FIFO/LRU evictions.
> - Dual insertion invariants under both Condition 1 and Condition 2.
> - Timing gap closures across Flush+Reload, Flush+Flush, Prime+Probe, and PRP.
> - Shared-memory retention preservation under adversarial thrashing.
> - Elastic quota borrowing and instant revocation floors in Ada-EHB+.
> - Microarchitectural hardware delay budgets and storage overhead bounds.
>
> All 20 tests pass with 100% success in under 0.04 seconds, confirming complete algorithmic correctness."

* **Slide Transition:** *"Slide 18 provides a comprehensive comparative assessment against state-of-the-art defenses."*

---

### Slide 18: Comprehensive Comparative Assessment
* **Speaker:** A Venu Vivek (CS23I1015)
* **Round:** Round 2
* **Duration:** ~45 Seconds
* **Visual Context on Slide:** Comprehensive trade-off matrix comparing Unprotected Baseline, PLCache, SHARP, TreasureCache, Ada-EHB, and Ada-EHB+ across Security, Performance, Area, and Adaptability.

#### Spoken Script ("What to Say"):
> "Slide 18 places our work in the context of the broader computer architecture landscape.
>
> When we examine prior state-of-the-art defenses:
> - **PLCache** offers security but incurs a severe 15–20% performance penalty due to rigid cache way partitioning.
> - **SHARP** minimizes area overhead but remains vulnerable to Prime+Reprime+Probe attacks because it lacks Condition 2.
> - **TreasureCache** achieves excellent security with zero performance loss under isolated workloads, but fails completely under shared-memory contention.
> - **Ada-EHB and Ada-EHB+** solve all four challenges simultaneously: they provide 100% side-channel defense, preserve full shared-cache utilization, eliminate shared contention vulnerabilities, and adapt dynamically to asymmetric multi-tenant cloud workloads with less than 0.35% silicon overhead."

* **Slide Transition:** *"Now, let us review our team's individual contributions on Slide 19."*

---

### Slide 19: Team Roles & Individual Contributions
* **Speaker:** A Venu Vivek (CS23I1015)
* **Round:** Round 2
* **Duration:** ~30 Seconds
* **Visual Context on Slide:** Three structured author cards detailing the engineering contributions of Sreekar Tirumala, Kontham Sripadha, and A Venu Vivek.

#### Spoken Script ("What to Say"):
> "On Slide 19, we highlight the collaborative efforts of our team:
> - **Sreekar Tirumala (CS23I1034)** served as Lead Architectural Analyst, deriving the mathematical proofs, authoring the synthesizable Verilog RTL for the CAM and Retention ALU, and designing the Ada-EHB+ extension.
> - **Kontham Sripadha (CS23I1018)** served as Lead Simulation Engineer, architecting our cycle-accurate Python testbench, executing multi-seed statistical benchmarks, and generating all publication figures.
> - **I, A Venu Vivek (CS23I1015)**, served as Security and Threat Modeling Specialist, analyzing the side-channel attack vectors, uncovering the shared-memory contention vulnerability, and implementing the 20-test master QA verification suite."

* **Slide Transition:** *"Finally, let us conclude on Slide 20."*

---

### Slide 20: Conclusion, Future Work & Q&A
* **Speaker:** A Venu Vivek (CS23I1015)
* **Round:** Round 2 (Closing for the Team)
* **Duration:** ~40 Seconds
* **Visual Context on Slide:** Executive closing slide summarizing core achievements, future research directions, open-source repository link, and Q&A invitation.

#### Spoken Script ("What to Say"):
> "To conclude on Slide 20:
> Through rigorous analysis, we verified that TreasureCache represents a major milestone in microarchitectural defense by decoupling cache eviction from side-channel leakage.
>
> However, our research demonstrated that domain isolation alone is insufficient in modern systems with shared libraries and asymmetric workloads. Our proposed extensions—**Ada-EHB** and **Ada-EHB+**—successfully bridge this gap, delivering 100% residency under shared thrashing, eliminating timing leaks across all four attack vectors, and maintaining single-cycle hardware feasibility.
>
> All our simulation models, synthesizable RTL, test suites, and documentation are fully open-sourced on GitHub.
>
> On behalf of Sripadha, Sreekar, and myself, thank you for your time. We are now open for your questions."

* **Presentation Conclusion:** *"End of presentation. Invite questions from the evaluators."*

---

## Recording Tips for the Team

1. **Rehearsal & Pace:** Each speaker should speak at a calm, deliberate pace (~130 words per minute). Do not rush through equations or numbers.
2. **Smooth Handoffs:** When handing over, make eye contact with the camera and verbally introduce the next speaker by name (e.g., *"Over to you, Sreekar"* / *"Back to you, Sripadha"*).
3. **Screen Sharing:** Ensure the presentation is in full-screen 16:9 Slide Show mode in Microsoft PowerPoint.
4. **Microphone Setup:** Ensure a quiet environment with minimal room echo so voice audio remains crisp and intelligible.
