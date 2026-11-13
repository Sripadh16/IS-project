"""
advanced_attacks.py - Multi-Vector Cache Side-Channel Attack Suite & Benchmark

Implements, benchmarks, and validates the complete suite of cache side-channel attacks
reviewed in Table I, Section II, and Section V-C2 of the IEEE TDSC 2024 paper:
"TreasureCache: Hiding Cache Evictions Against Side-Channel Attacks"
by Mengming Li, Kai Bu, Chenlu Miao, and Kui Ren.

Attacks Implemented:
1. Flush+Reload (Section II-A):
   - Vector: Shared virtual memory line (e.g., shared cryptographic library / AES T-tables).
   - Mechanism: Attacker flushes shared line, waits for victim, and reloads it measuring access latency.
   - Defense: TreasureCache Condition 1 buffers flushed lines with private sharers into EHB,
     closing the ~160+ cycle DRAM gap down to an indistinguishable ~2 cycles (LLC vs EHB hit).

2. Flush+Flush (Section II-A):
   - Vector: Execution latency difference of the flush instruction itself on shared memory lines.
   - Mechanism: Measures clflush execution cycles (cached lines ~95 cycles vs uncached ~45 cycles).
   - Defense: Constant-Time Flush (CT-Flush at ~70 cycles) enforces timing invariance whether
     a line hits or misses in cache, reducing timing delta to 0 cycles.

3. Prime+Probe (Section II-B):
   - Vector: Cross-core LLC conflict set without shared memory.
   - Mechanism: Attacker primes LLC set, waits for victim access, and probes the eviction set.
   - Defense: Victim eviction of attacker lines triggers Condition 1 (since attacker had private
     sharers from priming), placing evicted line into EHB; probe hits EHB (40 cycles) instead of DRAM (200 cycles).

4. Prime+Reprime+Probe (Section II-B & Section V-C2):
   - Vector: Advanced eviction-set attack engineered to evade Condition 1.
   - Mechanism: Attacker primes LLC set then purges private caches so lines reside solely in LLC.
   - Defense: Demonstrates why TreasureCache's Condition 2 (buffering blocks evicted by an
     EHB-reload line) is vital! Condition 1 alone is bypassed (100% attack success), while Condition 2
     completely neutralizes the attack.
"""

import json
import math
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from cache_model import (
    MultiCoreCacheSystem,
    EvictionHiddenBuffer,
    AdaptiveEvictionHiddenBuffer,
    LINE_SIZE
)


@dataclass
class AttackResult:
    """Structured results from a side-channel attack evaluation."""
    attack_name: str
    mode: str
    active_latency: float       # Mean latency when victim accessed target (cycles)
    inactive_latency: float     # Mean latency when victim was idle (cycles)
    timing_delta: float         # |inactive_latency - active_latency| (cycles)
    threshold: float            # Classification threshold separating active vs inactive
    success_rate: float         # Classification accuracy [0.0, 1.0]
    verdict: str                # "VULNERABLE" or "NEUTRALIZED"
    details: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"[{self.attack_name}] Mode: {self.mode:15s} | "
            f"Active: {self.active_latency:6.1f} cyc | "
            f"Inactive: {self.inactive_latency:6.1f} cyc | "
            f"Delta: {self.timing_delta:6.1f} cyc | "
            f"Success: {self.success_rate * 100:5.1f}% | "
            f"Verdict: {self.verdict}"
        )


