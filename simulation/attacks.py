"""
attacks.py - Simulation of Cache Side-Channel Attacks
Models:
  1. Prime+Probe Attack on AES-like table lookup
  2. Evict+Time Attack
  3. Flush+Reload / Flush+Flush Analysis
Evaluates attacker detection accuracy and timing gaps across defense modes.
"""

import random
import numpy as np
from typing import Dict, List, Tuple
from cache_model import MultiCoreCacheSystem


class AESVictimWorkload:
    """
    Simulates a victim cryptographic process accessing a lookup table (e.g. AES S-Box / T-Table).
    Table size: 256 entries * 4 bytes = 1024 bytes (16 cache lines of 64 bytes).
    Base address: 0x100000.
    """
    def __init__(self, base_addr: int = 0x100000):
        self.base_addr = base_addr
        self.num_lines = 16
        self.secret_key = 0xA7

    def get_line_for_byte(self, val: int) -> int:
        return (val >> 4) & 0x0F

    def get_address_for_line(self, line_idx: int) -> int:
        return self.base_addr + (line_idx * 64)

    def execute_encryption_round(self, cache_sys: MultiCoreCacheSystem, plaintext_byte: int) -> int:
        intermediate_val = plaintext_byte ^ self.secret_key
        target_line = self.get_line_for_byte(intermediate_val)
        target_addr = self.get_address_for_line(target_line)
        latency, _ = cache_sys.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)
        return latency


class AttackerPrimeAndProbe:
    """
    Simulates an attacker on Core 1 mounting a Prime+Probe attack
    targeting LLC sets utilized by the victim.
    """
    def __init__(self, target_set_indices: List[int], ways_to_prime: int = 16):
        self.target_sets = target_set_indices
        self.ways_to_prime = ways_to_prime

    def get_eviction_addresses(self, set_idx: int, llc_num_sets: int) -> List[int]:
        addrs = []
        for way in range(self.ways_to_prime):
            # Construct address mapping precisely to set_idx in LLC
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
            # Measure reload time
            lat, _ = cache_sys.read_address(core_id=1, addr=addr, domain_id=1)
            total_latency += lat
            if lat > 60:
                miss_count += 1
        return total_latency, miss_count


def run_prime_and_probe_simulation(mode: str = 'none', rounds: int = 300, thrash_noise: bool = False) -> Dict:
    cache_sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=64)
    victim = AESVictimWorkload()
    attacker = AttackerPrimeAndProbe(target_set_indices=list(range(16)), ways_to_prime=16)

    correct_detections = 0
    victim_latencies = []
    attacker_latencies_on_target = []
    attacker_latencies_on_non_target = []

    for r in range(rounds):
        p_byte = random.randint(0, 255)
        expected_secret_line = victim.get_line_for_byte(p_byte ^ victim.secret_key)
        
        # 1. Attacker primes all 16 candidate sets
        for s in range(16):
            attacker.prime(cache_sys, s)

        # 2. Adversarial Thrashing Injection (if active)
        if thrash_noise:
            # Attacker injects rapid memory traffic across many addresses to overflow EHB
            for noise_idx in range(96):
                noise_addr = 0x800000 + (noise_idx * 64)
                cache_sys.read_address(core_id=1, addr=noise_addr, domain_id=1)

        # 3. Victim executes encryption round
        v_lat = victim.execute_encryption_round(cache_sys, p_byte)
        victim_latencies.append(v_lat)

        # 4. Attacker probes all sets
        probe_results = {}
        for s in range(16):
            total_lat, misses = attacker.probe(cache_sys, s)
            probe_results[s] = total_lat
            if s == expected_secret_line:
                attacker_latencies_on_target.append(total_lat)
            else:
                attacker_latencies_on_non_target.append(total_lat)

        # Candidate chosen by attacker is set with maximum observed latency
        max_val = max(probe_results.values())
        candidates = [k for k, v in probe_results.items() if v == max_val]
        
        # If all sets have identical latency (e.g. all hit in LLC due to defense), attacker must guess randomly
        if len(candidates) == 16:
            predicted_line = random.choice(candidates)
        else:
            predicted_line = random.choice(candidates)

        if predicted_line == expected_secret_line:
            correct_detections += 1

    accuracy = correct_detections / rounds
    return {
        "mode": mode,
        "rounds": rounds,
        "accuracy": accuracy,
        "victim_latencies": victim_latencies,
        "attacker_latencies_target": attacker_latencies_on_target,
        "attacker_latencies_non_target": attacker_latencies_on_non_target,
        "ehb_stats": {
            "hits": cache_sys.ehb.hits if cache_sys.ehb else 0,
            "misses": cache_sys.ehb.misses if cache_sys.ehb else 0,
            "evictions": cache_sys.ehb.evictions if cache_sys.ehb else 0,
        } if cache_sys.ehb else None
    }


def run_evict_and_time_simulation(mode: str = 'none', rounds: int = 200) -> Dict:
    cache_sys = MultiCoreCacheSystem(mode=mode, ehb_capacity=64)
    victim = AESVictimWorkload()
    attacker = AttackerPrimeAndProbe(target_set_indices=[0], ways_to_prime=16)

    evicted_times = []
    non_evicted_times = []

    for r in range(rounds):
        # Pick a byte that maps to set 0
        # (p_byte ^ secret_key) >> 4 == 0  ==>  p_byte ^ secret_key in [0..15]
        p_byte = victim.secret_key ^ random.randint(0, 15)
        
        # Scenario A: Target set is evicted beforehand by attacker
        attacker.prime(cache_sys, 0)
        t_evicted = victim.execute_encryption_round(cache_sys, p_byte)
        evicted_times.append(t_evicted)
        
        # Scenario B: Target line is pre-cached (no eviction)
        # Victim reads once to warm cache
        victim.execute_encryption_round(cache_sys, p_byte)
        t_cached = victim.execute_encryption_round(cache_sys, p_byte)
        non_evicted_times.append(t_cached)

    timing_gap = np.mean(evicted_times) - np.mean(non_evicted_times)
    return {
        "mode": mode,
        "timing_gap": float(timing_gap),
        "mean_evicted_latency": float(np.mean(evicted_times)),
        "mean_cached_latency": float(np.mean(non_evicted_times)),
        "evicted_samples": evicted_times,
        "cached_samples": non_evicted_times
    }
