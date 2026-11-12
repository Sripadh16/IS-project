"""
attacks.py - Side-Channel Attack Implementations & Thrashing Evaluation
Models:
  1. Prime+Probe Attack on AES-like table lookups (16 cache sets)
  2. Evict+Time Attack measuring victim latency variation
  3. Adversarial Thrashing Campaign targeting the Eviction-Hidden Buffer
  4. Multi-trial statistical analysis with confidence intervals
"""

import random
import numpy as np
from typing import Dict, List, Tuple
from cache_model import MultiCoreCacheSystem


class AESVictimWorkload:
    """
    Simulates a victim cryptographic process accessing a lookup table (e.g., AES S-Box / T-Table).
    Table: 16 cache lines (1024 bytes) mapped to LLC sets 0..15.
    """
    def __init__(self, base_addr: int = 0x100000):
        self.base_addr = base_addr
        self.num_lines = 16
        self.secret_key = 0xA7

    def get_line_for_byte(self, val: int) -> int:
        return (val >> 4) & 0x0F

    def get_address_for_line(self, line_idx: int) -> int:
        return self.base_addr + (line_idx * 64)

    def execute_encryption_round(self, cache_sys: MultiCoreCacheSystem, plaintext_byte: int) -> Tuple[int, str]:
        intermediate_val = plaintext_byte ^ self.secret_key
        target_line = self.get_line_for_byte(intermediate_val)
        target_addr = self.get_address_for_line(target_line)
        latency, hit_level = cache_sys.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)
        return latency, hit_level


class AttackerPrimeAndProbe:
    """
    Simulates an attacker on Core 1 mounting a Prime+Probe attack
    targeting the 16 LLC sets utilized by the victim's cryptographic table.
    """
    def __init__(self, target_set_indices: List[int], ways_to_prime: int = 16):
        self.target_sets = target_set_indices
        self.ways_to_prime = ways_to_prime

    def get_eviction_addresses(self, set_idx: int, llc_num_sets: int) -> List[int]:
        addrs = []
        for way in range(self.ways_to_prime):
            addr = ((way + 10) << (6 + int(np.log2(llc_num_sets)))) | (set_idx << 6)
            addrs.append(addr)
        return addrs

    def prime(self, cache_sys: MultiCoreCacheSystem, set_idx: int):
        addrs = self.get_eviction_addresses(set_idx, cache_sys.llc.num_sets)
        for addr in addrs:
            cache_sys.read_address(core_id=1, addr=addr, domain_id=1)

    def probe(self, cache_sys: MultiCoreCacheSystem, set_idx: int) -> Tuple[int, int]:
        addrs = self.get_eviction_addresses(set_idx, cache_sys.llc.num_sets)
        total_latency = 0
        miss_count = 0
        for addr in addrs:
            lat, _ = cache_sys.read_address(core_id=1, addr=addr, domain_id=1)
            total_latency += lat
            if lat > 60:
                miss_count += 1
        return total_latency, miss_count