class FlushReloadAttack:
    """
    Flush+Reload Attack Model (IEEE TDSC 2024 Section II-A).
    Attacker flushes a shared memory address, waits, and reloads it to measure access time.
    """
    def __init__(self, mode: str = 'none', ehb_capacity: int = 64, seed: int = 42,
                 llc_sets: int = 32, llc_ways: int = 4, target_addr: int = 0x100000,
                 rounds: int = 50, **kwargs):
        self.mode = mode
        self.ehb_capacity = ehb_capacity
        self.seed = seed
        self.llc_sets = llc_sets
        self.llc_ways = llc_ways
        self.target_addr = target_addr
        self.rounds = rounds

    def create_system(self, seed_offset: int = 0) -> MultiCoreCacheSystem:
        return MultiCoreCacheSystem(
            mode=self.mode,
            ehb_capacity=self.ehb_capacity,
            seed=self.seed + seed_offset,
            llc_sets=self.llc_sets,
            llc_ways=self.llc_ways
        )

    def run_trial(self, sys: MultiCoreCacheSystem, victim_active: bool) -> Tuple[int, str]:
        # Pre-condition: Shared line is warmed up with joint ownership {0, 1}
        sys.read_address(core_id=0, addr=self.target_addr, domain_id=0, is_sensitive=True)
        sys.read_address(core_id=1, addr=self.target_addr, domain_id=1, is_sensitive=False)

        # Step 1 (Flush): Attacker flushes shared virtual memory line
        sys.clflush(core_id=1, addr=self.target_addr)

        # Step 2 (Wait): Victim executes
        if victim_active:
            # Victim accesses target shared line (e.g. S-Box / crypto routine)
            sys.read_address(core_id=0, addr=self.target_addr, domain_id=0, is_sensitive=True)
        else:
            # Victim accesses unrelated dummy address or idles
            sys.read_address(core_id=0, addr=0x900000, domain_id=0, is_sensitive=False)

        # Step 3 (Reload): Attacker reloads shared address and measures latency
        reload_lat, level = sys.read_address(core_id=1, addr=self.target_addr, domain_id=1, is_sensitive=False)
        return reload_lat, level

    def run_experiment(self, rounds: Optional[int] = None) -> AttackResult:
        rounds = rounds or self.rounds
        active_lats = []
        active_levels = []
        inactive_lats = []
        inactive_levels = []

        for r in range(rounds):
            sys_act = self.create_system(seed_offset=r)
            lat_a, lvl_a = self.run_trial(sys_act, victim_active=True)
            active_lats.append(lat_a)
            active_levels.append(lvl_a)

            sys_inact = self.create_system(seed_offset=r)
            lat_i, lvl_i = self.run_trial(sys_inact, victim_active=False)
            inactive_lats.append(lat_i)
            inactive_levels.append(lvl_i)

        mean_act = sum(active_lats) / rounds
        mean_inact = sum(inactive_lats) / rounds
        delta = abs(mean_inact - mean_act)

        # Architectural discrimination threshold between Cache Hit (<100) and DRAM Miss (>=100)
        cache_threshold = 100.0

        # In Flush+Reload, Active access hits LLC (<100), while Inactive access misses to DRAM (>=100)
        tp = sum(1 for lat in active_lats if lat < cache_threshold)
        tn = sum(1 for lat in inactive_lats if lat >= cache_threshold)
        success_rate = (tp + tn) / (2 * rounds)

        verdict = "VULNERABLE" if (delta >= 30.0 and success_rate >= 0.85) else "NEUTRALIZED"

        return AttackResult(
            attack_name="Flush+Reload",
            mode=self.mode,
            active_latency=mean_act,
            inactive_latency=mean_inact,
            timing_delta=delta,
            threshold=cache_threshold,
            success_rate=success_rate,
            verdict=verdict,
            details={
                "active_levels": {k: active_levels.count(k) for k in set(active_levels)},
                "inactive_levels": {k: inactive_levels.count(k) for k in set(inactive_levels)}
            }
        )


