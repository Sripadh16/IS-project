# Master Presentation Script (Concise & Plain English)
## TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks
**Course:** Information Security / Advanced Computer Architecture Capstone  
**Assigned Paper:** *Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren* (IEEE TDSC 2024)  
**Total Target Duration:** 10–12 Minutes (20 Slides)  
**Speaking Format:** Two Quick Rounds per Team Member  
**Speaking Order:** **Kontham Sripadha (Intro)** &rarr; **Sreekar Tirumala** &rarr; **A Venu Vivek** &rarr; **Kontham Sripadha** &rarr; **Sreekar Tirumala** &rarr; **A Venu Vivek**  
**Language Level:** Clear, Plain English — No Heavy Jargon

---

## Quick Reference: 2-Round Speaker Schedule

| Round | Speaker | Roll No. | Topic | Slides | Target Time |
| :---: | :--- | :---: | :--- | :---: | :---: |
| **Round 1 (Part 1)** | **Kontham Sripadha** | `CS23I1018` | Intro, The Timing Problem, Attack Types & Prior Defenses | **Slides 1 – 4** | ~2.5 mins |
| **Round 1 (Part 2)** | **Sreekar Tirumala** | `CS23I1034` | TreasureCache Core Idea, Dual Rules & Math Validation | **Slides 5 – 7** | ~2.0 mins |
| **Round 1 (Part 3)** | **A Venu Vivek** | `CS23I1015` | Hardware Feasibility, The Shared-Memory Flaw & Our Fix | **Slides 8 – 10** | ~2.0 mins |
| **Round 2 (Part 1)** | **Kontham Sripadha** | `CS23I1018` | Simulator Code & Results (Figures 1 & 2) | **Slides 11 – 13** | ~2.0 mins |
| **Round 2 (Part 2)** | **Sreekar Tirumala** | `CS23I1034` | Shared Contention Fix (Figure 3), Attacks (Fig 4) & RTL (Fig 5) | **Slides 14 – 16** | ~2.0 mins |
| **Round 2 (Part 3)** | **A Venu Vivek** | `CS23I1015` | 20/20 Test Suite, Defense Comparison, Team Roles & Closing | **Slides 17 – 20** | ~2.5 mins |

---

# ROUND 1: Paper Overview, The Core Problem & Critical Flaws

---

### Slide 1: Title Slide & Team Introduction
* **Presenter:** Kontham Sripadha (`CS23I1018`)
* **Round:** Round 1 (Opening) | **Target Time:** ~35 Seconds
* **Slide Shows:** Title, course information, and team member cards.

#### Spoken Words:
> "Hello everyone, and welcome to our capstone presentation. I am Kontham Sripadha, presenting alongside Sreekar Tirumala and A Venu Vivek.
>
> Today, we present our research analysis and project implementation of the IEEE 2024 paper: *TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks*.
>
> In this project, we studied how attackers steal secret keys through CPU cache timing, tested the paper's defense, discovered a critical vulnerability when memory is shared, and built our own upgraded defense called **Ada-EHB** to solve it. We will present our work across two quick rounds."

* **Handoff:** *"Let us start on Slide 2 with the basic hardware problem."*

---

### Slide 2: The Root Problem: Cache Timing Differences
* **Presenter:** Kontham Sripadha (`CS23I1018`)
* **Round:** Round 1 | **Target Time:** ~35 Seconds
* **Slide Shows:** Fast Cache (40 cycles) vs. Slow Main Memory (200 cycles).

#### Spoken Words:
> "On Slide 2, here is the core problem. Modern processors have small, fast on-chip caches and large, slow main memory.
>
> Reading data from the cache takes about 40 clock cycles, but fetching it from main memory takes over 200 cycles. That 160-cycle difference is the security hole.
>
> Because multiple CPU cores share the main cache, an attacker can intentionally kick a victim program's secret data out of the cache. If the victim later needs that data, it experiences a noticeable delay. By simply timing how long operations take, an attacker can reconstruct secret encryption keys."

* **Handoff:** *"Slide 3 classifies how attackers exploit this timing gap."*

---

### Slide 3: Types of Cache Timing Attacks
* **Presenter:** Kontham Sripadha (`CS23I1018`)
* **Round:** Round 1 | **Target Time:** ~35 Seconds
* **Slide Shows:** Conflict-based attacks (Prime+Probe) vs. Flush-based attacks (Flush+Reload).

