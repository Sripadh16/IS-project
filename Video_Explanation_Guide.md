# Video Explanation Guide & Presentation Script
**Course Project Deliverable 4: Research Paper Analysis Presentation**
*Paper: "TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks" (IEEE TDSC 2024)*

---

## 1. Recording Setup & Submission Checklist
According to `IS_ResearchAnalysis_Instructions.pdf` (Rubric Items 4, 6, & 8):
- [ ] **Recording Tool**: Use Zoom, OBS Studio, Microsoft Teams, or Google Meet.
- [ ] **Face Visibility**: Each team member's face and name must be clearly visible on screen (webcam overlay) while speaking.
- [ ] **Visual Aids**: Share the PowerPoint presentation (`TreasureCache_Presentation.pptx`) and share VS Code / terminal running the simulation code (`simulation/run_experiments.py`).
- [ ] **Individual Defense**: Every team member must speak and explain their assigned section.
- [ ] **Target Duration**: Approximately 12 to 16 minutes total (~3-4 minutes per member).

---

## 2. Team Role Distribution

| Member | Assigned Role | Slides / Scope Covered | Estimated Time |
| :--- | :--- | :--- | :--- |
| **Student A** | Lead Architecture Analyst | Slides 1–2, 4 (Motivation, Inclusive LLC, Prior Work) | 3:30 mins |
| **Student B** | Security & Threat Analyst | Slides 3, 5, 7 (Threat Model, P+P, CT-Flush) | 3:30 mins |
| **Student C** | Simulation & Systems Engineer | Slides 6, 10–12 + Live Code Walkthrough (`simulation/`) | 4:30 mins |
| **Student D** | Extension & Documentation Specialist | Slides 8, 9, 13–14 (Gaps, Ada-EHB, Conclusions) | 3:30 mins |

---

## 3. Slide-by-Slide Speaker Script

### [Slide 1: Title Slide] — *Student A*
> **Spoken Script**:
> "Hello everyone, and welcome. Today our team is presenting our research analysis, critical evaluation, and experimental implementation of the paper **'TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks'**, published in IEEE Transactions on Dependable and Secure Computing in 2024 by Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren.
> In this presentation, we will walk you through the core microarchitectural problem of shared-cache side channels, break down why existing defenses like randomized mapping and way-partitioning fall short, explore TreasureCache's novel paradigm of hiding evictions rather than preventing them, discuss our critical assessment and identified research gaps, and present our own cycle-accurate simulator and proposed architectural extension, Ada-EHB."

---

### [Slide 2: Shared Inclusive LLC Timing Channels] — *Student A*
> **Spoken Script**:
> "Let us start with the root architectural problem. In modern multi-core processors, cores share a large Last-Level Cache (LLC) to maximize throughput. To maintain cache coherence, most x86 and ARM processors enforce cache inclusiveness—meaning any cache line present in private L1 or L2 caches must also be resident in the shared LLC.
> The vulnerability arises when an LLC set becomes full: an eviction in the LLC immediately triggers a hardware back-invalidation signal that forcibly ejects that line from private L1 and L2 caches as well.
> Because an LLC cache hit takes about 38 to 40 cycles, while a main memory DRAM access takes over 200 cycles, there is an unmistakable 160-to-200-cycle timing gap. An unprivileged attacker running on a neighboring core can intentionally monitor this timing disparity using high-resolution cycle counters like `rdtsc` to extract sensitive cryptographic keys from AES, RSA, or secure enclaves."

---

### [Slide 3: Threat Model and Attack Taxonomy] — *Student B*
> **Spoken Script**:
> "Thank you, Student A. Now, looking at the threat model: the attacker and victim share physical hardware but run in separate security domains without special privileges. Cache eviction attacks fundamentally fall into two main categories:
> First, conflict-based attacks—specifically **Prime+Probe** and **Evict+Time**. In Prime+Probe, the attacker fills target LLC sets with its own addresses. When the victim executes a secret-dependent lookup—such as an AES S-Box table lookup—it evicts an attacker line. When the attacker probes those sets, any delayed set reveals the exact cache set the victim accessed. Evict+Time works similarly by evicting a set and measuring the victim's total execution time.
> Second, flush-based attacks—such as **Flush+Reload** and **Flush+Flush**—which exploit shared memory pages (like OpenSSL libraries). The attacker uses the unprivileged `clflush` instruction to invalidate lines. In Flush+Flush, the attacker even exploits the execution timing of `clflush` itself, which executes faster on uncached lines than on cached lines."

---