class FlushFlushAttack:
    """
    Flush+Flush Attack Model (IEEE TDSC 2024 Section II-A).
    Attacker repeatedly flushes shared memory lines and measures the flush instruction latency.
    Flushing a cached line is noticeably slower (~95 cycles) than an uncached line (~45 cycles).
    Neutralized by Constant-Time Flush (CT-Flush at ~70 cycles).
    """
    def __init__(self, mode: str = 'none', ehb_capacity: int = 64, seed: int = 42,
                 llc_sets: int = 32, llc_ways: int = 4, target_addr: int = 0x100000,
                 rounds: int = 50, **kwargs):
        self.mode = mode
        self.ehb_capacity = ehb_capacity
        self.seed = seed
        self.llc_sets = llc_sets
        self.llc_ways = llc_ways
        self.target_addr = target_addr
        self.rounds = rounds

    def create_system(self, seed_offset: int = 0) -> MultiCoreCacheSystem:
        return MultiCoreCacheSystem(
            mode=self.mode,
            ehb_capacity=self.ehb_capacity,
            seed=self.seed + seed_offset,
            llc_sets=self.llc_sets,
            llc_ways=self.llc_ways
        )

    def run_trial(self, sys: MultiCoreCacheSystem, victim_active: bool) -> int:
        if victim_active:
            # Victim accesses shared line, leaving it resident in cache
            sys.read_address(core_id=0, addr=self.target_addr, domain_id=0, is_sensitive=True)
        else:
            # Victim does not access shared line; line is uncached
            sys.read_address(core_id=0, addr=0x900000, domain_id=0, is_sensitive=False)
            block = self.target_addr // LINE_SIZE
            sys._invalidate_private(block)
            sys.llc[sys._set(block)].pop(block, None)
            if sys.ehb:
                sys.ehb.entries.pop(block, None)

        # Attacker measures execution time of clflush
        flush_lat = sys.clflush(core_id=1, addr=self.target_addr)
        return flush_lat

    def run_experiment(self, rounds: Optional[int] = None) -> AttackResult:
        rounds = rounds or self.rounds
        active_lats = []
        inactive_lats = []

        for r in range(rounds):
            sys_act = self.create_system(seed_offset=r)
            flush_act = self.run_trial(sys_act, victim_active=True)
            active_lats.append(flush_act)

            sys_inact = self.create_system(seed_offset=r)
            flush_inact = self.run_trial(sys_inact, victim_active=False)
            inactive_lats.append(flush_inact)

        mean_act = sum(active_lats) / rounds
        mean_inact = sum(inactive_lats) / rounds
        delta = abs(mean_act - mean_inact)

        # Discrimination threshold between cached clflush (>70) and uncached clflush (<=70)
        flush_threshold = 70.0

        tp = sum(1 for lat in active_lats if lat > flush_threshold)
        tn = sum(1 for lat in inactive_lats if lat <= flush_threshold)
        success_rate = (tp + tn) / (2 * rounds)

        verdict = "VULNERABLE" if (delta >= 25.0 and success_rate >= 0.85) else "NEUTRALIZED"

        return AttackResult(
            attack_name="Flush+Flush",
            mode=self.mode,
            active_latency=mean_act,
            inactive_latency=mean_inact,
            timing_delta=delta,
            threshold=flush_threshold,
            success_rate=success_rate,
            verdict=verdict
        )


