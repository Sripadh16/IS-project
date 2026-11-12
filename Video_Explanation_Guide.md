# Video Explanation Guide & Presentation Script
**Course Project Deliverable 4: Research Paper Analysis Presentation**
*Paper: "TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks" (IEEE TDSC 2024 [1])*

---

## 1. Recording Setup & Submission Checklist
According to `IS_ResearchAnalysis_Instructions.pdf` (Rubric Items 4, 6, & 8):
- [ ] **Recording Application**: Zoom, OBS Studio, Microsoft Teams, or Google Meet.
- [ ] **Face Visibility**: Each team member's face and full name must be clearly visible on screen (webcam overlay) while speaking.
- [ ] **Visual Media**: Share the 15-slide PowerPoint deck (`TreasureCache_Presentation.pptx`) and share VS Code / Terminal demonstrating live simulation execution (`python simulation/run_experiments.py`).
- [ ] **Individual Contribution Defense**: Every team member must speak and explain their assigned section.
- [ ] **Target Duration**: Approximately 12 to 16 minutes total (~3 to 4 minutes per member).

---

## 2. Team Role Distribution

| Member | Assigned Role | Slides / Scope Covered | Estimated Time |
| :--- | :--- | :--- | :--- |
| **Kontham Sripadha** | Lead Analyst & Simulation Engineer | Slides 1–2, 10–12 + Live Code Walkthrough (`simulation/`) | 4:30 mins |
| **Team Member 2** | Security & Threat Analyst | Slides 3, 5, 7 (Threat Model, P+P, CT-Flush Waiting Period) | 3:30 mins |
| **Team Member 3** | Architecture Analyst | Slides 4, 6, 11 (Prior Defenses, Dual Placement Policy, Timing Gap) | 3:30 mins |
| **Team Member 4** | Extension & Documentation Lead | Slides 8, 9, 13–15 (Gaps, Ada-EHB Formal Model, Conclusion, Refs) | 4:00 mins |

---

## 3. Slide-by-Slide Speaker Script

### [Slide 1: Title Slide] — *Kontham Sripadha*
> **Spoken Script**:
> "Hello everyone, and welcome. Today our team is presenting our comprehensive research analysis, architectural assessment, and experimental validation of the paper **'TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks'**, published in IEEE Transactions on Dependable and Secure Computing in 2024 by Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren.
> In this presentation, we will examine the root microarchitectural problem of cross-core cache timing channels, evaluate why prior randomized mapping and partitioning defenses incur prohibitive trade-offs, break down TreasureCache's novel philosophy of hiding evictions rather than preventing them, discuss our critical assessment of adversarial buffer thrashing, and demonstrate our independent contribution: Ada-EHB, an adaptive frequency-aware eviction buffer verified through a cycle-calibrated multi-core simulator."

---

### [Slide 2: Memory Hierarchy Timing Disparities] — *Kontham Sripadha*
> **Spoken Script**:
> "Let us examine the root hardware problem. Modern processors implement multi-level cache hierarchies with fast private L1 and L2 caches, and a large shared Last-Level Cache (LLC) connected to main memory DRAM. In x86 and ARM processors, the LLC is inclusive: any line in private caches must also reside in the shared LLC.
> Notice the distinct latency tiers in our modeled architecture: private L1 hits take 4 cycles, private L2 hits take 12 cycles, shared LLC hits take 38 cycles, while DRAM misses take ~200 cycles.
> When an inclusive LLC set fills up, an eviction triggers hardware back-invalidation into private L1 and L2 caches. This creates an unmistakable 160-to-200-cycle timing disparity. An unprivileged attacker sharing the LLC can monitor this timing gap using cycle counters like `rdtsc` to infer secret cryptographic memory lookups during AES, RSA, or SGX enclave execution."

---

### [Slide 3: Threat Model and Attack Taxonomy] — *Team Member 2*
> **Spoken Script**:
> "Thank you, Sripadha. Looking at the threat model: the attacker and victim share physical hardware but run in distinct security domains without administrative privileges. Cache eviction attacks fall into two distinct classes:
> First, conflict-based attacks—specifically **Prime+Probe** and **Evict+Time**. These attacks do NOT require shared memory. In Prime+Probe, the attacker fills target LLC sets with conflict lines. When the victim executes an AES lookup, it evicts an attacker line into DRAM. When the attacker probes the sets, any set with delayed reload latency reveals the secret memory index. Evict+Time works similarly by evicting a set and measuring overall victim execution runtime.
> Second, flush-based attacks—such as **Flush+Reload** and **Flush+Flush**—which DO require shared memory pages (e.g., shared OpenSSL libraries). The attacker executes `clflush` to invalidate shared lines. In Flush+Flush, the attacker exploits the execution time of `clflush` itself, which completes in ~45 cycles on uncached lines versus ~95 cycles on cached lines, generating zero cache misses."

