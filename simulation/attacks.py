"""
attacks.py - Attack Models, Workloads, and Controlled Residency Experiments
Models:
  - AES-like victim cryptographic table lookup workload
  - Targeted LLC set eviction with explicit verification
  - Domain-isolated residency trial (verifying TreasureCache ownership protection)
  - Shared-memory contention trial (verifying Ada-EHB retention scoring under shared churn)
  - Matched Evict+Time timing evaluation (comparing control vs post-eviction latencies)
"""

import random
from typing import Dict, List, Optional
from cache_model import MultiCoreCacheSystem, LINE_SIZE


class AESVictimWorkload:
    """
    Simulates a victim cryptographic process accessing a lookup table (e.g., AES S-Box / T-Table).
    Table: 16 cache lines mapped to LLC sets.
    """
    def __init__(self, base_addr: int = 0x100000):
        self.base_addr = base_addr
        self.secret_key = 0xA7

    def get_line_for_byte(self, val: int) -> int:
        return (val >> 4) & 15

    def get_address_for_line(self, line: int) -> int:
        return self.base_addr + line * LINE_SIZE

    def execute_encryption_round(self, sys: MultiCoreCacheSystem, plaintext_byte: int):
        target_line = self.get_line_for_byte(plaintext_byte ^ self.secret_key)
        target_addr = self.get_address_for_line(target_line)
        return sys.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)


def force_llc_eviction(sys: MultiCoreCacheSystem, address: int, domain: int = 1, count: Optional[int] = None) -> bool:
    """
    Evicts address's LLC set with conflicting lines on the attacker core.
    Returns whether the target block was actually evicted from the LLC set.
    """
    block = address // LINE_SIZE
    idx = sys._set(block)
    ways_to_access = count if count is not None else (sys.llc_ways + 2)
    
    for j in range(ways_to_access):
        conflict_block = (100000 + j) * sys.llc_sets + idx
        sys.read_address(core_id=1, addr=conflict_block * LINE_SIZE, domain_id=domain)
        
    return block not in sys.llc[idx]