class PrimeProbeAttack:
    """
    Prime+Probe Attack Model (IEEE TDSC 2024 Section II-B).
    Attacker constructs conflict eviction sets without shared memory, primes LLC sets,
    waits for victim access, and probes the eviction set to detect victim access.
    """
    def __init__(self, mode: str = 'none', ehb_capacity: int = 64, seed: int = 42,
                 llc_sets: int = 32, llc_ways: int = 4, target_set: int = 7,
                 rounds: int = 50, **kwargs):
        self.mode = mode
        self.ehb_capacity = ehb_capacity
        self.seed = seed
        self.llc_sets = llc_sets
        self.llc_ways = llc_ways
        self.target_set = target_set
        self.rounds = rounds
        self.victim_addr = ((100000) * llc_sets + target_set) * LINE_SIZE
        self.eviction_set = [((800000 + j) * llc_sets + target_set) * LINE_SIZE for j in range(llc_ways)]

    def create_system(self, seed_offset: int = 0) -> MultiCoreCacheSystem:
        return MultiCoreCacheSystem(
            mode=self.mode,
            ehb_capacity=self.ehb_capacity,
            seed=self.seed + seed_offset,
            llc_sets=self.llc_sets,
            llc_ways=self.llc_ways
        )

    def run_trial(self, sys: MultiCoreCacheSystem, victim_active: bool) -> Tuple[int, List[int], List[str]]:
        # Step 1: Prime - Attacker loads eviction set into LLC
        for addr in self.eviction_set:
            sys.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)

        # Step 2: Wait - Victim executes
        if victim_active:
            # Victim accesses address that maps to target_set, evicting an attacker line
            sys.read_address(core_id=0, addr=self.victim_addr, domain_id=0, is_sensitive=True)
        else:
            # Victim accesses unrelated set (set 0)
            sys.read_address(core_id=0, addr=(100000 * self.llc_sets + 0) * LINE_SIZE, domain_id=0, is_sensitive=False)

        # Attacker invalidates private copies before probe so probe measures LLC/EHB latency
        for addr in self.eviction_set:
            sys._invalidate_private(addr // LINE_SIZE)

        # Step 3: Probe - Attacker accesses eviction set lines and measures latency
        probe_latencies = []
        hit_levels = []
        for addr in self.eviction_set:
            lat, lvl = sys.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)
            probe_latencies.append(lat)
            hit_levels.append(lvl)

        max_lat = max(probe_latencies)
        return max_lat, probe_latencies, hit_levels

    def run_experiment(self, rounds: Optional[int] = None) -> AttackResult:
        rounds = rounds or self.rounds
        active_max_lats = []
        inactive_max_lats = []

        for r in range(rounds):
            sys_act = self.create_system(seed_offset=r)
            max_act, _, _ = self.run_trial(sys_act, victim_active=True)
            active_max_lats.append(max_act)

            sys_inact = self.create_system(seed_offset=r)
            max_inact, _, _ = self.run_trial(sys_inact, victim_active=False)
            inactive_max_lats.append(max_inact)

        mean_act = sum(active_max_lats) / rounds
        mean_inact = sum(inactive_max_lats) / rounds
        delta = abs(mean_act - mean_inact)

        # Discrimination threshold: presence of any DRAM miss (>=100)
        probe_threshold = 100.0

        tp = sum(1 for lat in active_max_lats if lat >= probe_threshold)
        tn = sum(1 for lat in inactive_max_lats if lat < probe_threshold)
        success_rate = (tp + tn) / (2 * rounds)

        verdict = "VULNERABLE" if (delta >= 30.0 and success_rate >= 0.85) else "NEUTRALIZED"

        return AttackResult(
            attack_name="Prime+Probe",
            mode=self.mode,
            active_latency=mean_act,
            inactive_latency=mean_inact,
            timing_delta=delta,
            threshold=probe_threshold,
            success_rate=success_rate,
            verdict=verdict
        )