### [Slide 4: Why Existing Defenses Fall Short] — *Student A*
> **Spoken Script**:
> "Prior defenses attempted to mitigate these attacks by PREVENTING evictions, but they incurred heavy penalties.
> For example, randomized mapping techniques like CEASER and ScatterCache use cryptographic ciphers to dynamically randomize the mapping from addresses to cache sets. However, this introduces high latency onto the critical memory lookup path, and attackers have demonstrated that statistical profiling over multiple rounds can still reconstruct eviction sets.
> On the other hand, strict cache partitioning—such as Intel CAT or DAWG—physically splits cache ways among cores. This causes severe capacity fragmentation, degrading general benchmark performance by 8 to 14 percent, requires OS modifications, and prevents transparent shared libraries. This dilemma motivated the authors to rethink the entire defense philosophy."

---

### [Slide 5: The TreasureCache Paradigm] — *Student B*
> **Spoken Script**:
> "This brings us to TreasureCache's central paradigm shift: **'Don't spend massive hardware complexity trying to prevent evictions; instead, allow LLC evictions to occur naturally, but transparently hide exploitable evictions in a tiny buffer!'**
> TreasureCache introduces two tightly integrated mechanisms:
> First, the **Eviction-Hidden Buffer (EHB)**, a small fully-associative buffer that catches exploitable evictions and serves hits at ~40 cycles—matching LLC hit latency.
> Second, **Constant-Time Flush (CT-Flush)**, which normalizes the execution time of flush instructions to a flat 70 cycles, completely neutralizing Flush+Flush and Flush+Reload.
> Together, these mechanisms require zero OS changes, no compiler rewrites, and maintain normal hardware performance with under 1.2% average overhead."

---

### [Slide 6: Eviction-Hidden Buffer (EHB) Architecture] — *Student C*
> **Spoken Script**:
> "Let's examine how the EHB operates in hardware. The EHB uses an **Indexed Fully-Associative** architecture. A fully-associative structure is essential because set-associative or direct-mapped buffers would introduce internal set-conflicts that an attacker could exploit.
> To prevent a small 64-line buffer from overflowing, TreasureCache uses a **Secure Placement Policy**. Instead of buffering all LLC evictions, it checks cache inclusiveness: it only buffers blocks that have active copies in private L1 or L2 caches. If an evicted block was only resident in the LLC without private cache copies, it is ordinary background traffic and bypasses directly to DRAM.
> When a victim later accesses a block that was evicted from LLC, the lookup hits in the EHB in ~40 cycles, completely concealing the eviction from the attacker."

---

### [Slide 7: Secure Replacement & CT-Flush] — *Student B*
> **Spoken Script**:
> "To prevent an attacker from manipulating the buffer itself, TreasureCache implements a **Secure Replacement Policy**. If the EHB fills up, non-victim lines and stale entries are replaced first, preventing an attacker from intentionally knocking victim lines out of the buffer to create a secondary side channel.
> Furthermore, with **CT-Flush**, the processor pipeline executes flush operations in constant time (~70 cycles) regardless of whether the line was resident in cache or dirty. This closes the timing gap that Flush+Flush relies on, allowing shared read-only memory to remain enabled safely."

---

### [Slide 8: Critical Assessment & Identified Gaps] — *Student D*
> **Spoken Script**:
> "Now, turning to our team's critical evaluation of the paper: while TreasureCache is an impressive architectural achievement, our deep dive identified several unresolved vulnerabilities and restrictive assumptions:
> 1. **Vulnerability to Adversarial Thrashing**: The 64-line buffer is finite. If an attacker runs aggressive memory-streaming loops across multiple cores, they can induce heavy LLC turnover. Under intense pressure, victim lines can be prematurely evicted from the EHB before the victim can reuse them, exposing the DRAM latency gap once again.
> 2. **CAM Scalability and Power Overhead**: Fully-associative CAM structures consume significant dynamic power. Scaling this buffer to 64-core or multi-socket NUMA servers presents thermal and silicon budget challenges.
> 3. **Non-Inclusive Caches**: Modern architectures like AMD Zen utilize non-inclusive cache hierarchies, where LLC evictions do not force private cache invalidations. TreasureCache's placement policy does not directly translate to such designs."

---

### [Slide 9: Proposed Extension: Ada-EHB] — *Student D*
> **Spoken Script**:
> "To solve the buffer thrashing vulnerability, our team designed and modeled an architectural improvement: the **Adaptive Frequency-Aware Eviction-Hidden Buffer (Ada-EHB)**.
> Ada-EHB introduces:
> 1. **Multi-Domain Contention Scoring**: Lines that experience rapid cross-core access turnover between victim and attacker domains receive an elevated sensitivity weight ($W_s = 3.0$).
> 2. **Entropy-Aware Replacement Priority**: Replacement candidates are evaluated using the function $P(k) = S(k) / \ln(1 + \text{Age}(k))$. Sensitive victim blocks obtain 'sticky residency', ensuring they are not displaced by attacker noise loops.
> 3. **Burst Rate Limiting**: Streaming attacker evictions are throttled from entering the buffer.
> In our experiments, Ada-EHB keeps the buffer hit ratio above 85% and maintains attacker accuracy at the random-guess baseline even under active adversarial thrashing."