#### Spoken Words:
> "On Slide 3, cache timing attacks fall into two main groups.
>
> First, **Conflict attacks**, like Prime+Probe. Here, the attacker does not share any memory with the victim. The attacker simply fills cache lines with dummy data. When the victim runs, it pushes some attacker data out. The attacker times its own data to see which lines became slow, revealing which cache locations the victim used.
>
> Second, **Flush attacks**, like Flush+Reload. Here, programs share read-only libraries, like OpenSSL. The attacker removes a shared line using a flush instruction, waits for the victim to run, and reloads it to see if it came back fast."

* **Handoff:** *"On Slide 4, let us see why previous defenses were not enough."*

---

### Slide 4: Why Previous Defenses Fall Short
* **Presenter:** Kontham Sripadha (`CS23I1018`)
* **Round:** Round 1 (Closing for Sripadha) | **Target Time:** ~35 Seconds
* **Slide Shows:** Partitioning (wastes space), Randomization (broken by math), Invalidation Delay (leaks in multi-step attacks).

#### Spoken Words:
> "On Slide 4, existing defenses have serious drawbacks:
>
> **Partitioning schemes** split the cache into private slices. While this stops attacks, it wastes 15 to 20% of cache performance because idle cores hold onto empty space that active programs cannot use.
>
> **Randomization schemes** scramble cache addresses, but attackers quickly figure out the pattern using mathematical algorithms.
>
> **Delay schemes**, like SHARP, delay kicking out data, but they fail against multi-step attacks.
>
> Now, Sreekar will explain how TreasureCache solves this problem."

* **Handoff:** *"Over to you, Sreekar."*

---

### Slide 5: TreasureCache Core Idea: Hide Evictions
* **Presenter:** Sreekar Tirumala (`CS23I1034`)
* **Round:** Round 1 | **Target Time:** ~40 Seconds
* **Slide Shows:** The Eviction-Holding Buffer (EHB) catching kicked-out data.

#### Spoken Words:
> "Thank you, Sripadha. On Slide 5, TreasureCache makes a very smart observation: **kicking data out of the cache is not dangerous by itself. The danger only occurs when the victim has to wait 200 cycles for slow main memory.**
>
> So instead of stopping evictions, TreasureCache simply hides them. It adds a small, fast hardware buffer called the **Eviction-Holding Buffer**, or **EHB**, right next to the cache.
>
> When victim data gets kicked out of the cache, it is caught and held in this buffer. If the victim needs that data again, it loads from the buffer in 40 cycles—exactly like a normal cache hit. The attacker sees flat access times and learns nothing."

* **Handoff:** *"Slide 6 explains the rules for saving data."*

---

### Slide 6: Dual Insertion Rules & Fixed-Time Flush
* **Presenter:** Sreekar Tirumala (`CS23I1034`)
* **Round:** Round 1 | **Target Time:** ~40 Seconds
* **Slide Shows:** Rule 1 (Victim Evictions) vs. Rule 2 (Reload Replacements), plus 70-cycle Flush.

#### Spoken Words:
> "Slide 6 shows how the buffer decides what data to store.
>
> **Rule 1** saves victim data that gets pushed out of the cache by an attacker. But Rule 1 alone is not enough. When a victim loads data back from the buffer into the cache, that incoming block pushes an existing line out.
>
> **Rule 2** catches this second displaced block. As we will prove later, Rule 2 is strictly required to stop advanced attacks.
>
> Finally, to stop flush attacks, TreasureCache forces all memory flush commands to take exactly 70 clock cycles, completely removing any timing differences."

* **Handoff:** *"Slide 7 covers our mathematical validation."*

---

### Slide 7: Mathematical Validation & Security Bounds
* **Presenter:** Sreekar Tirumala (`CS23I1034`)
* **Round:** Round 1 (Closing for Sreekar) | **Target Time:** ~40 Seconds
* **Slide Shows:** Equations (1)–(4), the $k \ge 89$ line threshold, and 1,000x attack slowdown.