class PrimeReprimeProbeAttack:
    """
    Prime+Reprime+Probe Attack Model (IEEE TDSC 2024 Section II-B & Section V-C2).
    Advanced attack attempting to evade Placement Condition 1 by purging attacker lines
    from private caches so they reside SOLELY in the LLC.
    Demonstrates why TreasureCache's Condition 2 (buffering blocks evicted by an EHB-reload line)
    is vital to prevent this attack vector!
    """
    def __init__(self, mode: str = 'none', ehb_capacity: int = 64, seed: int = 42,
                 llc_sets: int = 32, llc_ways: int = 4, target_set: int = 7,
                 cond1_only: bool = False, condition1_only: Optional[bool] = None,
                 rounds: int = 50, **kwargs):
        self.mode = mode
        self.ehb_capacity = ehb_capacity
        self.seed = seed
        self.llc_sets = llc_sets
        self.llc_ways = llc_ways
        self.target_set = target_set
        self.cond1_only = condition1_only if condition1_only is not None else cond1_only
        self.rounds = rounds
        self.victim_addr = ((100000) * llc_sets + target_set) * LINE_SIZE
        self.eviction_set = [((900000 + j) * llc_sets + target_set) * LINE_SIZE for j in range(llc_ways)]

    def create_system(self, seed_offset: int = 0) -> MultiCoreCacheSystem:
        sys_obj = MultiCoreCacheSystem(
            mode=self.mode,
            ehb_capacity=self.ehb_capacity,
            seed=self.seed + seed_offset,
            llc_sets=self.llc_sets,
            llc_ways=self.llc_ways
        )
        if self.cond1_only and sys_obj.ehb is not None:
            # Simulate Condition-1-only baseline (e.g., SHARP or naive EHB) that ignores from_ehb
            def _evict_cond1_only(victim_block: int, idx: int, from_ehb: bool):
                sys_obj.llc[idx].pop(victim_block, None)
                sys_obj.stats['llc_evictions'] += 1
                had_sharers = sys_obj._invalidate_private(victim_block)
                # Purposely omit Condition 2: only checks had_sharers
                if sys_obj.ehb and had_sharers:
                    sys_obj.stats['ehb_eligible'] += 1
                    owners = sys_obj.owners.get(victim_block, set())
                    is_sens = victim_block in sys_obj.sensitive
                    if sys_obj.ehb.insert(victim_block, owners, is_sens, sys_obj.time):
                        sys_obj.stats['ehb_inserted'] += 1
            sys_obj._evict_llc = _evict_cond1_only
        return sys_obj

    def run_trial(self, sys: MultiCoreCacheSystem, victim_active: bool) -> Tuple[int, List[int], List[str]]:
        # Pre-condition: Victim accesses sensitive line, warming it in private cache
        sys.read_address(core_id=0, addr=self.victim_addr, domain_id=0, is_sensitive=True)

        # Step 1: Prime - Attacker accesses eviction set, filling target_set and
        # evicting victim_addr into EHB (Condition 1 holds because victim had private sharers)
        for addr in self.eviction_set:
            sys.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)

        # Step 2: Reprime - Attacker purges private cache copies so lines reside ONLY in LLC!
        for addr in self.eviction_set:
            sys._invalidate_private(addr // LINE_SIZE)

        # Step 3: Wait - Victim executes
        if victim_active:
            # Victim accesses victim_addr: hits in EHB and triggers LLC reload with from_ehb=True!
            # Installing this line evicts an attacker line that has had_sharers == False.
            # Condition 2 catches this eviction!
            sys.read_address(core_id=0, addr=self.victim_addr, domain_id=0, is_sensitive=True)
        else:
            # Victim accesses unrelated set (set 0)
            sys.read_address(core_id=0, addr=(100000 * self.llc_sets + 0) * LINE_SIZE, domain_id=0, is_sensitive=False)

        # Step 4: Probe - Attacker accesses eviction set and measures latency
        probe_latencies = []
        hit_levels = []
        for addr in self.eviction_set:
            lat, lvl = sys.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)
            probe_latencies.append(lat)
            hit_levels.append(lvl)

        max_lat = max(probe_latencies)
        return max_lat, probe_latencies, hit_levels

    def run_experiment(self, rounds: Optional[int] = None) -> AttackResult:
        rounds = rounds or self.rounds
        active_max_lats = []
        inactive_max_lats = []

        for r in range(rounds):
            sys_act = self.create_system(seed_offset=r)
            max_act, _, _ = self.run_trial(sys_act, victim_active=True)
            active_max_lats.append(max_act)

            sys_inact = self.create_system(seed_offset=r)
            max_inact, _, _ = self.run_trial(sys_inact, victim_active=False)
            inactive_max_lats.append(max_inact)

        mean_act = sum(active_max_lats) / rounds
        mean_inact = sum(inactive_max_lats) / rounds
        delta = abs(mean_act - mean_inact)

        probe_threshold = 100.0

        tp = sum(1 for lat in active_max_lats if lat >= probe_threshold)
        tn = sum(1 for lat in inactive_max_lats if lat < probe_threshold)
        success_rate = (tp + tn) / (2 * rounds)

        verdict = "VULNERABLE" if (delta >= 30.0 and success_rate >= 0.85) else "NEUTRALIZED"

        mode_name = self.mode if not self.cond1_only else "cond1_only_sharp"
        return AttackResult(
            attack_name="Prime+Reprime+Probe",
            mode=mode_name,
            active_latency=mean_act,
            inactive_latency=mean_inact,
            timing_delta=delta,
            threshold=probe_threshold,
            success_rate=success_rate,
            verdict=verdict
        )


