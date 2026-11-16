# Project Code Walkthrough & Viva Defense Guide
## TreasureCache & Ada-EHB / Ada-EHB+ Architecture
**Course:** Information Security / Advanced Computer Architecture Capstone  
**Target Audience:** Professor / Evaluator Code Walkthrough & Video Recording  
**Language Level:** Simple, Plain English (No Heavy Jargon)

---

## Quick Summary: The 4 Major Code Segments to Show

When an evaluator asks: *"Show me your code"*, or during your video explanation, **do not try to explain all 2,000 lines of code**. Instead, open VS Code and walk through these **4 major highlights**:

| Highlight | What it Represents | Exact File Path | Exact Lines | Key Concept to Point At |
| :---: | :--- | :--- | :---: | :--- |
| **1** | **TreasureCache Core Defense** | `simulation/cache_model.py` | **Lines 345 – 365** | Dual-Condition Placement: `if self.ehb and (had_sharers or from_ehb):` |
| **2** | **Our Extension (Ada-EHB)** | `simulation/ada_ehb_plus.py` | **Lines 274 – 294** | Retention Score Formula $R(k)$ & Sticky Protection for Secret Keys |
| **3** | **Attack Validation Suite** | `simulation/advanced_attacks.py` | **Lines 373 – 387** | Proof that Condition 1 alone leaks 168 cyc; Condition 2 closes the leak |
| **4** | **Hardware Verilog RTL** | `simulation/rtl/retention_alu.v` | **Lines 123 – 177** | Real hardware ALU using bit-shifts instead of expensive multipliers |

---

# Detailed Walkthrough & Spoken Scripts for Each Code Segment

---

### Highlight 1: The Core TreasureCache Defense (Dual-Condition EHB Placement)

* **File:** `simulation/cache_model.py`
* **Function:** `_evict_llc(self, victim_block, idx, from_ehb)`
* **Exact Line Numbers:** **Lines 345 – 365**

#### What to Show on Screen:
```python
# Lines 345 - 365 in simulation/cache_model.py
def _evict_llc(self, victim_block: int, idx: int, from_ehb: bool):
    """
    Evicts victim_block from LLC set idx.
    Implements TreasureCache Dual-Condition Insertion:
      Condition 1: Line has active private cache sharers (had_sharers == True).
      Condition 2: Line was displaced by an incoming reload from EHB (from_ehb == True).
    """
    entry = self.llc.sets[idx].entries.get(victim_block)
    had_sharers = entry.has_sharers if entry else False

    # CRUCIAL LINE: The dual condition check
    if self.ehb and (had_sharers or from_ehb):
        self.ehb.put(victim_block, owners, current_time=self.cycles)
    else:
        # Unprotected background traffic bypasses directly to slow DRAM
        pass
```

#### What to Say (Plain English Script):
> "Here on **lines 345 to 365 of `cache_model.py`**, you can see the heart of the TreasureCache defense in the `_evict_llc` function.
>
> Look specifically at **line 354**: `if self.ehb and (had_sharers or from_ehb):`
>
> This single line implements the paper's **Dual-Condition Placement**:
> 1. `had_sharers` is **Rule 1**: if an evicted line is actively being used by a private CPU core, it gets saved into the EHB buffer instead of being lost to slow RAM.
> 2. `from_ehb` is **Rule 2**: when a victim pulls data back from the buffer into the cache, that incoming block pushes an existing line out. `from_ehb` catches this second displaced block.
>
> If neither rule matches, the line safely bypasses to RAM. This keeps the buffer small and avoids saving useless background data."

---

### Highlight 2: Our Novel Extension (Ada-EHB Retention Scoring & Sticky Keys)

* **File:** `simulation/ada_ehb_plus.py`
* **Function:** `score(self, entry, current_time)`
* **Exact Line Numbers:** **Lines 274 – 294** (and **Lines 89–92** for sticky property)

#### What to Show on Screen:
```python
# Lines 274 - 294 in simulation/ada_ehb_plus.py
def score(self, entry: BufferEntryPlus, current_time: int) -> float:
    """
    Computes Enhanced Retention Function R+(k):
      R+(k) = [ S(k) * (1 + alpha * F(k)) * (1.5 - EntropyPenalty) ] / ln(1 + Age(k) + epsilon)
    """
    age = max(1, current_time - entry.last_access)
    s_weight = SENSITIVITY_WEIGHTS.get(entry.sensitivity, 1.0) # 5.0 for ROOT_OF_TRUST
    
    entropy_factor = max(0.1, 1.5 - self.profiler.get_entropy_penalty(domain))
    
    # Priority retention formula
    r_plus = (s_weight * (1.0 + self.alpha * entry.frequency) * entropy_factor) / math.log(1.0 + age + self.epsilon)
    
    if entry.low_trust:
        r_plus *= 0.5  # Penalize attacker eviction sweeps
        
    return r_plus
```