def run_prime_and_probe_simulation(mode: str = 'none', rounds: int = 300, thrash_intensity: int = 0, seed: int = 42) -> Dict:
    """
    Runs Prime+Probe campaign across 300 rounds.
    thrash_intensity: Number of adversarial streaming cache lines accessed to overwhelm EHB.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    cache_sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=64)
    victim = AESVictimWorkload()
    attacker = AttackerPrimeAndProbe(target_set_indices=list(range(16)), ways_to_prime=16)

    correct_detections = 0
    victim_latencies = []
    ehb_hits_count = 0
    dram_misses_count = 0

    for r in range(rounds):
        p_byte = random.randint(0, 255)
        expected_secret_line = victim.get_line_for_byte(p_byte ^ victim.secret_key)
        
        # 1. Attacker primes all 16 target sets in LLC
        for s in range(16):
            attacker.prime(cache_sys, s)

        # 2. Adversarial Thrashing Injection:
        # Attacker generates streaming memory accesses to induce massive LLC evictions
        # and overwhelm the EHB buffer.
        if thrash_intensity > 0:
            for noise_idx in range(thrash_intensity):
                noise_addr = 0x900000 + (noise_idx * 64)
                cache_sys.read_address(core_id=1, addr=noise_addr, domain_id=1, is_sensitive=False)

        # 3. Victim executes one encryption round
        v_lat, v_level = victim.execute_encryption_round(cache_sys, p_byte)
        victim_latencies.append(v_lat)
        if v_level == "EHB_HIT":
            ehb_hits_count += 1
        elif v_level == "DRAM_MISS":
            dram_misses_count += 1

        # 4. Attacker probes all 16 sets
        probe_results = {}
        for s in range(16):
            total_lat, misses = attacker.probe(cache_sys, s)
            probe_results[s] = total_lat

        # Attacker selects set with maximum observed latency
        max_val = max(probe_results.values())
        candidates = [k for k, v in probe_results.items() if v == max_val]
        predicted_line = random.choice(candidates)

        if predicted_line == expected_secret_line:
            correct_detections += 1

    accuracy = correct_detections / rounds
    return {
        "mode": mode,
        "rounds": rounds,
        "accuracy": accuracy,
        "victim_latencies": victim_latencies,
        "ehb_hits": ehb_hits_count,
        "dram_misses": dram_misses_count
    }


def run_evict_and_time_simulation(mode: str = 'none', rounds: int = 200, seed: int = 42) -> Dict:
    """
    Evaluates Evict+Time attack measuring victim execution timing gap.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    cache_sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=64)
    victim = AESVictimWorkload()
    attacker = AttackerPrimeAndProbe(target_set_indices=[0], ways_to_prime=16)

    evicted_times = []
    non_evicted_times = []

    for r in range(rounds):
        p_byte = victim.secret_key ^ random.randint(0, 15)
        
        # Scenario A: Target set is evicted beforehand by attacker
        attacker.prime(cache_sys, 0)
        t_evicted, _ = victim.execute_encryption_round(cache_sys, p_byte)
        evicted_times.append(t_evicted)
        
        # Scenario B: Target line is cached (no eviction)
        victim.execute_encryption_round(cache_sys, p_byte)
        t_cached, _ = victim.execute_encryption_round(cache_sys, p_byte)
        non_evicted_times.append(t_cached)

    timing_gap = float(np.mean(evicted_times) - np.mean(non_evicted_times))
    return {
        "mode": mode,
        "timing_gap": timing_gap,
        "mean_evicted": float(np.mean(evicted_times)),
        "mean_cached": float(np.mean(non_evicted_times)),
        "evicted_samples": evicted_times,
        "cached_samples": non_evicted_times
    }


def evaluate_buffer_hit_ratio_under_thrashing(mode: str, capacity: int, thrash_lines: int = 80, trials: int = 100, seed: int = 42) -> float:
    """
    Directly measures EHB hit ratio under adversarial thrashing.
    Simulates a victim with 16 sensitive lines that get displaced from LLC by attacker traffic,
    and measures whether victim re-accesses hit in EHB or miss to DRAM.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    cache_sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=capacity)
    victim = AESVictimWorkload()
    
    ehb_hits = 0
    ehb_misses = 0

    for trial in range(trials):
        # 1. Victim initializes/accesses working set (16 lines)
        for line in range(16):
            addr = victim.get_address_for_line(line)
            cache_sys.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)

        # 2. Attacker causes conflict evictions in LLC for victim lines -> forces into EHB
        for s in range(16):
            for way in range(16):
                addr = ((way + 20) << (6 + 11)) | (s << 6)
                cache_sys.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)

        # 3. Attacker injects heavy thrashing noise traffic
        for n in range(thrash_lines):
            noise_addr = 0x800000 + (n * 64)
            cache_sys.read_address(core_id=1, addr=noise_addr, domain_id=1, is_sensitive=False)

        # 4. Victim re-accesses its 16 working set lines
        for line in range(16):
            addr = victim.get_address_for_line(line)
            lat, level = cache_sys.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
            if level == "EHB_HIT":
                ehb_hits += 1
            elif level == "DRAM_MISS":
                ehb_misses += 1

    total = ehb_hits + ehb_misses
    hit_ratio = (ehb_hits / total * 100.0) if total > 0 else 0.0
    return hit_ratio