def run_residency_trial(mode: str, capacity: int, churn: int, seed: int, working_set: int = 8) -> Dict:
    """
    Domain-isolated residency trial:
    Victim owns lines in Domain 0. Attacker generates churn strictly in Domain 1.
    Evaluates whether TreasureCache's domain ownership mechanism successfully isolates
    victim-owned lines from private attacker churn.
    """
    sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=capacity, seed=seed, llc_sets=32, llc_ways=4)
    rng = random.Random(seed)
    victim_addrs = [(0x100000 // LINE_SIZE + i) * LINE_SIZE for i in range(working_set)]
    
    # 1. Victim touches sensitive lines
    for a in victim_addrs:
        sys.read_address(core_id=0, addr=a, domain_id=0, is_sensitive=True)
        
    # 2. Force each victim line out of LLC into EHB using conflict addresses
    for a in victim_addrs:
        force_llc_eviction(sys, a, count=6)
        
    initial_buffered = sum(sys.ehb.contains(a // LINE_SIZE) for a in victim_addrs) if sys.ehb else 0
    
    # 3. Attacker accesses distinct private lines in Domain 1
    for j in range(churn):
        addr = ((200000 + j) * sys.llc_sets + (j % sys.llc_sets)) * LINE_SIZE
        sys.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)
        
    retained = sum(sys.ehb.contains(a // LINE_SIZE) for a in victim_addrs) if sys.ehb else 0
    
    # 4. Probe victim lines and record hit level and latency
    results = []
    for a in victim_addrs:
        lat, level = sys.read_address(core_id=0, addr=a, domain_id=0, is_sensitive=True)
        results.append({'latency': lat, 'level': level})
        
    return {
        'initial_buffered': initial_buffered,
        'retained': retained,
        'working_set': working_set,
        'ehb_hits': sum(r['level'] == 'EHB_HIT' for r in results),
        'dram_misses': sum(r['level'] == 'DRAM_MISS' for r in results),
        'mean_latency': sum(r['latency'] for r in results) / len(results),
        'stats': sys.stats,
        'bypasses': sys.ehb.bypasses if sys.ehb else 0
    }


def run_shared_contention_trial(mode: str, capacity: int, shared_churn: int, seed: int, working_set: int = 8) -> Dict:
    """
    Shared-memory contention trial:
    Models shared library pages (e.g. OpenSSL libcrypto.so) where blocks have joint ownership {0, 1}.
    Victim has hot, sensitive cryptographic table lines (high frequency, sensitive=True).
    Attacker rapidly calls shared utility routines, generating churn on non-sensitive shared blocks.
    Evaluates where Ada-EHB retention scoring and token-bucket rate-limiting protect hot victim
    lines against unweighted LRU displacement in Standard TreasureCache.
    """
    sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=capacity, seed=seed, llc_sets=32, llc_ways=4)
    victim_addrs = [(0x100000 // LINE_SIZE + i) * LINE_SIZE for i in range(working_set)]
    
    # 1. Victim accesses sensitive shared lines multiple times (establishing access frequency)
    for _ in range(3):
        for a in victim_addrs:
            # Shared line owned by Domain 0 and Domain 1
            sys.read_address(core_id=0, addr=a, domain_id=0, is_sensitive=True)
            sys.read_address(core_id=1, addr=a, domain_id=1, is_sensitive=True)
            
    # 2. Force victim lines out of LLC into EHB
    for a in victim_addrs:
        force_llc_eviction(sys, a, count=6)
        
    initial_buffered = sum(sys.ehb.contains(a // LINE_SIZE) for a in victim_addrs) if sys.ehb else 0
    
    # 3. Attacker injects shared non-sensitive churn lines that qualify for EHB insertion
    for j in range(shared_churn):
        shared_churn_addr = ((400000 + j) * sys.llc_sets + (j % sys.llc_sets)) * LINE_SIZE
        # Present in Core 0 (has sharers) and owned by {0, 1}
        sys.read_address(core_id=0, addr=shared_churn_addr, domain_id=0, is_sensitive=False)
        sys.read_address(core_id=1, addr=shared_churn_addr, domain_id=1, is_sensitive=False)
        # Force eviction of shared churn line into EHB
        force_llc_eviction(sys, shared_churn_addr, count=6)
        
    retained = sum(sys.ehb.contains(a // LINE_SIZE) for a in victim_addrs) if sys.ehb else 0
    
    # 4. Probe victim lines
    results = []
    for a in victim_addrs:
        lat, level = sys.read_address(core_id=0, addr=a, domain_id=0, is_sensitive=True)
        results.append({'latency': lat, 'level': level})
        
    return {
        'initial_buffered': initial_buffered,
        'retained': retained,
        'working_set': working_set,
        'ehb_hits': sum(r['level'] == 'EHB_HIT' for r in results),
        'dram_misses': sum(r['level'] == 'DRAM_MISS' for r in results),
        'mean_latency': sum(r['latency'] for r in results) / len(results),
        'stats': sys.stats,
        'bypasses': sys.ehb.bypasses if sys.ehb else 0
    }


def run_evict_and_time_simulation(mode: str = 'none', rounds: int = 50, seed: int = 42, thrash_intensity: int = 0) -> Dict:
    """
    Matched control vs post-eviction victim timing measurement across identical sequences.
    """
    rng = random.Random(seed)
    evicted_times = []
    control_times = []
    levels = []
    
    for i in range(rounds):
        target_addr = 0x100000
        
        # Scenario A: Baseline Control (LLC-resident hit control)
        control_sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=64, seed=seed + i, llc_sets=32, llc_ways=4)
        control_sys.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)
        # Invalidate private copies so the subsequent access tests LLC/EHB hit
        control_sys._invalidate_private(target_addr // LINE_SIZE)
        c_lat, _ = control_sys.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)
        control_times.append(c_lat)
        
        # Scenario B: Target line evicted by attacker, followed by churn
        test_sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=64, seed=seed + i, llc_sets=32, llc_ways=4)
        test_sys.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)
        force_llc_eviction(test_sys, target_addr, count=6)
        
        for j in range(thrash_intensity):
            churn_addr = ((300000 + j) * 32 + (j % 32)) * LINE_SIZE
            test_sys.read_address(core_id=1, addr=churn_addr, domain_id=1, is_sensitive=False)
            
        t_lat, level = test_sys.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)
        evicted_times.append(t_lat)
        levels.append(level)
        
    return {
        'timing_gap': sum(evicted_times) / rounds - sum(control_times) / rounds,
        'mean_evicted': sum(evicted_times) / rounds,
        'mean_cached': sum(control_times) / rounds,
        'evicted_samples': evicted_times,
        'cached_samples': control_times,
        'ehb_hit_fraction': levels.count('EHB_HIT') / rounds,
        'levels': {k: levels.count(k) for k in set(levels)}
    }