---

### [Slide 4: Why Existing Defenses Fall Short] — *Team Member 3*
> **Spoken Script**:
> "Prior defenses attempted to mitigate these attacks by PREVENTING evictions, but incurred severe penalties.
> Randomized mapping schemes like CEASER and ScatterCache use cryptographic ciphers to dynamically randomize the mapping from addresses to cache sets. However, this places encryption logic directly on the critical memory lookup path, and attackers have demonstrated that statistical profiling over multiple rounds can still reconstruct eviction sets. Furthermore, randomized mapping does not protect against flush attacks.
> On the other hand, strict cache partitioning—such as Intel CAT or DAWG—physically splits cache ways among cores. This causes severe capacity fragmentation, degrading general benchmark performance by 4 to 14 percent, requires OS scheduler modifications, and prevents shared library deduplication. This motivated TreasureCache's new approach."

---

### [Slide 5: The TreasureCache Paradigm] — *Team Member 2*
> **Spoken Script**:
> "This brings us to TreasureCache's central paradigm shift: **'Allow LLC evictions to occur naturally as-is, but eliminate their side-channel utility by hiding exploitable evictions in a tiny buffer!'**
> TreasureCache introduces two tightly integrated mechanisms:
> First, the **Eviction-Hidden Buffer (EHB)**, a specialized fully-associative buffer that captures exploitable evictions and serves hits at ~40 cycles—matching LLC hit latency.
> Second, **Constant-Time Flush (CT-Flush)**, which enforces a predefined waiting period (~70 cycles) even when the requested line is absent.
> Together, these mechanisms require zero OS modifications, no compiler changes, and preserve benchmark performance with under 1.2% overhead in gem5 simulations."

---

### [Slide 6: EHB Architecture & Dual-Condition Placement] — *Team Member 3*
> **Spoken Script**:
> "Slide 6 breaks down the EHB architecture. The buffer capacity is parameterized by the core count and global threshold—modeled as 64 entries (4 KB) in our 2-core setup. An Indexed Fully-Associative architecture is essential to prevent internal set conflicts that an adversary could exploit.
> To prevent a small buffer from overflowing, TreasureCache enforces a dual-condition Secure Placement Policy:
> Condition 1: The evicted block has active copies resident in private L1/L2 caches.
> Condition 2: The evicted block was replaced by a block loaded from the EHB.
> If neither condition is met, the block represents benign background cache churn and bypasses directly to DRAM."

---

### [Slide 7: Secure Replacement Policy & CT-Flush] — *Team Member 2*
> **Spoken Script**:
> "To prevent an attacker from manipulating the buffer itself, TreasureCache implements an ownership-based Secure Replacement Policy. Each security domain is allocated an ownership quota ($Q = \text{Capacity} / N_{\text{domains}}$). Incoming blocks can only displace blocks belonging to the same domain or unowned stale blocks, preventing an attacker from evicting victim lines.
> Furthermore, with CT-Flush, the processor pipeline executes flush operations in constant time using a predefined waiting period (~70 cycles) regardless of cached state. This closes the timing gap that Flush+Flush relies on, allowing shared read-only memory to remain enabled safely."

---

### [Slide 8: Critical Assessment — Established Limitations vs. Hypotheses] — *Team Member 4*
> **Spoken Script**:
> "Now, turning to our team's critical evaluation of the paper: we distinguish between established limitations in published literature and our team's independent research hypothesis.
> The established limitations include CAM dynamic power scaling in multi-core servers, and non-inclusive cache topologies like AMD Zen where LLC evictions do not force private cache invalidations.
> Our team's research hypothesis investigates adversarial shared churn: while the original paper's ownership quota protects against private evictions, what happens when an attacker accesses shared library pages that qualify for the EHB? Under standard unweighted LRU within quotas, rapid shared churn forces premature displacement of sensitive victim lines to DRAM. When the victim re-accesses these displaced lines, it incurs a DRAM miss, reopening the side-channel timing disparity!"

---