#### Spoken Words:
> "On Slide 7, we mathematically verified the paper's theoretical model.
>
> The paper proves that for an attacker to have even a 50% chance of evicting victim data, the buffer capacity must be at least **89 lines**.
>
> This forces the attacker to expand their probing loop from 10,000 cycles to nearly **10 million cycles**—a **1,000-times slowdown** that makes practical attacks impossible.
>
> We ran a 50,000-trial random simulation in Python, and our results matched the mathematical model with less than 0.04% error. Now, Venu will cover hardware costs and the major flaw we discovered."

* **Handoff:** *"Over to you, Venu."*

---

### Slide 8: Hardware Feasibility & Silicon Costs
* **Presenter:** A Venu Vivek (`CS23I1015`)
* **Round:** Round 1 | **Target Time:** ~35 Seconds
* **Slide Shows:** 78,583 gates, 380 ps search delay, 0.34% area overhead.

#### Spoken Words:
> "Thank you, Sreekar. On Slide 8, we evaluated whether this hardware can realistically be built in physical silicon chips.
>
> We modeled the design using 28-nanometer chip technology. The entire buffer takes only **78,583 logic gates**, which is less than **0.34%** of the cache silicon area.
>
> It searches for data in just **380 picoseconds**, easily finishing in a single clock cycle at 2.5 GHz.
>
> Furthermore, because small private L1 and L2 caches handle 99% of requests, this buffer is rarely accessed, adding less than **0.03%** to chip power. Hardware feasibility is fully confirmed."

* **Handoff:** *"However, on Slide 9, we found a critical flaw in the paper."*

---

### Slide 9: The Major Flaw: Shared-Memory Contention
* **Presenter:** A Venu Vivek (`CS23I1015`)
* **Round:** Round 1 | **Target Time:** ~40 Seconds
* **Slide Shows:** Joint ownership flaw (`owners={0, 1}`) dropping protection to 0%.

#### Spoken Words:
> "Slide 9 highlights the most important finding of our project. TreasureCache assumes CPU cores run completely separate programs.
>
> But in real-world cloud servers, virtual machines share common software libraries, like OpenSSL. These shared memory lines are co-owned by both victim and attacker.
>
> Because TreasureCache treats all data equally, an attacker can flood the buffer with shared requests and kick out all of the victim's secret keys to slow main memory!
>
> Victim protection collapses from **100% down to 0%**, forcing slow 201-cycle delays that completely reopen the attack!"

* **Handoff:** *"Slide 10 presents our upgraded solutions."*

---

### Slide 10: Our Solution: Ada-EHB & Ada-EHB+
* **Presenter:** A Venu Vivek (`CS23I1015`)
* **Round:** Round 1 (Closing for Venu) | **Target Time:** ~40 Seconds
* **Slide Shows:** Retention Scoring $R(k)$, Elastic Quotas (DEDQ), and Entropy Profiling.

#### Spoken Words:
> "On Slide 10, to solve this problem, our team designed **Ada-EHB** and **Ada-EHB+**.
>
> In **Ada-EHB**, we created a Dynamic Retention Score. Sensitive cryptographic keys receive high scores and become 'sticky'—an attacker cannot kick them out of the buffer. Incoming attacker floods are safely bypassed to RAM.
>
> In **Ada-EHB+**, active programs can dynamically borrow unused buffer space from idle cores, and an address entropy monitor automatically detects attack patterns.
>
> Now, Sripadha will start Round 2 with our code and benchmark results."

* **Handoff:** *"Back to you, Sripadha."*

---

# ROUND 2: Code Walkthrough, Benchmark Results & Conclusion

---

### Slide 11: Simulator Design & Source Code Walkthrough
* **Presenter:** Kontham Sripadha (`CS23I1018`)
* **Round:** Round 2 (Opening) | **Target Time:** ~35 Seconds
* **Slide Shows:** Microarchitectural simulator pipeline and code reference card for `simulation/cache_model.py`.

#### Spoken Words:
> "Welcome to Round 2. On Slide 11, I will walk you through our implementation.
>
> In `simulation/cache_model.py`, we built a cycle-accurate CPU cache simulator in Python. We accurately modeled private L1 and L2 caches, a 16MB shared cache, and off-chip RAM.
>
> In lines 112 to 220 of `cache_model.py`, we implemented the buffer logic, parallel tag matching, and insertion rules. In `run_experiments.py`, we automated tests across 5 independent random seeds and 100 trials to guarantee fair, repeatable results.
>
> Let us look at the observed results on Slide 12."

