"""
cache_model.py - Hardware Cache Hierarchy, TreasureCache & Ada-EHB Simulation Model

Sequential synthetic cache-event simulator (educational model; not full-system gem5).
Models:
  - 64-byte lines, multi-level inclusive cache hierarchy (private L1/L2 per core, shared inclusive LLC).
  - Explicit per-core private-cache sharer tracking (sharers: set of core IDs).
  - Explicit per-domain ownership tracking (owners: set of domain IDs) representing physical page ownership.
  - Dual-condition secure placement policy (Condition 1: private sharers; Condition 2: EHB-reload replacement).
  - Domain-isolated ownership replacement policy (eligibility strictly enforces subset ownership).
  - EHB reload mechanism: hits in EHB are removed from EHB and installed into LLC (marked from_ehb=True).
  - Coherence back-invalidation: LLC evictions back-invalidate private L1/L2 caches.
  - Constant-Time Flush (CT-Flush): constant 70-cycle execution on cached and uncached lines.
  - Proposed Ada-EHB: Dynamic retention scoring, 4-bit frequency counters, sticky residency for sensitive entries,
    and token-bucket burst rate-limiting.
"""

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

LINE_SIZE = 64


@dataclass
class BufferEntry:
    """Represents an entry stored inside the Eviction-Hidden Buffer (EHB)."""
    address: int
    owners: Set[int]
    sensitive: bool
    insertion_time: int
    last_access: int
    frequency: int = 1