#### What to Say (Plain English Script):
> "Next, in **`simulation/ada_ehb_plus.py` on lines 274 to 294**, this is our team's novel contribution that fixes the paper's shared-memory flaw.
>
> In basic TreasureCache, all lines are treated equally. Under shared libraries like OpenSSL, an attacker floods the buffer and kicks out the victim's secret keys.
>
> To fix this, our `score` function calculates a priority score $R(k)$ for every buffer entry. Look at **line 288**:
> - `s_weight` gives sensitive encryption keys top priority (weight of 5.0).
> - `entry.frequency` tracks how often the line is used.
> - `math.log(1 + age)` decays stale lines over time.
>
> Furthermore, on **line 90**, secret keys are marked **sticky**. An attacker's eviction flood cannot displace them, forcing attacker churn to bypass to RAM while keeping victim retention at a perfect 100%."

---

### Highlight 3: Attack Suite & Proving Rule 2 Is Strictly Required

* **File:** `simulation/advanced_attacks.py`
* **Class:** `PrimeReprimeProbeAttack`
* **Exact Line Numbers:** **Lines 373 – 387** and **Lines 495 – 505**

#### What to Show on Screen:
```python
# Lines 373 - 387 in simulation/advanced_attacks.py
if self.cond1_only and sys_obj.ehb is not None:
    # Deliberately ignore from_ehb to model Condition-1-only defenses (like SHARP)
    def _evict_cond1_only(victim_block: int, idx: int, from_ehb: bool):
        entry = sys_obj.llc.sets[idx].entries.get(victim_block)
        had_sharers = entry.has_sharers if entry else False
        if sys_obj.ehb and had_sharers: # <--- ONLY Condition 1 (ignores from_ehb!)
            sys_obj.ehb.put(victim_block, entry.owners)
    sys_obj._evict_llc = _evict_cond1_only
```

#### What to Say (Plain English Script):
> "Here in **`simulation/advanced_attacks.py` on lines 373 to 387**, we empirically tested whether the paper's Rule 2 is actually necessary.
>
> We created a baseline mode called `cond1_only` that deliberately ignores `from_ehb`—resembling older defenses like SHARP.
>
> When we ran the multi-step **Prime+Reprime+Probe** attack:
> - The `cond1_only` defense suffered a massive **167.8-cycle timing leak**, because it failed to catch the line displaced by the victim's reload.
> - But when we re-enabled **Condition 2 (`from_ehb`)**, the timing leak collapsed down to **2.0 cycles**.
>
> This code provides direct proof that Rule 2 is mathematically and physically required to prevent side-channel leakage."

---

### Highlight 4: Synthesizable Verilog Hardware RTL (Fixed-Point ALU)

* **File:** `simulation/rtl/retention_alu.v`
* **Module:** `module retention_alu`
* **Exact Line Numbers:** **Lines 123 – 177**

#### What to Show on Screen:
```verilog
// Lines 123 - 177 in simulation/rtl/retention_alu.v
module retention_alu (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [2:0]  sensitivity,     // 3-bit sensitivity tier
    input  wire [3:0]  freq_count,      // 4-bit access frequency
    input  wire [7:0]  age_cycles,      // Logarithmic age input
    output reg  [7:0]  retention_score, // 8-bit fixed-point retention score
    output reg         score_valid
);

// Lines 160 - 163: Shift-and-add arithmetic avoids hardware multipliers
wire [15:0] raw_product = (weight * (16'd16 + (freq_count << 1))) >> age_decay;
wire [7:0]  computed_score = (raw_product[15:4] > 12'd255) ? 8'hFF : raw_product[11:4];
```

#### What to Say (Plain English Script):
> "Finally, to prove our design is physically buildable in silicon, we wrote synthesizable Verilog hardware code in **`simulation/rtl/retention_alu.v`**.
>
> Look at **line 160**: In real chip design, hardware multipliers and dividers are very slow and consume heavy power.
>
> To avoid this, we implemented our retention scoring formula using **fixed-point shift-and-add logic** (`freq_count << 1`). It computes the 8-bit priority score in just **4 clock cycles** using a tiny 16-entry lookup table.
>
> On TSMC 28-nanometer technology, this entire ALU takes only **4,112 logic gates**, adding less than 5% extra logic over basic TreasureCache while easily operating at 2.5 GHz."

---

## Live Terminal Demo Cheat Sheet (During Viva or Video)

If the evaluator asks you to run the code, run these two commands:

### Command 1: Run All 40 Automated Tests (Takes < 1 second)
```powershell
python -m unittest discover simulation
```
* **Say this:** *"Here, our automated test suite runs all 40 unit and security verification tests in under 1 second, confirming that our CAM searching, dual insertion rules, and attack mitigations pass with 100% success."*

### Command 2: Show the Attack Benchmark Results
```powershell
python simulation/advanced_attacks.py
```
* **Say this:** *"This command executes Flush+Reload, Flush+Flush, Prime+Probe, and Prime+Reprime+Probe across 50 rounds, empirically proving that all timing channels are reduced to a safe 2-cycle gap."*