* **Handoff:** *"Slide 12 shows our first benchmark."*

---

### Slide 12: Benchmark 1: Private Workloads (Figure 1)
* **Presenter:** Kontham Sripadha (`CS23I1018`)
* **Round:** Round 2 | **Target Time:** ~35 Seconds
* **Slide Shows:** Embedded **Figure 1**; Unprotected (0/8 lines) vs. TreasureCache & Ada-EHB (8/8 lines, 100%).

#### Spoken Words:
> "Slide 12 and Figure 1 show our first benchmark when programs do not share memory.
>
> In the unprotected baseline, the victim loses all 8 data lines, suffering 100% eviction to slow main memory.
>
> But with TreasureCache and our Ada-EHB, once buffer capacity reaches 16 lines or higher, **all 8 victim lines are safely retained—achieving 100% protection at 40 cycles**.
>
> This proves that under simple private workloads, TreasureCache works exactly as promised."

* **Handoff:** *"Slide 13 shows how this eliminates timing leaks."*

---

### Slide 13: Benchmark 2: Eliminating Time Leaks (Figure 2)
* **Presenter:** Kontham Sripadha (`CS23I1018`)
* **Round:** Round 2 (Closing for Sripadha) | **Target Time:** ~35 Seconds
* **Slide Shows:** Embedded **Figure 2**; 164.5-cycle time leak collapsed to 2.0 cycles.

#### Spoken Words:
> "Slide 13 and Figure 2 show access latency during an Evict+Time attack.
>
> In an unprotected cache, kicked-out data takes over 201 cycles to load, creating a massive **164.5-cycle timing gap** that leaks secret keys.
>
> With TreasureCache and Ada-EHB, kicked-out data is served from the buffer in just 42 cycles. The timing gap drops from 164 cycles down to just **2 clock cycles**.
>
> That tiny difference is completely hidden within normal hardware noise, neutralizing the attack. Now, Sreekar will present our shared-memory breakthrough."

* **Handoff:** *"Over to you, Sreekar."*

---

### Slide 14: Breakthrough: Shared Memory Defense (Figure 3)
* **Presenter:** Sreekar Tirumala (`CS23I1034`)
* **Round:** Round 2 | **Target Time:** ~40 Seconds
* **Slide Shows:** Embedded **Figure 3**; TreasureCache drops to 0/8 lines (201 cyc), Ada-EHB retains 8/8 lines (40 cyc).

#### Spoken Words:
> "Thank you, Sripadha. Slide 14 and Figure 3 show the central experimental result of our project.
>
> Here, we tested shared libraries. Look at the middle bar on Figure 3: under shared attacker traffic, **TreasureCache completely collapses to 0 out of 8 lines retained!** The victim is forced to fetch from slow RAM at 201 cycles.
>
> Now look at our Ada-EHB on the right: **it keeps all 8 lines safe at 40 cycles**.
>
> In `simulation/ada_ehb_plus.py`, our retention score locks sensitive lines in place, completely solving the paper's biggest vulnerability."

* **Handoff:** *"Slide 15 evaluates all four attack types."*

---

### Slide 15: Attack Suite Code & Results (Figure 4)
* **Presenter:** Sreekar Tirumala (`CS23I1034`)
* **Round:** Round 2 | **Target Time:** ~40 Seconds
* **Slide Shows:** Embedded **Figure 4**; Flush+Reload, Flush+Flush, Prime+Probe, and PRP Condition 2 proof.

#### Spoken Words:
> "On Slide 15 and Figure 4, we tested all 4 attack types across 50 rounds in `simulation/advanced_attacks.py`.
>
> Flush+Reload, Flush+Flush, and Prime+Probe are all reduced to a safe 2-cycle gap.
>
> Crucially, look at the fourth attack: **Prime+Reprime+Probe**. Defenses that only use Rule 1 leak **168 cycles**! Our code proves that **Rule 2 is strictly required** to catch displaced lines and close the leak. Both TreasureCache and Ada-EHB pass this test."

* **Handoff:** *"Slide 16 presents our hardware Verilog implementation."*

---

### Slide 16: Hardware Verilog RTL Implementation (Figure 5)
* **Presenter:** Sreekar Tirumala (`CS23I1034`)
* **Round:** Round 2 (Closing for Sreekar) | **Target Time:** ~40 Seconds
* **Slide Shows:** Embedded **Figure 5**; Verilog RTL files (`cam_tag_cell.v`, `retention_alu.v`), 78,583 gate breakdown.