class EvictionHiddenBuffer:
    """
    Standard TreasureCache Eviction-Hidden Buffer (EHB).
    - Fully-associative buffer of parameterized capacity.
    - Domain ownership quota: conservative cap (capacity // num_domains) per domain.
    - Eligibility Rule: An incoming block can ONLY replace an entry whose owners
      are a subset of the incoming block's owners. This strictly prevents cross-domain eviction.
    - Reload Behavior: Hits in the EHB take the entry out of the buffer so it can be re-installed into LLC.
    """
    def __init__(self, capacity_lines: int = 64, hit_latency: int = 40, num_domains: int = 2):
        self.capacity = capacity_lines
        self.hit_latency = hit_latency
        self.num_domains = num_domains
        self.quota = max(1, capacity_lines // num_domains)
        self.entries: Dict[int, BufferEntry] = {}
        
        # Operational counters
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.bypasses = 0

    def contains(self, block_addr: int) -> bool:
        return block_addr in self.entries

    def take(self, block_addr: int, current_time: int) -> Optional[BufferEntry]:
        """
        Retrieves and removes an entry on hit, modeling EHB-to-LLC reload.
        """
        entry = self.entries.pop(block_addr, None)
        if entry is None:
            self.misses += 1
        else:
            self.hits += 1
            entry.last_access = current_time
            if entry.frequency < 15:
                entry.frequency += 1
        return entry

    def _eligible(self, incoming_owners: Set[int]) -> List[Tuple[int, BufferEntry]]:
        """
        Conservative replacement eligibility rule:
        An insertion may replace ONLY an entry whose owners are a subset of the incoming
        block's owners (e.owners.issubset(incoming_owners)).
        This prevents an attacker-owned block (e.g. {1}) from ever evicting a victim-owned
        block (e.g. {0}).
        """
        return [(a, e) for a, e in self.entries.items() if e.owners.issubset(incoming_owners)]

    def insert(self, block_addr: int, owners: Set[int], sensitive: bool, current_time: int) -> bool:
        owners = set(owners)
        if not owners or self.capacity == 0:
            self.bypasses += 1
            return False

        # If already resident, update ownership and sensitivity flags
        if block_addr in self.entries:
            e = self.entries[block_addr]
            e.owners |= owners
            e.sensitive |= sensitive
            e.last_access = current_time
            if e.frequency < 15:
                e.frequency += 1
            return True

        # Check quota limits: shared entries count against all their owners
        for d in owners:
            domain_count = sum(d in e.owners for e in self.entries.values())
            if domain_count >= self.quota:
                eligible = [(a, e) for a, e in self._eligible(owners) if d in e.owners]
                if not eligible:
                    self.bypasses += 1
                    return False
                break
        else:
            eligible = self._eligible(owners) if len(self.entries) >= self.capacity else []

        if eligible:
            # Standard TreasureCache policy: replace the LRU among eligible entries
            evict_key = min(eligible, key=lambda item: item[1].last_access)[0]
            del self.entries[evict_key]
            self.evictions += 1
        elif len(self.entries) >= self.capacity:
            self.bypasses += 1
            return False

        self.entries[block_addr] = BufferEntry(
            address=block_addr,
            owners=owners,
            sensitive=sensitive,
            insertion_time=current_time,
            last_access=current_time,
            frequency=1
        )
        return True


class AdaptiveEvictionHiddenBuffer(EvictionHiddenBuffer):
    """
    Proposed Ada-EHB: Adaptive Frequency-Aware Eviction-Hidden Buffer.
    
    Formal Mathematical Specification:
      1. Retention Score:
         R(k) = [ S(k) * (1 + alpha * F(k)) ] / ln(1 + Age(k) + epsilon)
         where:
           - S(k): Sensitivity weight (3.0 for sensitive lines, 1.0 for normal).
           - F(k): 4-bit saturating frequency counter (0 <= F(k) <= 15).
           - alpha: Frequency importance weight (0.2).
           - Age(k): current_time - last_access (in clock cycles).
           - epsilon: 1e-5 (prevents division by zero).
      
      2. Domain-Isolated Replacement with Protected Sensitive Entries:
         - Candidate replacement entries must strictly belong to the incoming block's domain subset (_eligible).
         - Non-sensitive entries are preferred for eviction.
         - Sensitive entries are protected while eligible non-sensitive entries exist.
         - If all eligible entries are sensitive, non-sensitive incoming blocks bypass directly to DRAM.
      
      3. Token-Bucket Burst Rate-Limiting:
         - Per-domain token bucket: capacity M = 8 tokens, refill rate = 1 token per 125 cycles.
         - Non-sensitive burst evictions exceeding available tokens bypass directly to DRAM.
    """
    def __init__(self, capacity_lines: int = 64, hit_latency: int = 40, num_domains: int = 2):
        super().__init__(capacity_lines, hit_latency, num_domains)
        self.alpha = 0.2
        self.epsilon = 1e-5
        self.tokens: Dict[int, float] = {d: 8.0 for d in range(num_domains)}
        self.updated: Dict[int, int] = {d: 0 for d in range(num_domains)}
        self.max_tokens = 8.0
        self.refill_rate = 1.0 / 125.0  # 8 tokens per 1000 cycles

    def score(self, entry: BufferEntry, current_time: int) -> float:
        age = max(1, current_time - entry.last_access)
        s_weight = 3.0 if entry.sensitive else 1.0
        return (s_weight * (1.0 + self.alpha * entry.frequency)) / math.log(1.0 + age + self.epsilon)

    def insert(self, block_addr: int, owners: Set[int], sensitive: bool, current_time: int) -> bool:
        owners = set(owners)
        if not owners or self.capacity == 0:
            self.bypasses += 1
            return False

        if block_addr in self.entries:
            e = self.entries[block_addr]
            e.owners |= owners
            e.sensitive |= sensitive
            e.last_access = current_time
            if e.frequency < 15:
                e.frequency += 1
            return True

        # Token-bucket rate-limiting for non-sensitive burst traffic
        if not sensitive:
            for d in owners:
                elapsed = max(0, current_time - self.updated[d])
                self.tokens[d] = min(self.max_tokens, self.tokens[d] + elapsed * self.refill_rate)
                self.updated[d] = current_time
                if self.tokens[d] < 1.0:
                    self.bypasses += 1
                    return False

        must_replace = (len(self.entries) >= self.capacity or any(
            sum(d in e.owners for e in self.entries.values()) >= self.quota for d in owners
        ))

        if must_replace:
            eligible = self._eligible(owners)
            # Prefer non-sensitive entries for replacement
            nonsensitive = [(a, e) for a, e in eligible if not e.sensitive]
            if nonsensitive:
                eligible = nonsensitive
            elif not sensitive:
                # If all eligible resident entries are sensitive and incoming is non-sensitive:
                # Sticky residency protects existing sensitive entries -> bypass to DRAM!
                self.bypasses += 1
                return False

            if not eligible:
                self.bypasses += 1
                return False

            # Select candidate with lowest retention score (tie-break on older last_access)
            key, old_entry = min(eligible, key=lambda x: (self.score(x[1], current_time), x[1].last_access))
            incoming_entry = BufferEntry(block_addr, owners, sensitive, current_time, current_time)

            if not sensitive and self.score(incoming_entry, current_time) <= self.score(old_entry, current_time):
                self.bypasses += 1
                return False

            del self.entries[key]
            self.evictions += 1

        self.entries[block_addr] = BufferEntry(
            address=block_addr,
            owners=owners,
            sensitive=sensitive,
            insertion_time=current_time,
            last_access=current_time,
            frequency=1
        )

        if not sensitive:
            for d in owners:
                self.tokens[d] -= 1.0

        return True


class MultiCoreCacheSystem:
    """
    Simulates a 2-core processor with inclusive multi-level caching:
      - Private L1 per core (512 lines = 32 KB, LRU, 4 cycles)
      - Private L2 per core (4096 lines = 256 KB, LRU, 12 cycles)
      - Shared Inclusive LLC (parameterized sets and ways, default 2048 sets x 16 ways = 2 MB, 38 cycles)
      - Memory DRAM (~200 cycles)
    Defense modes supported:
      - 'none': Standard inclusive cache without side-channel defense
      - 'partitioned': Static way-partitioning (disjoint ways per domain)
      - 'treasure_cache': TreasureCache EHB with domain ownership quotas & CT-Flush
      - 'ada_ehb': Proposed Ada-EHB with retention scoring, sticky residency, & rate-limiting
    """
    def __init__(self, mode: str = 'none', ehb_capacity: int = 64, seed: int = 42, llc_sets: int = 2048, llc_ways: int = 16):
        self.mode = mode
        self.time = 0
        self.rng = random.Random(seed)
        
        # Latency constants
        self.LATENCY_L1 = 4
        self.LATENCY_L2 = 12
        self.LATENCY_LLC = 38
        self.LATENCY_EHB = 40
        self.LATENCY_DRAM = 200
        self.LATENCY_CT_FLUSH = 70
        
        # Private caches per core: bounded dictionaries with LRU semantics
        self.l1: List[Dict[int, int]] = [{}, {}]
        self.l2: List[Dict[int, int]] = [{}, {}]
        self.l1_limit = 512    # 32 KB
        self.l2_limit = 4096   # 256 KB
        
        # Shared LLC sets
        self.llc_sets = llc_sets
        self.llc_ways = llc_ways
        self.llc: List[Dict[int, int]] = [{} for _ in range(llc_sets)]
        
        # Global coherence and ownership metadata
        self.sharers: Dict[int, Set[int]] = {}  # block -> set(core_id)
        self.owners: Dict[int, Set[int]] = {}   # block -> set(domain_id)
        self.sensitive: Set[int] = set()        # sensitive block addresses
        
        # EHB instances
        if mode == 'treasure_cache':
            self.ehb: Optional[EvictionHiddenBuffer] = EvictionHiddenBuffer(ehb_capacity, hit_latency=self.LATENCY_EHB)
        elif mode == 'ada_ehb':
            self.ehb: Optional[EvictionHiddenBuffer] = AdaptiveEvictionHiddenBuffer(ehb_capacity, hit_latency=self.LATENCY_EHB)
        else:
            self.ehb = None
            
        self.stats = {
            'llc_evictions': 0,
            'back_invalidations': 0,
            'ehb_eligible': 0,
            'ehb_inserted': 0
        }

    def _set(self, block: int) -> int:
        return block % self.llc_sets

    def _private_add(self, core: int, block: int):
        """Adds block to private L1 and L2 caches, updating sharer sets on eviction."""
        for cache, limit in ((self.l1[core], self.l1_limit), (self.l2[core], self.l2_limit)):
            cache.pop(block, None)
            cache[block] = self.time
            if len(cache) > limit:
                oldest = next(iter(cache))
                del cache[oldest]
                if oldest not in self.l1[core] and oldest not in self.l2[core]:
                    self.sharers.get(oldest, set()).discard(core)
        self.sharers.setdefault(block, set()).add(core)

    def _invalidate_private(self, block: int) -> bool:
        """Back-invalidates a block from all private L1/L2 caches. Returns whether block had sharers."""
        had = bool(self.sharers.get(block))
        for c in range(2):
            self.l1[c].pop(block, None)
            self.l2[c].pop(block, None)
        self.sharers.pop(block, None)
        if had:
            self.stats['back_invalidations'] += 1
        return had

    def _install_llc(self, block: int, domain: int, from_ehb: bool = False):
        """Installs block into shared LLC, triggering eviction if set is full."""
        idx = self._set(block)
        group = self.llc[idx]
        group.pop(block, None)

        if self.mode == 'partitioned':
            # Partitioning: disjoint ways per domain
            owned = [b for b in group if domain in self.owners.get(b, set())]
            if len(owned) >= self.llc_ways // 2:
                oldest_owned = min(owned, key=lambda b: group[b])
                self._evict_llc(oldest_owned, idx, from_ehb)
        elif len(group) >= self.llc_ways:
            oldest = min(group, key=lambda b: group[b])
            self._evict_llc(oldest, idx, from_ehb)

        group[block] = self.time

    def _evict_llc(self, victim_block: int, idx: int, from_ehb: bool):
        """Evicts a block from LLC and enforces dual-condition EHB placement."""
        self.llc[idx].pop(victim_block, None)
        self.stats['llc_evictions'] += 1
        had_sharers = self._invalidate_private(victim_block)

        # Dual-Condition Secure Placement:
        # 1. Block had active private-cache sharers (inclusiveness violation risk).
        # 2. OR eviction was caused by an EHB reload replacement.
        if self.ehb and (had_sharers or from_ehb):
            self.stats['ehb_eligible'] += 1
            owners = self.owners.get(victim_block, set())
            is_sens = victim_block in self.sensitive
            if self.ehb.insert(victim_block, owners, is_sens, self.time):
                self.stats['ehb_inserted'] += 1

    def read_address(self, core_id: int, addr: int, domain_id: int, is_sensitive: bool = False) -> Tuple[int, str]:
        """
        Executes a memory read across the cache hierarchy.
        Returns: (latency_in_cycles, hit_level_string)
        """
        block = addr // LINE_SIZE
        self.owners.setdefault(block, set()).add(domain_id)
        if is_sensitive:
            self.sensitive.add(block)

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

        # 5. DRAM Access (Miss across entire hierarchy)
        self._install_llc(block, domain_id, from_ehb=False)
        self._private_add(core_id, block)
        latency = self.LATENCY_DRAM + self.rng.randint(-4, 8)
        self.time += latency
        return latency, 'DRAM_MISS'

    def clflush(self, core_id: int, addr: int) -> int:
        """
        Simulates flush instruction.
        When EHB is present, CT-Flush enforces a predefined constant waiting period (~70 cycles).
        Additionally, per Condition 1 (Section V-C2), evictions caused by flush instructions
        that had active private-cache sharers are securely placed into the EHB.
        """
        block = addr // LINE_SIZE
        had_sharers = self._invalidate_private(block)
        in_llc = (self.llc[self._set(block)].pop(block, None) is not None)
        cached = had_sharers or in_llc
        if self.ehb:
            if had_sharers:
                owners = self.owners.get(block, set())
                is_sens = block in self.sensitive
                if self.ehb.insert(block, owners, is_sens, self.time):
                    self.stats['ehb_inserted'] += 1
                self.stats['ehb_eligible'] += 1
            else:
                cached = (self.ehb.entries.pop(block, None) is not None) or cached
            latency = self.LATENCY_CT_FLUSH
        else:
            latency = 95 if cached else 45
            
        self.time += latency
        return latency