---

### [Slide 10: Simulation Setup & Live Code Walkthrough] — *Student C*
> **Spoken Script**:
> *(Switch screen share briefly to VS Code / terminal running `python simulation/run_experiments.py`)*
> "To validate these findings, our team implemented a complete cycle-accurate cache simulator in Python.
> As you can see here in `cache_model.py`, we model private L1 caches (32 KB, 4 cycles), private L2 caches (256 KB, 12 cycles), an inclusive 2 MB LLC (16-way, 38 cycles), and DRAM (200 cycles).
> In `attacks.py`, we implement a victim performing AES table lookups and an attacker mounting Prime+Probe and Evict+Time attacks across 300 rounds.
> When we run `python simulation/run_experiments.py`, the simulator executes across 4 configurations: Unprotected LRU, Static Partitioning, Standard TreasureCache, and our Proposed Ada-EHB."

---

### [Slide 11: Experimental Results — Latency Gap] — *Student C*
> **Spoken Script**:
> *(Return to presentation slide 11)*
> "Looking at Slide 11, Figure 1 clearly demonstrates the latency distributions from our simulation.
> On the left, in the unprotected cache, there is a distinct 197.7-cycle timing gap between cached hits (~38 cycles) and DRAM misses (~200 cycles). This is the exact timing gap attackers exploit.
> On the right, under TreasureCache, evicted accesses hit inside the EHB at ~40 cycles. The observable timing gap collapses from 198 cycles down to just 1.0 cycle, completely eliminating the attacker's ability to distinguish an eviction."

---

### [Slide 12: Experimental Results — Attack Success & Buffer Scaling] — *Student D*
> **Spoken Script**:
> "Slide 12 presents our security and capacity results.
> On the left (Figure 2), in the unprotected baseline, the Prime+Probe attacker achieves 100% accuracy in identifying the secret key's cache sets. Both TreasureCache and Ada-EHB slash attacker accuracy to 5.7%–6.0%, right at the theoretical random-guess floor of 6.25% (1 out of 16 sets).
> When we inject adversarial thrashing, standard TreasureCache experiences buffer pressure, but our Ada-EHB successfully preserves victim lines, maintaining accuracy at 5.0%.
> On the right (Figure 3), our capacity scaling analysis shows that Ada-EHB achieves superior hit resilience across all buffer sizes compared to standard EHB."

---

### [Slide 13: Team Member Contributions] — *Student A*
> **Spoken Script**:
> "Slide 13 summarizes the division of responsibilities across our team:
> Student A focused on the microarchitectural analysis of inclusive LLC caches and prior defenses;
> Student B spearheaded the threat model, attack vectors, and CT-Flush analysis;
> Student C engineered the multi-core cache simulator, attack harness, and benchmarking pipeline;
> And Student D designed the Ada-EHB extension and compiled the technical documentation."

---

### [Slide 14: Conclusion & Key Takeaways] — *Student A*
> **Spoken Script**:
> "In conclusion, our study confirms that TreasureCache's paradigm of hiding cache evictions is significantly more efficient than complex eviction-prevention schemes, achieving near-zero performance overhead while defeating cross-core side channels.
> Furthermore, our proposed Ada-EHB extension demonstrates that frequency-aware and sensitivity-based buffer management effectively shields the eviction buffer from adversarial thrashing.
> Thank you very much for your attention. We are now happy to answer any questions!"

---

## 4. Potential Q&A / Defense Preparation
Prepare to answer these questions during live oral examination:
1. **Why does inclusive LLC make side-channel attacks worse than non-inclusive LLC?**
   - *Answer*: Inclusive LLC requires back-invalidating private L1/L2 caches when an LLC line is evicted. This enables cross-core attackers to evict lines from a victim's private L1/L2 without having direct access to private caches.
2. **Why couldn't TreasureCache just use a larger set-associative buffer instead of CAM?**
   - *Answer*: Set-associative buffers have rigid set indexing. An attacker could construct an eviction set specifically for the buffer, re-creating the side channel inside the buffer itself. Fully-associative buffers prevent set conflicts.
3. **What is the primary trade-off of Constant-Time Flush (CT-Flush)?**
   - *Answer*: Uncached lines that normally flush in ~45 cycles now take ~70 cycles. However, `clflush` is infrequently executed in general application code, so the overall system performance degradation is negligible (< 0.2%).