#### Spoken Words:
> "On Slide 16 and Figure 5, we wrote synthesizable Verilog code for the hardware in `simulation/rtl/`.
>
> We built the search cell in `cam_tag_cell.v`, a rate limiter in `token_bucket_limiter.v`, and the score calculator in `retention_alu.v`.
>
> To keep the hardware fast and simple, we used bit-shifts instead of expensive multipliers, finishing in just 4 clock cycles.
>
> The entire hardware requires **78,583 gates**, adding less than **5% extra logic** over basic TreasureCache. Now over to Venu for testing and conclusion."

* **Handoff:** *"Over to you, Venu."*

---

### Slide 17: Quality Assurance: 20/20 Tests Passed
* **Presenter:** A Venu Vivek (`CS23I1015`)
* **Round:** Round 2 (Opening) | **Target Time:** ~30 Seconds
* **Slide Shows:** 20/20 automated regression tests passing in 0.04s in `simulation/test_advanced_suite.py`.

#### Spoken Words:
> "Thank you, Sreekar. On Slide 17, to prove our code is robust, I built an automated test suite in `simulation/test_advanced_suite.py`.
>
> It runs **20 automated tests in just 0.04 seconds**.
>
> It programmatically verifies tag matching, insertion rules, attack defenses, shared-memory protection, and hardware timing limits. **All 20 tests pass with 100% success**. Every claim we make is directly proven by code."

* **Handoff:** *"Slide 18 compares our system to prior defenses."*

---

### Slide 18: Comparison with Prior Defenses
* **Presenter:** A Venu Vivek (`CS23I1015`)
* **Round:** Round 2 | **Target Time:** ~35 Seconds
* **Slide Shows:** Master trade-off table comparing Baseline, PLCache, SHARP, TreasureCache, and Ada-EHB+.

#### Spoken Words:
> "Slide 18 compares our work against other defenses:
>
> Partitioning schemes like PLCache protect data, but slow down the CPU by up to 20%.
>
> Invalidation-delay schemes like SHARP are cheap, but leak secrets in multi-step attacks.
>
> TreasureCache is fast and secure for private data, but fails when memory is shared.
>
> Our **Ada-EHB and Ada-EHB+** provide complete protection against all attacks, solve the shared memory problem, and adapt elastically to cloud workloads with virtually zero performance loss."

* **Handoff:** *"Slide 19 outlines our individual contributions."*

---

### Slide 19: Team Roles & Individual Contributions
* **Presenter:** A Venu Vivek (`CS23I1015`)
* **Round:** Round 2 | **Target Time:** ~25 Seconds
* **Slide Shows:** Individual contribution cards for Sripadha, Sreekar, and Venu.

#### Spoken Words:
> "On Slide 19, here is how our team divided the work:
>
> **Kontham Sripadha** led the memory timing analysis, built the Python cache simulator, and generated our benchmark charts.
>
> **Sreekar Tirumala** led the architectural analysis, discovered the shared-memory flaw, created Ada-EHB+, and wrote the synthesizable Verilog RTL.
>
> **I, A Venu Vivek**, evaluated silicon feasibility, built the multi-vector attack suite, and engineered the 20-test automated verification suite."

* **Handoff:** *"Finally, let us conclude on Slide 20."*

---

### Slide 20: Conclusion & Defense Q&A
* **Presenter:** A Venu Vivek (`CS23I1015`)
* **Round:** Round 2 (Closing for the Team) | **Target Time:** ~35 Seconds
* **Slide Shows:** Summary bullets, open-source GitHub link, and Q&A invitation.

#### Spoken Words:
> "To conclude on Slide 20:
>
> TreasureCache proves that hiding evictions in a tiny buffer is far better than freezing cache partitions.
>
> However, our project proved that basic TreasureCache fails under shared memory. Our extensions, **Ada-EHB** and **Ada-EHB+**, solve this flaw and provide 100% protection with negligible silicon overhead.
>
> All our code, tests, and documentation are open-sourced on GitHub. Thank you for your time, and we are now happy to answer your questions."

* **Ending:** *"End of presentation. Invite questions from the evaluators."*
