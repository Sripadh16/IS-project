"""
ada_ehb_plus.py - Ada-EHB+ (Ada-EHB 2.0) Next-Generation Cache Architecture Extension

Architectural Motivation:
Standard TreasureCache uses static domain quotas (N_quota = capacity // num_domains)
and uniform LRU replacement. Baseline Ada-EHB introduced dynamic retention scoring R(k),
sticky residency, and a token-bucket rate limiter.
However, in realistic multi-tenant cloud/datacenter environments:
1. Workload Asymmetry & Static Quota Inefficiency:
   Idle cores/domains lock up capacity that active secure cores running cryptographic
   operations desperately need. Static quotas lead to premature victim evictions while
   idle slots sit completely vacant.
2. Eviction-Set Sweeps vs Real Access Locality:
   Attackers traversing eviction sets produce characteristic flat, near-maximum Shannon
   entropy access patterns across addresses. Genuine cryptographic routines (e.g. AES S-box,
   RSA modular exponentiation) or application loops exhibit localized repetition and high temporal/spatial locality.

Key Architectural Mechanisms in Ada-EHB+:
1. Dynamic Elastic Domain Quota (DEDQ):
   - Dynamically allows active secure domains to borrow unused buffer capacity from idle domains
     up to a guaranteed safe ceiling.
   - Enforces an instant revocation floor if a borrowed domain becomes active, immediately restoring
     its guaranteed base quota.
2. Sliding-Window Shannon Entropy Profiler:
   - Tracks access distributions per domain over a sliding window W (e.g. 32 accesses).
   - Detects eviction set sweeps when normalized Shannon entropy H_hat(d) >= threshold (0.85).
   - Churned lines are flagged as low-trust and prioritized for DRAM bypass or rapid eviction.
3. Multi-Tier Sensitivity Levels:
   - Level 0 (NORMAL): Standard data line (S = 1.0)
   - Level 1 (PROTECTED_PAGE): OS/Enclave protected memory page (S = 2.0)
   - Level 2 (ROOT_OF_TRUST): Cryptographic S-box, AES/RSA private keys (S = 5.0 + Sticky)
4. Enhanced Retention Function R+(k):
   R+(k) = [ S(k) * (1 + alpha * F(k)) * (1.5 - EntropyPenalty(domain)) ] / ln(1 + Age(k) + epsilon)
"""

import collections
import math
import os
import sys
import unittest
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, Optional, Set, Tuple, Union

# Ensure simulation directory is in import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache_model import (
    LINE_SIZE,
    EvictionHiddenBuffer,
    AdaptiveEvictionHiddenBuffer,
    MultiCoreCacheSystem,
)
from attacks import force_llc_eviction


class SensitivityLevel(IntEnum):
    """Discrete sensitivity tiers for memory lines."""
    NORMAL = 0          # S = 1.0, Standard data line
    PROTECTED_PAGE = 1  # S = 2.0, OS/Enclave protected memory page
    ROOT_OF_TRUST = 2   # S = 5.0 + Sticky, Cryptographic S-box, AES/RSA private keys


SENSITIVITY_WEIGHTS: Dict[SensitivityLevel, float] = {
    SensitivityLevel.NORMAL: 1.0,
    SensitivityLevel.PROTECTED_PAGE: 2.0,
    SensitivityLevel.ROOT_OF_TRUST: 5.0,
}


@dataclass
class BufferEntryPlus:
    """Represents an entry stored inside Ada-EHB+."""
    address: int
    owners: Set[int]
    sensitivity: SensitivityLevel
    insertion_time: int
    last_access: int
    frequency: int = 1
    low_trust: bool = False
    borrowed_from: Optional[int] = None

    @property
    def sensitive(self) -> bool:
        """Backward compatibility: True if sensitivity is above NORMAL."""
        return self.sensitivity > SensitivityLevel.NORMAL

    @property
    def is_sticky(self) -> bool:
        """Level 2 (ROOT_OF_TRUST) entries have sticky residency."""
        return self.sensitivity == SensitivityLevel.ROOT_OF_TRUST