### [Slide 9: Proposed Extension — Ada-EHB Formal Specification] — *Team Member 4*
> **Spoken Script**:
> "To eliminate this thrashing vulnerability, our team designed Ada-EHB. Every buffered entry $k$ is assigned a dynamic Retention Score:
> $$R(k) = \frac{S(k) \cdot (1 + \alpha \cdot F(k))}{\ln(1 + \text{Age}(k) + \epsilon)}$$
> where $S(k)$ is a sensitivity weight (3.0 for sensitive lines, 1.0 for normal), $F(k)$ is a 4-bit saturating frequency counter incremented on re-reference, and $\text{Age}(k)$ tracks elapsed cycles.
> When the buffer is full, the hardware evicts the block with the minimum retention score: $\arg\min R(k)$. If all resident entries have higher retention than an incoming non-sensitive candidate, the candidate bypasses directly to DRAM.
> In addition, a token-bucket burst rate-limiter caps non-sensitive churn allocations at 8 burst tokens per domain, requiring only 704 bytes of total metadata overhead."

---

### [Slide 10: Simulation Methodology & Live Code Walkthrough] — *Kontham Sripadha*
> **Spoken Script**:
> *(Demonstrating live execution of `python simulation/run_experiments.py` in terminal)*
> "To validate these findings, we developed a cycle-calibrated multi-core cache simulator in Python.
> As shown in `cache_model.py`, we model private L1/L2 caches, an inclusive 2 MB LLC, DRAM latencies, and hardware back-invalidation.
> In `attacks.py`, the victim executes an AES lookup table workload while the attacker mounts Prime+Probe across 16 sets.
> We evaluated 4 configurations over 5 independent random seeds with 300 rounds each to compute statistical means and standard deviations."

---

### [Slide 11: Experimental Results — Timing Gap Elimination] — *Team Member 3*
> **Spoken Script**:
> "Looking at Slide 11, Figure 1 presents the access latency distributions. On the left, unprotected cache shows an exploitable 197.8-cycle timing gap between cached hits (~38 cycles) and DRAM misses (~200 cycles).
> On the right, under TreasureCache, evicted accesses hit inside the EHB at ~40 cycles. The Evict+Time timing gap collapses from 198 cycles down to just 1.17 +/- 0.02 cycles, completely eliminating the attacker's ability to distinguish an eviction."

---

### [Slide 12: Experimental Results — Attacker Accuracy & Buffer Scaling] — *Team Member 4*
> **Spoken Script**:
> "Slide 12 presents our security and capacity evaluation.
> On the left (Figure 2), Prime+Probe attacker accuracy drops from 100% in unprotected cache to 6.27% +/- 0.83% in partitioned cache and 6.27% +/- 1.48% in Ada-EHB, matching the theoretical random-guess expectation of 6.25% (1 out of 16 sets).
> On the right (Figure 3), under heavy adversarial churn, standard TreasureCache drops to 0% hit ratio at 16 and 32 lines and 66.7% at 64 lines due to LRU displacement. In contrast, Ada-EHB retains 100% hit ratio down to 32 lines and 62.5% at 16 lines through retention scoring and burst rate-limiting."

---

### [Slide 13: Team Member Contributions] — *Kontham Sripadha*
> **Spoken Script**:
> "Slide 13 details our individual contributions:
> Kontham Sripadha served as Lead Simulation Engineer, implementing the cache simulator and benchmarking pipeline;
> Team Member 2 spearheaded threat modeling, attack taxonomy, and CT-Flush analysis;
> Team Member 3 led comparative analysis of prior defenses and inclusive cache invariants;
> And Team Member 4 formulated the Ada-EHB retention score model and compiled the technical documentation."

---

### [Slide 14: Conclusion & Key Takeaways] — *Kontham Sripadha*
> **Spoken Script**:
> "In conclusion, TreasureCache successfully demonstrates that hiding cache evictions is far superior to preventing them, achieving negligible overhead while closing cross-core timing channels.
> Our team identified a critical buffer thrashing vulnerability under shared churn, and our Ada-EHB extension proves that frequency-aware retention scoring effectively shields sensitive buffers.
> Thank you very much for your time!"

---

### [Slide 15: References & Academic Citations] — *Kontham Sripadha*
> **Spoken Script**:
> "Here are the primary academic works cited in our research report and presentation, including the original TreasureCache paper published in IEEE TDSC in 2024, along with foundational prior works across microarchitectural attacks and defenses. We welcome your questions."