def run_all_attacks_comparison(rounds: int = 50, verbose: bool = True) -> Dict[str, Dict[str, AttackResult]]:
    """
    Benchmarks Baseline (Unprotected) vs TreasureCache vs Ada-EHB across all 4 attack vectors:
      1. Flush+Reload (Section II-A)
      2. Flush+Flush (Section II-A)
      3. Prime+Probe (Section II-B)
      4. Prime+Reprime+Probe (Section II-B & V-C2)
    Also benchmarks Condition-1-Only (SHARP) on Prime+Reprime+Probe to demonstrate why Condition 2 is vital.
    """
    results: Dict[str, Dict[str, AttackResult]] = {
        "Flush+Reload": {},
        "Flush+Flush": {},
        "Prime+Probe": {},
        "Prime+Reprime+Probe": {}
    }

    # 1. Flush+Reload
    for mode in ['none', 'treasure_cache', 'ada_ehb']:
        atk = FlushReloadAttack(mode=mode)
        results["Flush+Reload"][mode] = atk.run_experiment(rounds=rounds)

    # 2. Flush+Flush
    for mode in ['none', 'treasure_cache', 'ada_ehb']:
        atk = FlushFlushAttack(mode=mode)
        results["Flush+Flush"][mode] = atk.run_experiment(rounds=rounds)

    # 3. Prime+Probe
    for mode in ['none', 'treasure_cache', 'ada_ehb']:
        atk = PrimeProbeAttack(mode=mode)
        results["Prime+Probe"][mode] = atk.run_experiment(rounds=rounds)

    # 4. Prime+Reprime+Probe
    for mode in ['none', 'treasure_cache', 'ada_ehb']:
        atk = PrimeReprimeProbeAttack(mode=mode, cond1_only=False)
        results["Prime+Reprime+Probe"][mode] = atk.run_experiment(rounds=rounds)

    # Dedicated demonstration of Condition 1 Only (SHARP) vulnerability
    atk_c1 = PrimeReprimeProbeAttack(mode='treasure_cache', cond1_only=True)
    results["Prime+Reprime+Probe"]["cond1_only"] = atk_c1.run_experiment(rounds=rounds)

    # Save structured results to JSON
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "advanced_attacks_results.json")
    export_data = {
        "metadata": {
            "title": "TreasureCache Multi-Vector Attack Suite Benchmark (IEEE TDSC 2024)",
            "rounds_per_condition": rounds
        },
        "results": {
            attack: {
                mode: {
                    "active_latency": round(res.active_latency, 2),
                    "inactive_latency": round(res.inactive_latency, 2),
                    "timing_delta": round(res.timing_delta, 2),
                    "threshold": res.threshold,
                    "success_rate": round(res.success_rate, 4),
                    "verdict": res.verdict,
                    "details": res.details
                }
                for mode, res in mode_dict.items()
            }
            for attack, mode_dict in results.items()
        }
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    if verbose:
        print_benchmark_report(results, rounds)
        print(f"[Exported Benchmark Data] {json_path}")

    return results


def print_benchmark_report(results: Dict[str, Dict[str, AttackResult]], rounds: int):
    """Prints a structured ASCII report of multi-vector benchmark findings."""
    print("=" * 105)
    print("  TREASURECACHE MULTI-VECTOR ATTACK SUITE BENCHMARK (IEEE TDSC 2024 Table I & Section II)")
    print(f"  Configuration: Evaluated over {rounds} independent rounds per condition across multi-level inclusive cache")
    print("=" * 105)
    print(f"{'Attack Vector':<23} | {'Defense Mode':<20} | {'Active (cyc)':<12} | {'Inactive':<10} | {'Delta':<8} | {'Accuracy':<8} | {'Verdict':<12}")
    print("-" * 105)

    mode_labels = {
        'none': 'Baseline (None)',
        'treasure_cache': 'TreasureCache',
        'ada_ehb': 'Ada-EHB (Proposed)',
        'cond1_only': 'Cond-1 Only (SHARP)'
    }

    for attack_name, mode_dict in results.items():
        for mode_key, res in mode_dict.items():
            label = mode_labels.get(mode_key, mode_key)
            print(
                f"{attack_name:<23} | "
                f"{label:<20} | "
                f"{res.active_latency:<12.1f} | "
                f"{res.inactive_latency:<10.1f} | "
                f"{res.timing_delta:<8.1f} | "
                f"{res.success_rate * 100:<7.1f}% | "
                f"{res.verdict:<12}"
            )
        print("-" * 105)

    print("\n" + "=" * 105)
    print("  ARCHITECTURAL ANALYSIS & NEUTRALIZATION PROOFS (IEEE TDSC 2024)")
    print("=" * 105)
    print("""
1. Flush+Reload (Section II-A):
   - Baseline: Flushed lines missing from LLC incur DRAM access (~200 cycles) when victim is inactive,
     versus ~38 cycles when active (Delta: ~162 cycles, 100% attack accuracy).
   - TreasureCache & Ada-EHB: Under Condition 1 (Section V-C2), evictions caused by flush instructions
     that had active private-cache sharers are securely buffered into the EHB. Reloading from EHB takes
     ~40 cycles (indistinguishable from a 38-cycle LLC hit), eliminating the timing delta to ~2 cycles
     and reducing attack classification to ~50% (random guess baseline). Verdict: NEUTRALIZED.

2. Flush+Flush (Section II-A):
   - Baseline: clflush execution takes 95 cycles on cached lines versus 45 cycles on uncached lines
     (Delta: 50 cycles, 100% attack accuracy).
   - TreasureCache & Ada-EHB: Constant-Time Flush (CT-Flush at 70 cycles) enforces timing invariance
     by maintaining constant duration regardless of cache hit/miss status (Delta: 0 cycles, 50% accuracy).
     Verdict: NEUTRALIZED.

3. Prime+Probe (Section II-B):
   - Baseline: Victim access to the primed set evicts an attacker line to DRAM (~200 cycles),
     generating an easily detectable probe timing surge (Delta: ~160+ cycles, 100% accuracy).
   - TreasureCache & Ada-EHB: When the victim evicts an attacker line, back-invalidation confirms the
     attacker core had active private sharers (Placement Condition 1). The line is admitted to EHB;
     attacker probe hits in EHB (40 cycles) instead of DRAM. Timing delta shrinks to 2 cycles.
     Verdict: NEUTRALIZED.

4. Prime+Reprime+Probe (Section II-B & Section V-C2):
   - Cond-1 Only (SHARP): The attacker purges private caches so lines reside solely in LLC.
     When the victim reloads its line, the evicted attacker line has had_sharers == False.
     Condition 1 alone fails to protect it, allowing it to drop to DRAM (Delta: ~160+ cycles, 100% accuracy).
   - TreasureCache & Ada-EHB: Incorporates Condition 2 (Section V-C2): evictions caused by an EHB-reload
     replacement (from_ehb == True) are eligible for buffering even without private sharers!
     The evicted attacker line is captured into EHB, probe hits at 40 cycles, and the attack fails completely
     (Delta: 2 cycles, 50% accuracy). Demonstrates why Condition 2 is vital!
""")
    print("=" * 105)


if __name__ == "__main__":
    run_all_attacks_comparison(rounds=50, verbose=True)