class ShannonEntropyProfiler:
    """
    Sliding-Window Shannon Entropy Profiler.
    Tracks recent access distributions per domain over a window W (default 32).
    
    Formal Mathematical Formulation:
      H(d) = - sum_{b in window} p_b * log2(p_b)
      H_max = log2(|window|)
      H_hat(d) = H(d) / H_max  in [0.0, 1.0]
      
    When an eviction set sweep with near-maximum entropy (H_hat >= 0.85) is detected,
    it indicates systematic conflict eviction probing.
    """
    def __init__(self, window_size: int = 32, sweep_threshold: float = 0.85):
        self.window_size = window_size
        self.sweep_threshold = sweep_threshold
        self.windows: Dict[int, collections.deque] = collections.defaultdict(
            lambda: collections.deque(maxlen=window_size)
        )
        self.sweep_detected: Dict[int, bool] = collections.defaultdict(bool)

    def record_access(self, domain: int, block_addr: int):
        """Records a block access for domain and updates sweep state."""
        self.windows[domain].append(block_addr)
        self._update_sweep_detection(domain)

    def get_entropy(self, domain: int) -> float:
        """Calculates Shannon entropy H(d) in bits."""
        w = self.windows[domain]
        n = len(w)
        if n < 2:
            return 0.0
        counts = collections.Counter(w)
        entropy = 0.0
        for count in counts.values():
            p = count / n
            entropy -= p * math.log2(p)
        return entropy

    def get_normalized_entropy(self, domain: int) -> float:
        """Calculates normalized Shannon entropy H_hat(d) in [0.0, 1.0]."""
        w = self.windows[domain]
        n = len(w)
        if n < 4:
            return 0.0
        h = self.get_entropy(domain)
        h_max = math.log2(n)
        return h / h_max if h_max > 0 else 0.0

    def _update_sweep_detection(self, domain: int):
        norm_h = self.get_normalized_entropy(domain)
        if len(self.windows[domain]) >= min(16, self.window_size // 2):
            self.sweep_detected[domain] = norm_h >= self.sweep_threshold
        else:
            self.sweep_detected[domain] = False

    def is_sweep_active(self, domain: int) -> bool:
        """Returns whether domain is currently flagged as executing an eviction set sweep."""
        return self.sweep_detected.get(domain, False)

    def get_entropy_penalty(self, domain: int) -> float:
        """
        Returns EntropyPenalty(domain) in [0.0, 1.0].
        - Locality workloads (crypto/standard apps): H_hat <= 0.70 -> penalty = 0.0
        - Flat eviction-set traversal: H_hat >= 0.95 -> penalty = 1.0
        - Linear interpolation for intermediate entropy values.
        """
        norm_h = self.get_normalized_entropy(domain)
        if norm_h <= 0.70:
            return 0.0
        elif norm_h >= 0.95:
            return 1.0
        else:
            return (norm_h - 0.70) / (0.95 - 0.70)


class AdaEHBPlusBuffer(EvictionHiddenBuffer):
    """
    Ada-EHB+ (Ada-EHB 2.0): Next-Generation Adaptive Eviction-Hidden Buffer.
    
    Architectural Enhancements:
    1. Dynamic Elastic Domain Quota (DEDQ):
       - Allows active secure domains to borrow unused capacity from idle domains.
       - Safe ceiling guarantees non-borrowed domains retain reserved capacity.
       - Instant revocation floor immediately evicts excess borrowed lines if the idle domain wakes.
    2. Sliding-Window Shannon Entropy Profiler:
       - Detects flat, near-maximum entropy eviction-set sweeps.
       - Flags attacker churn as low-trust and prioritizes for DRAM bypass or rapid replacement.
    3. Multi-Tier Sensitivity Levels:
       - Level 0 (NORMAL): S = 1.0
       - Level 1 (PROTECTED_PAGE): S = 2.0
       - Level 2 (ROOT_OF_TRUST): S = 5.0 + Sticky Residency
    4. Enhanced Retention Function:
       R+(k) = [ S(k) * (1 + alpha * F(k)) * (1.5 - EntropyPenalty(domain)) ] / ln(1 + Age(k) + epsilon)
    5. Token-Bucket Rate Limiter:
       - 8 tokens per domain, refilling at 1 token per 125 cycles for non-sensitive bursts.
    """
    def __init__(
        self,
        capacity_lines: int = 64,
        hit_latency: int = 40,
        num_domains: int = 3,
        window_size: int = 32,
        idle_timeout: int = 500
    ):
        super().__init__(capacity_lines, hit_latency, num_domains)
        self.capacity = capacity_lines
        self.hit_latency = hit_latency
        self.num_domains = num_domains
        self.base_floor = max(1, capacity_lines // num_domains)
        self.idle_timeout = idle_timeout
        
        # Scoring parameters
        self.alpha = 0.2
        self.epsilon = 1e-5
        
        # Operational state
        self.entries: Dict[int, BufferEntryPlus] = {}
        self.last_domain_activity: Dict[int, int] = {d: 0 for d in range(num_domains)}
        self.secure_domains: Set[int] = set()
        
        # Entropy profiler
        self.profiler = ShannonEntropyProfiler(window_size=window_size, sweep_threshold=0.85)
        
        # Token-bucket rate limiting
        self.tokens: Dict[int, float] = {d: 8.0 for d in range(num_domains)}
        self.updated: Dict[int, int] = {d: 0 for d in range(num_domains)}
        self.max_tokens = 8.0
        self.refill_rate = 1.0 / 125.0
        
        # Extended telemetry
        self.revocations = 0
        self.sweep_bypasses = 0
        self.borrowed_insertions = 0

    def record_access(self, domain: int, block_addr: int, current_time: int):
        """Records an access for entropy profiling and activity tracking."""
        self.last_domain_activity[domain] = current_time
        self.profiler.record_access(domain, block_addr)

    def is_domain_idle(self, domain: int, current_time: int) -> bool:
        """Determines whether a domain is currently idle (0 occupancy and inactive)."""
        occ = self.get_domain_occupancy(domain)
        if occ > 0:
            return False
        last_t = self.last_domain_activity.get(domain, 0)
        return (last_t == 0) or ((current_time - last_t) >= self.idle_timeout)

    def get_domain_occupancy(self, domain: int) -> int:
        """Returns the number of entries owned by domain."""
        return sum(domain in e.owners for e in self.entries.values())

    def get_elastic_quota(self, domain: int, current_time: int) -> int:
        """
        Calculates the Dynamic Elastic Domain Quota (DEDQ) for domain.
        - Active secure domains can borrow unused capacity from idle domains up to safe ceiling.
        - Non-secure / untrusted domains are restricted to base floor.
        """
        if domain not in self.secure_domains:
            return self.base_floor
            
        idle_domains = [
            d for d in range(self.num_domains)
            if d != domain and self.is_domain_idle(d, current_time)
        ]
        
        available_borrowed = sum(
            max(0, self.base_floor - self.get_domain_occupancy(d))
            for d in idle_domains
        )
        
        # Safe ceiling: preserve base floor for all non-idle domains
        active_domains_floor = sum(
            self.base_floor for d in range(self.num_domains)
            if d != domain and d not in idle_domains
        )
        ceiling = max(self.base_floor, self.capacity - active_domains_floor)
        elastic_quota = min(ceiling, self.base_floor + available_borrowed)
        return elastic_quota

    def score(self, entry: BufferEntryPlus, current_time: int) -> float:
        """
        Computes the Enhanced Retention Function R+(k):
          R+(k) = [ S(k) * (1 + alpha * F(k)) * (1.5 - EntropyPenalty(domain)) ] / ln(1 + Age(k) + epsilon)
        """
        age = max(1, current_time - entry.last_access)
        s_weight = SENSITIVITY_WEIGHTS.get(entry.sensitivity, 1.0)
        
        if entry.owners:
            penalty = max(self.profiler.get_entropy_penalty(d) for d in entry.owners)
        else:
            penalty = 0.0
            
        entropy_factor = max(0.1, 1.5 - penalty)
        r_plus = (s_weight * (1.0 + self.alpha * entry.frequency) * entropy_factor) / math.log(1.0 + age + self.epsilon)
        
        # Penalize entries flagged as low-trust from eviction sweeps
        if entry.low_trust:
            r_plus *= 0.5
            
        return r_plus

    def take(self, block_addr: int, current_time: int) -> Optional[BufferEntryPlus]:
        """Retrieves and removes entry on hit (EHB reload into LLC)."""
        entry = self.entries.pop(block_addr, None)
        if entry is None:
            self.misses += 1
        else:
            self.hits += 1
            entry.last_access = current_time
            if entry.frequency < 15:
                entry.frequency += 1
        return entry

    def insert(
        self,
        block_addr: int,
        owners: Set[int],
        sensitivity: Union[SensitivityLevel, int, bool],
        current_time: int
    ) -> bool:
        """
        Inserts block into Ada-EHB+ enforcing DEDQ, Multi-Tier Sticky Residency,
        and Entropy-Aware Replacement.
        """
        owners = set(owners)
        if not owners or self.capacity == 0:
            self.bypasses += 1
            return False

        # Convert sensitivity to SensitivityLevel enum
        if isinstance(sensitivity, bool):
            sens_level = SensitivityLevel.ROOT_OF_TRUST if sensitivity else SensitivityLevel.NORMAL
        elif isinstance(sensitivity, int):
            sens_level = SensitivityLevel(sensitivity)
        else:
            sens_level = sensitivity

        # Update domain activity & register secure domains
        for d in owners:
            self.last_domain_activity[d] = current_time
            if sens_level > SensitivityLevel.NORMAL:
                self.secure_domains.add(d)

        # Hit in buffer: update entry metadata and frequency
        if block_addr in self.entries:
            e = self.entries[block_addr]
            e.owners |= owners
            if sens_level > e.sensitivity:
                e.sensitivity = sens_level
            e.last_access = current_time
            if e.frequency < 15:
                e.frequency += 1
            return True

        # Sliding-Window Shannon Entropy Profiler Check
        sweep_active = any(self.profiler.is_sweep_active(d) for d in owners)
        is_low_trust = sweep_active and (sens_level == SensitivityLevel.NORMAL)

        # Rapid DRAM bypass for low-trust lines during sweeps when buffer is contended
        if is_low_trust and len(self.entries) >= self.capacity:
            self.bypasses += 1
            self.sweep_bypasses += 1
            return False

        # Token-bucket burst rate limiter for non-sensitive traffic
        if sens_level == SensitivityLevel.NORMAL:
            for d in owners:
                elapsed = max(0, current_time - self.updated[d])
                self.tokens[d] = min(self.max_tokens, self.tokens[d] + elapsed * self.refill_rate)
                self.updated[d] = current_time
                if self.tokens[d] < 1.0:
                    self.bypasses += 1
                    return False

        # Dynamic Elastic Domain Quota (DEDQ) Enforcement
        domain_quota_exceeded = any(
            self.get_domain_occupancy(d) >= self.get_elastic_quota(d, current_time)
            for d in owners
        )
        must_replace = (len(self.entries) >= self.capacity) or domain_quota_exceeded

        # Instant Revocation Floor Enforcement:
        # If an active domain with occupancy < base_floor requires insertion and buffer is full,
        # reclaim a slot from the domain that borrowed the most above base_floor.
        reclaimed = False
        if len(self.entries) >= self.capacity:
            for d in owners:
                if self.get_domain_occupancy(d) < self.base_floor:
                    # Look for a domain with excess borrowed capacity
                    borrower_domains = [
                        bd for bd in range(self.num_domains)
                        if self.get_domain_occupancy(bd) > self.base_floor
                    ]
                    if borrower_domains:
                        worst_borrower = max(
                            borrower_domains,
                            key=lambda bd: self.get_domain_occupancy(bd) - self.base_floor
                        )
                        # Reclaim lowest retention line from this borrower
                        borrower_entries = [
                            (a, e) for a, e in self.entries.items()
                            if worst_borrower in e.owners
                        ]
                        if borrower_entries:
                            # Prioritize low-trust -> NORMAL -> PROTECTED -> ROOT
                            pool_low = [x for x in borrower_entries if x[1].low_trust]
                            pool_normal = [x for x in borrower_entries if not x[1].low_trust and x[1].sensitivity == SensitivityLevel.NORMAL]
                            pool_prot = [x for x in borrower_entries if x[1].sensitivity == SensitivityLevel.PROTECTED_PAGE]
                            pool_root = [x for x in borrower_entries if x[1].sensitivity == SensitivityLevel.ROOT_OF_TRUST]
                            
                            revoke_pool = pool_low or pool_normal or pool_prot or pool_root
                            rev_addr, _ = min(revoke_pool, key=lambda x: (self.score(x[1], current_time), x[1].last_access))
                            del self.entries[rev_addr]
                            self.evictions += 1
                            self.revocations += 1
                            reclaimed = True
                            break

        # Standard Replacement under Domain Isolation & Multi-Tier Sticky Policy
        if must_replace and not reclaimed:
            if domain_quota_exceeded:
                eligible = [
                    (a, e) for a, e in self._eligible(owners)
                    if any(d in e.owners and self.get_domain_occupancy(d) >= self.get_elastic_quota(d, current_time) for d in owners)
                ]
            else:
                eligible = self._eligible(owners)

            if not eligible:
                self.bypasses += 1
                return False

            # Categorize eligible entries into tiers
            tier_low_trust = [(a, e) for a, e in eligible if e.low_trust]
            tier_normal = [(a, e) for a, e in eligible if not e.low_trust and e.sensitivity == SensitivityLevel.NORMAL]
            tier_protected = [(a, e) for a, e in eligible if e.sensitivity == SensitivityLevel.PROTECTED_PAGE]
            tier_root = [(a, e) for a, e in eligible if e.sensitivity == SensitivityLevel.ROOT_OF_TRUST]

            # Sticky Residency Enforcement:
            # NORMAL or PROTECTED_PAGE cannot evict ROOT_OF_TRUST
            if sens_level < SensitivityLevel.ROOT_OF_TRUST and not tier_low_trust and not tier_normal and not tier_protected:
                self.bypasses += 1
                return False

            # NORMAL cannot evict PROTECTED_PAGE
            if sens_level == SensitivityLevel.NORMAL and not tier_low_trust and not tier_normal:
                self.bypasses += 1
                return False

            # Select candidate pool from lowest available tier
            candidate_pool = tier_low_trust or tier_normal or tier_protected or tier_root

            # Pick victim candidate with lowest retention score R+(k)
            evict_key, old_entry = min(
                candidate_pool,
                key=lambda x: (self.score(x[1], current_time), x[1].last_access)
            )

            # Compare retention scores for non-root incoming
            incoming_entry = BufferEntryPlus(
                address=block_addr,
                owners=owners,
                sensitivity=sens_level,
                insertion_time=current_time,
                last_access=current_time,
                frequency=1,
                low_trust=is_low_trust
            )
            if sens_level < SensitivityLevel.ROOT_OF_TRUST and self.score(incoming_entry, current_time) <= self.score(old_entry, current_time):
                self.bypasses += 1
                return False

            del self.entries[evict_key]
            self.evictions += 1

        # Install new entry in buffer
        is_borrowed = any(self.get_domain_occupancy(d) >= self.base_floor for d in owners)
        if is_borrowed:
            self.borrowed_insertions += 1

        self.entries[block_addr] = BufferEntryPlus(
            address=block_addr,
            owners=owners,
            sensitivity=sens_level,
            insertion_time=current_time,
            last_access=current_time,
            frequency=1,
            low_trust=is_low_trust
        )

        # Deduct token for non-sensitive insertion
        if sens_level == SensitivityLevel.NORMAL:
            for d in owners:
                self.tokens[d] -= 1.0

        return True


class MultiCoreCacheSystemPlus(MultiCoreCacheSystem):
    """
    MultiCoreCacheSystemPlus: Extended cache system supporting N cores and N domains
    with full support for TreasureCache, Ada-EHB, and Ada-EHB+.
    """
    def __init__(
        self,
        mode: str = 'ada_ehb_plus',
        ehb_capacity: int = 48,
        num_domains: int = 3,
        num_cores: int = 3,
        seed: int = 42,
        llc_sets: int = 32,
        llc_ways: int = 4
    ):
        super().__init__(mode=mode, ehb_capacity=ehb_capacity, seed=seed, llc_sets=llc_sets, llc_ways=llc_ways)
        self.num_domains = num_domains
        self.num_cores = num_cores
        
        # Bounded private caches per core
        self.l1 = [{} for _ in range(num_cores)]
        self.l2 = [{} for _ in range(num_cores)]
        self.sensitivity_map: Dict[int, SensitivityLevel] = {}

        # Instantiate buffer based on mode
        if mode == 'treasure_cache':
            self.ehb: Optional[EvictionHiddenBuffer] = EvictionHiddenBuffer(
                ehb_capacity, hit_latency=self.LATENCY_EHB, num_domains=num_domains
            )
        elif mode == 'ada_ehb':
            self.ehb: Optional[EvictionHiddenBuffer] = AdaptiveEvictionHiddenBuffer(
                ehb_capacity, hit_latency=self.LATENCY_EHB, num_domains=num_domains
            )
        elif mode == 'ada_ehb_plus':
            self.ehb: Optional[EvictionHiddenBuffer] = AdaEHBPlusBuffer(
                ehb_capacity, hit_latency=self.LATENCY_EHB, num_domains=num_domains
            )
        else:
            self.ehb = None

    def _invalidate_private(self, block: int) -> bool:
        """Back-invalidates a block from all private L1/L2 caches across all cores."""
        had = bool(self.sharers.get(block))
        for c in range(self.num_cores):
            self.l1[c].pop(block, None)
            self.l2[c].pop(block, None)
        self.sharers.pop(block, None)
        if had:
            self.stats['back_invalidations'] += 1
        return had

    def _evict_llc(self, victim_block: int, idx: int, from_ehb: bool):
        """Evicts a block from LLC and enforces dual-condition EHB placement."""
        self.llc[idx].pop(victim_block, None)
        self.stats['llc_evictions'] += 1
        had_sharers = self._invalidate_private(victim_block)

        if self.ehb and (had_sharers or from_ehb):
            self.stats['ehb_eligible'] += 1
            owners = self.owners.get(victim_block, set())
            sens = self.sensitivity_map.get(
                victim_block,
                SensitivityLevel.ROOT_OF_TRUST if victim_block in self.sensitive else SensitivityLevel.NORMAL
            )

            if isinstance(self.ehb, AdaEHBPlusBuffer):
                if self.ehb.insert(victim_block, owners, sens, self.time):
                    self.stats['ehb_inserted'] += 1
            else:
                is_sens = (sens != SensitivityLevel.NORMAL) if isinstance(sens, SensitivityLevel) else bool(sens)
                if self.ehb.insert(victim_block, owners, is_sens, self.time):
                    self.stats['ehb_inserted'] += 1

    def read_address(
        self,
        core_id: int,
        addr: int,
        domain_id: int,
        is_sensitive: bool = False,
        sensitivity: Optional[SensitivityLevel] = None
    ) -> Tuple[int, str]:
        """
        Executes a memory read across the cache hierarchy.
        Supports discrete SensitivityLevels and records accesses for entropy profiling.
        """
        block = addr // LINE_SIZE
        self.owners.setdefault(block, set()).add(domain_id)

        # Resolve sensitivity level
        if sensitivity is not None:
            sens_level = sensitivity
        elif is_sensitive:
            sens_level = SensitivityLevel.ROOT_OF_TRUST
        else:
            sens_level = SensitivityLevel.NORMAL

        current_sens = self.sensitivity_map.get(block, SensitivityLevel.NORMAL)
        if sens_level > current_sens:
            self.sensitivity_map[block] = sens_level

        if sens_level > SensitivityLevel.NORMAL:
            self.sensitive.add(block)

        # Entropy profiler recording
        if isinstance(self.ehb, AdaEHBPlusBuffer):
            self.ehb.record_access(domain_id, block, self.time)

        # 1. Private L1 Hit
        if block in self.l1[core_id]:
            self._private_add(core_id, block)
            self.time += self.LATENCY_L1
            return self.LATENCY_L1, 'L1_HIT'

        # 2. Private L2 Hit
        if block in self.l2[core_id]:
            self._private_add(core_id, block)
            self.time += self.LATENCY_L2
            return self.LATENCY_L2, 'L2_HIT'

        idx = self._set(block)
        # 3. Shared LLC Hit
        if block in self.llc[idx]:
            self.llc[idx][block] = self.time
            self._private_add(core_id, block)
            self.time += self.LATENCY_LLC
            return self.LATENCY_LLC, 'LLC_HIT'

        # 4. EHB Hit (Reload into LLC)
        entry = self.ehb.take(block, self.time) if self.ehb else None
        if entry:
            self._install_llc(block, domain_id, from_ehb=True)
            self._private_add(core_id, block)
            self.time += self.LATENCY_EHB
            return self.LATENCY_EHB, 'EHB_HIT'

        # 5. DRAM Miss
        self._install_llc(block, domain_id, from_ehb=False)
        self._private_add(core_id, block)
        latency = self.LATENCY_DRAM + self.rng.randint(-4, 8)
        self.time += latency
        return latency, 'DRAM_MISS'


def run_asymmetric_workload_trial(
    ehb_capacity: int = 48,
    victim_lines: int = 24,
    churn_lines: int = 64,
    seed: int = 42
) -> Dict[str, Dict]:
    """
    Executes comparison trial across architectures under asymmetric multi-tenant workloads:
      - Domain 0: Cryptographic victim core (working set of 24 ROOT_OF_TRUST lines).
      - Domain 1: High-churn streaming attacker core (traversing eviction set with flat entropy).
      - Domain 2: Idle core (allocated to inactive tenant VM; 0 accesses).
      
    Demonstrates how Ada-EHB+ utilizes DEDQ to borrow from the idle domain, retaining 100%
    of sensitive lines with 0% false evictions, outperforming static TreasureCache and initial Ada-EHB.
    """
    results: Dict[str, Dict] = {}
    modes = ['treasure_cache', 'ada_ehb', 'ada_ehb_plus']
    
    for mode in modes:
        sys_sim = MultiCoreCacheSystemPlus(
            mode=mode,
            ehb_capacity=ehb_capacity,
            num_domains=3,
            num_cores=3,
            seed=seed,
            llc_sets=32,
            llc_ways=4
        )
        victim_addrs = [(0x100000 // LINE_SIZE + i) * LINE_SIZE for i in range(victim_lines)]

        # Phase 1: Victim (Domain 0, Core 0) accesses cryptographic working set
        for _ in range(3):
            for a in victim_addrs:
                sys_sim.read_address(
                    core_id=0,
                    addr=a,
                    domain_id=0,
                    sensitivity=SensitivityLevel.ROOT_OF_TRUST
                )

        # Phase 2: Force victim lines out of LLC into EHB via conflict eviction
        for a in victim_addrs:
            force_llc_eviction(sys_sim, a, count=6)

        initial_buffered = sum(
            sys_sim.ehb.contains(a // LINE_SIZE) for a in victim_addrs
        ) if sys_sim.ehb else 0

        # Phase 3: Attacker (Domain 1, Core 1) executes high-churn eviction-set sweep
        # Domain 2 remains strictly idle (0 accesses)
        for j in range(churn_lines):
            churn_addr = ((300000 + j) * sys_sim.llc_sets + (j % sys_sim.llc_sets)) * LINE_SIZE
            sys_sim.read_address(
                core_id=1,
                addr=churn_addr,
                domain_id=1,
                sensitivity=SensitivityLevel.NORMAL
            )

        retained = sum(
            sys_sim.ehb.contains(a // LINE_SIZE) for a in victim_addrs
        ) if sys_sim.ehb else 0

        # Phase 4: Victim probes cryptographic lines
        probe_results = []
        for a in victim_addrs:
            lat, level = sys_sim.read_address(
                core_id=0,
                addr=a,
                domain_id=0,
                sensitivity=SensitivityLevel.ROOT_OF_TRUST
            )
            probe_results.append({'latency': lat, 'level': level})

        ehb_hits = sum(r['level'] == 'EHB_HIT' for r in probe_results)
        dram_misses = sum(r['level'] == 'DRAM_MISS' for r in probe_results)
        mean_lat = sum(r['latency'] for r in probe_results) / len(probe_results)
        false_evictions = victim_lines - retained
        retention_rate = (retained / victim_lines) * 100.0

        results[mode] = {
            'victim_lines': victim_lines,
            'initial_buffered': initial_buffered,
            'retained': retained,
            'false_evictions': false_evictions,
            'retention_rate': retention_rate,
            'ehb_hits': ehb_hits,
            'dram_misses': dram_misses,
            'mean_latency': mean_lat,
            'bypasses': sys_sim.ehb.bypasses if sys_sim.ehb else 0,
            'evictions': sys_sim.ehb.evictions if sys_sim.ehb else 0,
        }
        if isinstance(sys_sim.ehb, AdaEHBPlusBuffer):
            results[mode]['revocations'] = sys_sim.ehb.revocations
            results[mode]['sweep_bypasses'] = sys_sim.ehb.sweep_bypasses
            results[mode]['borrowed_insertions'] = sys_sim.ehb.borrowed_insertions

    return results


def run_revocation_floor_trial(ehb_capacity: int = 48, seed: int = 42) -> Dict:
    """
    Demonstrates the Instant Revocation Floor mechanism:
    1. Domain 0 borrows capacity from idle Domain 2 up to capacity limit.
    2. Domain 2 (idle core) suddenly wakes up and accesses memory lines.
    3. Ada-EHB+ instantly honors Domain 2's guaranteed base quota floor by revoking
       borrowed lines without stalling or denying Domain 2 admission.
    """
    sys_sim = MultiCoreCacheSystemPlus(
        mode='ada_ehb_plus',
        ehb_capacity=ehb_capacity,
        num_domains=3,
        num_cores=3,
        seed=seed,
        llc_sets=32,
        llc_ways=4
    )
    floor = ehb_capacity // 3  # 16 lines
    
    # Domain 0 inserts 40 lines (borrowing capacity from idle domains)
    dom0_addrs = [(0x100000 // LINE_SIZE + i) * LINE_SIZE for i in range(40)]
    for a in dom0_addrs:
        sys_sim.read_address(core_id=0, addr=a, domain_id=0, sensitivity=SensitivityLevel.PROTECTED_PAGE)
        force_llc_eviction(sys_sim, a, count=6)
        
    dom0_initial = sum(sys_sim.ehb.contains(a // LINE_SIZE) for a in dom0_addrs)
    
    # Domain 2 wakes up and inserts its full guaranteed floor (16 lines)
    dom2_addrs = [(0x200000 // LINE_SIZE + i) * LINE_SIZE for i in range(floor)]
    for a in dom2_addrs:
        sys_sim.read_address(core_id=2, addr=a, domain_id=2, sensitivity=SensitivityLevel.PROTECTED_PAGE)
        force_llc_eviction(sys_sim, a, count=6)
        
    dom2_admitted = sum(sys_sim.ehb.contains(a // LINE_SIZE) for a in dom2_addrs)
    dom0_after_wake = sum(sys_sim.ehb.contains(a // LINE_SIZE) for a in dom0_addrs)
    
    return {
        'base_floor': floor,
        'dom0_initial_buffered': dom0_initial,
        'dom2_requested': floor,
        'dom2_admitted': dom2_admitted,
        'dom0_retained': dom0_after_wake,
        'revocations': sys_sim.ehb.revocations,
        'total_buffered': len(sys_sim.ehb.entries)
    }


class ComprehensiveAdaEHBPlusTests(unittest.TestCase):
    """Integrity and behavioral regression test suite for Ada-EHB+."""

    def test_1_shannon_entropy_profiler_eviction_sweep(self):
        """Validates that flat, distinct eviction set sweep yields near-maximum entropy."""
        profiler = ShannonEntropyProfiler(window_size=32, sweep_threshold=0.85)
        # Attacker traverses 32 completely distinct addresses
        for i in range(32):
            profiler.record_access(domain=1, block_addr=1000 + i)
            
        norm_h = profiler.get_normalized_entropy(domain=1)
        self.assertAlmostEqual(norm_h, 1.0, places=3, msg="Flat sweep must produce H_hat = 1.0")
        self.assertTrue(profiler.is_sweep_active(domain=1), "Sweep detection must trigger on H_hat >= 0.85")
        self.assertEqual(profiler.get_entropy_penalty(domain=1), 1.0, "Entropy penalty must saturate at 1.0")

    def test_2_shannon_entropy_profiler_localized_crypto(self):
        """Validates that cryptographic table lookups exhibit high locality and zero entropy penalty."""
        profiler = ShannonEntropyProfiler(window_size=32, sweep_threshold=0.85)
        # Victim repeatedly accesses 4 table lines
        for i in range(32):
            profiler.record_access(domain=0, block_addr=500 + (i % 4))
            
        norm_h = profiler.get_normalized_entropy(domain=0)
        self.assertLess(norm_h, 0.70, "High locality access must produce H_hat <= 0.70")
        self.assertFalse(profiler.is_sweep_active(domain=0), "Sweep detection must NOT trigger on crypto accesses")
        self.assertEqual(profiler.get_entropy_penalty(domain=0), 0.0, "Entropy penalty must be 0.0 for crypto")

    def test_3_dynamic_elastic_quota_borrowing(self):
        """Validates that an active secure domain borrows unused capacity from idle domains."""
        buf = AdaEHBPlusBuffer(capacity_lines=48, num_domains=3, idle_timeout=100)
        base_floor = 48 // 3  # 16
        
        # Domain 0 is registered as a secure domain
        buf.secure_domains.add(0)
        buf.last_domain_activity[0] = 10
        # Domain 1 is active (e.g. accessed at current_time=150, within idle_timeout=100)
        buf.last_domain_activity[1] = 150
        # Domain 2 has 0 accesses and is idle
        buf.last_domain_activity[2] = 0
        
        elastic_quota = buf.get_elastic_quota(domain=0, current_time=200)
        self.assertGreater(elastic_quota, base_floor, "Active secure domain must borrow idle capacity")
        self.assertEqual(elastic_quota, 32, "Domain 0 should borrow Domain 2's 16 lines (16 + 16 = 32)")
        
        # Non-secure domain (Domain 1) must NOT borrow
        dom1_quota = buf.get_elastic_quota(domain=1, current_time=200)
        self.assertEqual(dom1_quota, base_floor, "Non-secure domain must remain capped at base floor")

    def test_4_instant_revocation_floor_enforcement(self):
        """Validates that when an idle domain wakes up, its guaranteed floor is restored immediately."""
        res = run_revocation_floor_trial(ehb_capacity=48)
        self.assertEqual(res['dom2_admitted'], res['dom2_requested'], "Waking domain must receive 100% of its floor")
        self.assertGreater(res['revocations'], 0, "Revocations must trigger to free slots for waking domain")
        self.assertEqual(res['total_buffered'], 48, "Total buffer occupancy must respect capacity")

    def test_5_multitier_sticky_protection_root_of_trust(self):
        """Validates that ROOT_OF_TRUST entries cannot be evicted by NORMAL or PROTECTED_PAGE entries."""
        buf = AdaEHBPlusBuffer(capacity_lines=2, num_domains=1)
        buf.insert(1, owners={0}, sensitivity=SensitivityLevel.ROOT_OF_TRUST, current_time=1)
        buf.insert(2, owners={0}, sensitivity=SensitivityLevel.ROOT_OF_TRUST, current_time=2)
        
        # NORMAL insertion must bypass directly to DRAM
        admitted = buf.insert(3, owners={0}, sensitivity=SensitivityLevel.NORMAL, current_time=3)
        self.assertFalse(admitted, "NORMAL line must bypass when all entries are ROOT_OF_TRUST")
        
        # PROTECTED_PAGE insertion must also bypass
        admitted_prot = buf.insert(4, owners={0}, sensitivity=SensitivityLevel.PROTECTED_PAGE, current_time=4)
        self.assertFalse(admitted_prot, "PROTECTED_PAGE must bypass when all entries are ROOT_OF_TRUST")
        
        # Both ROOT_OF_TRUST entries must remain perfectly resident
        self.assertIn(1, buf.entries)
        self.assertIn(2, buf.entries)

    def test_6_multitier_replacement_hierarchy(self):
        """Validates replacement order: low-trust -> NORMAL -> PROTECTED_PAGE -> ROOT_OF_TRUST."""
        buf = AdaEHBPlusBuffer(capacity_lines=3, num_domains=1)
        buf.insert(1, owners={0}, sensitivity=SensitivityLevel.ROOT_OF_TRUST, current_time=1)
        buf.insert(2, owners={0}, sensitivity=SensitivityLevel.PROTECTED_PAGE, current_time=2)
        buf.insert(3, owners={0}, sensitivity=SensitivityLevel.NORMAL, current_time=3)
        
        # Inserting a new PROTECTED_PAGE line should evict the NORMAL line (Block 3)
        buf.insert(4, owners={0}, sensitivity=SensitivityLevel.PROTECTED_PAGE, current_time=4)
        self.assertIn(1, buf.entries, "ROOT_OF_TRUST line 1 must be preserved")
        self.assertIn(2, buf.entries, "PROTECTED_PAGE line 2 must be preserved")
        self.assertIn(4, buf.entries, "New line 4 must be admitted")
        self.assertNotIn(3, buf.entries, "NORMAL line 3 should be evicted first")

    def test_7_enhanced_retention_scoring_values(self):
        """Validates that R+(k) scoring reflects sensitivity tiers and entropy penalties."""
        buf = AdaEHBPlusBuffer(capacity_lines=8, num_domains=2)
        entry_root = BufferEntryPlus(1, {0}, SensitivityLevel.ROOT_OF_TRUST, 0, 0, frequency=5)
        entry_normal = BufferEntryPlus(2, {0}, SensitivityLevel.NORMAL, 0, 0, frequency=5)
        
        score_root = buf.score(entry_root, current_time=10)
        score_normal = buf.score(entry_normal, current_time=10)
        self.assertGreater(score_root, 4.0 * score_normal, "ROOT_OF_TRUST score must be ~5x higher than NORMAL")
        
        # Introduce high entropy penalty for Domain 1
        for i in range(32):
            buf.record_access(domain=1, block_addr=2000 + i, current_time=10)
        entry_attacker = BufferEntryPlus(3, {1}, SensitivityLevel.NORMAL, 0, 0, frequency=1)
        score_attacker = buf.score(entry_attacker, current_time=10)
        self.assertLess(score_attacker, score_normal, "Attacker line must be penalized by entropy profiler")

    def test_8_token_bucket_rate_limiting_plus(self):
        """Validates token-bucket rate limiter exhaustion and refill in Ada-EHB+."""
        buf = AdaEHBPlusBuffer(capacity_lines=16, num_domains=1)
        for i in range(1, 9):
            self.assertTrue(buf.insert(i, owners={0}, sensitivity=SensitivityLevel.NORMAL, current_time=0))
        # 9th block at t=0 should be rate-limited
        self.assertFalse(buf.insert(9, owners={0}, sensitivity=SensitivityLevel.NORMAL, current_time=0))
        # Advance time by 250 cycles (refills 2 tokens)
        self.assertTrue(buf.insert(9, owners={0}, sensitivity=SensitivityLevel.NORMAL, current_time=250))

    def test_9_asymmetric_trial_verifies_100_percent_retention(self):
        """Validates that the comparison trial achieves 100% retention and 0% false evictions for Ada-EHB+."""
        trial_results = run_asymmetric_workload_trial(ehb_capacity=48, victim_lines=24, churn_lines=64, seed=42)
        
        tc = trial_results['treasure_cache']
        ada = trial_results['ada_ehb']
        plus = trial_results['ada_ehb_plus']
        
        # Verify TreasureCache static quota limitation
        self.assertEqual(tc['retained'], 16, "TreasureCache should be capped at static quota (16 lines)")
        self.assertEqual(tc['false_evictions'], 8, "TreasureCache should suffer 8 false evictions")
        
        # Verify Baseline Ada-EHB static quota limitation
        self.assertEqual(ada['retained'], 16, "Baseline Ada-EHB should be capped at static quota (16 lines)")
        self.assertEqual(ada['false_evictions'], 8, "Baseline Ada-EHB should suffer 8 false evictions")
        
        # Verify Ada-EHB+ 100% retention and 0% false evictions
        self.assertEqual(plus['retained'], 24, "Ada-EHB+ MUST retain all 24 sensitive lines")
        self.assertEqual(plus['false_evictions'], 0, "Ada-EHB+ MUST achieve 0 false evictions")
        self.assertEqual(plus['retention_rate'], 100.0, "Ada-EHB+ MUST achieve 100% retention rate")
        self.assertEqual(plus['ehb_hits'], 24, "Ada-EHB+ MUST achieve 24 EHB hits")
        self.assertEqual(plus['dram_misses'], 0, "Ada-EHB+ MUST suffer 0 DRAM misses")
        self.assertEqual(plus['mean_latency'], 40.0, "Ada-EHB+ mean latency must be constant 40 cycles")


def print_comparison_table(trial_results: Dict[str, Dict]):
    """Prints a clean ASCII comparison table of trial results."""
    print("\n" + "=" * 90)
    print("  Ada-EHB+ (Ada-EHB 2.0) vs Baseline Ada-EHB vs TreasureCache Performance Trial")
    print("  Workload: Domain 0 (Crypto Victim: 24 lines) | Domain 1 (Attacker Sweep) | Domain 2 (Idle)")
    print("  Buffer Capacity: 48 lines | Domains: 3 | Base Quota: 16 lines")
    print("=" * 90)
    print(f"{'Architecture':<22} | {'Retained':<9} | {'False Evict':<11} | {'Retention %':<11} | {'EHB Hits':<9} | {'Mean Latency':<12}")
    print("-" * 90)
    
    names = {
        'treasure_cache': 'TreasureCache (Static)',
        'ada_ehb': 'Ada-EHB (Baseline)',
        'ada_ehb_plus': 'Ada-EHB+ (Ada-EHB 2.0)'
    }
    
    for key, name in names.items():
        res = trial_results[key]
        print(
            f"{name:<22} | "
            f"{res['retained']:<3}/{res['victim_lines']:<5} | "
            f"{res['false_evictions']:<11} | "
            f"{res['retention_rate']:>6.1f}%    | "
            f"{res['ehb_hits']:<9} | "
            f"{res['mean_latency']:>6.1f} cycles"
        )
    print("=" * 90)


if __name__ == '__main__':
    print("Executing Ada-EHB+ Asymmetric Workload Comparison Trial...")
    trial_data = run_asymmetric_workload_trial(ehb_capacity=48, victim_lines=24, churn_lines=64, seed=42)
    print_comparison_table(trial_data)
    
    print("\nExecuting Instant Revocation Floor Trial (Domain 2 Waking Up)...")
    rev_data = run_revocation_floor_trial(ehb_capacity=48)
    print(f"  Domain 0 Initial Borrowed Lines : {rev_data['dom0_initial_buffered']} lines")
    print(f"  Domain 2 Guaranteed Floor Target: {rev_data['dom2_requested']} lines")
    print(f"  Domain 2 Admitted on Wakeup    : {rev_data['dom2_admitted']}/{rev_data['dom2_requested']} lines (100% Guaranteed)")
    print(f"  Instant Revocations Executed    : {rev_data['revocations']} lines")
    print(f"  Total Buffer Resident Lines     : {rev_data['total_buffered']}/48 lines")
    
    print("\nRunning Automated Behavioral Regression Suite for Ada-EHB+...")
    suite = unittest.TestLoader().loadTestsFromTestCase(ComprehensiveAdaEHBPlusTests)
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)
    
    if test_result.wasSuccessful():
        print("\n[SUCCESS] All Ada-EHB+ architectural requirements and integrity tests PASSED.")
        sys.exit(0)
    else:
        print("\n[FAILURE] One or more Ada-EHB+ tests failed.")
        sys.exit(1)
