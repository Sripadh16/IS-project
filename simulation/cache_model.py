"""
cache_model.py - Hardware Cache Hierarchy, Baseline Defenses, TreasureCache & Ada-EHB
Models:
  - Multi-level inclusive cache hierarchy (Private L1/L2, Shared Inclusive LLC, DRAM)
  - Coherence back-invalidation on inclusive LLC evictions
  - Standard Unprotected LRU Cache
  - Static Way-Partitioning (Intel CAT style)
  - TreasureCache EHB with Domain Ownership Quotas & Constant-Time Flush (CT-Flush)
  - Proposed Ada-EHB: Adaptive Frequency-Aware EHB with Retention Scoring & Burst Rate Limiting
"""

import math
import random
from typing import Dict, List, Optional, Tuple, Set


class CacheBlock:
    """Represents a single cache block in L1, L2, or LLC."""
    def __init__(self, tag: int = 0, valid: bool = False, dirty: bool = False, domain_id: int = 0, is_sensitive: bool = False):
        self.tag: int = tag
        self.valid: bool = valid
        self.dirty: bool = dirty
        self.domain_id: int = domain_id  # 0: victim, 1: attacker
        self.is_sensitive: bool = is_sensitive
        self.last_access_time: int = 0
        self.access_count: int = 0
        self.in_private_cache: bool = False


class SetAssociativeCache:
    """Configurable Set-Associative Cache."""
    def __init__(self, name: str, size_bytes: int, ways: int, line_size: int = 64, hit_latency: int = 4):
        self.name = name
        self.size_bytes = size_bytes
        self.ways = ways
        self.line_size = line_size
        self.hit_latency = hit_latency
        
        self.num_lines = size_bytes // line_size
        self.num_sets = self.num_lines // ways
        self.offset_bits = int(math.log2(line_size))
        self.set_bits = int(math.log2(self.num_sets))
        self.set_mask = self.num_sets - 1
        
        self.sets: List[List[CacheBlock]] = [
            [CacheBlock() for _ in range(ways)] for _ in range(self.num_sets)
        ]
        
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def parse_address(self, addr: int) -> Tuple[int, int, int]:
        offset = addr & ((1 << self.offset_bits) - 1)
        set_idx = (addr >> self.offset_bits) & self.set_mask
        tag = addr >> (self.offset_bits + self.set_bits)
        return tag, set_idx, offset

    def probe(self, addr: int) -> Tuple[bool, int]:
        tag, set_idx, _ = self.parse_address(addr)
        lines = self.sets[set_idx]
        for idx, line in enumerate(lines):
            if line.valid and line.tag == tag:
                return True, idx
        return False, -1

    def access(self, addr: int, domain_id: int, current_time: int, way_mask: Optional[Tuple[int, int]] = None, is_sensitive: bool = False) -> Tuple[bool, Optional[CacheBlock], int]:
        tag, set_idx, _ = self.parse_address(addr)
        lines = self.sets[set_idx]
        start_way, end_way = (0, self.ways) if way_mask is None else way_mask
        
        # Check Hit in allocated ways
        for idx in range(start_way, end_way):
            line = lines[idx]
            if line.valid and line.tag == tag:
                self.hits += 1
                line.last_access_time = current_time
                line.access_count += 1
                if is_sensitive:
                    line.is_sensitive = True
                return True, None, set_idx
        
        # Miss: Find invalid block or LRU victim
        self.misses += 1
        invalid_idx = -1
        lru_idx = start_way
        min_time = float('inf')
        
        for idx in range(start_way, end_way):
            line = lines[idx]
            if not line.valid:
                invalid_idx = idx
                break
            if line.last_access_time < min_time:
                min_time = line.last_access_time
                lru_idx = idx
        
        evicted = None
        target_idx = invalid_idx if invalid_idx != -1 else lru_idx
        target_line = lines[target_idx]
        
        if target_line.valid:
            self.evictions += 1
            evicted = CacheBlock(target_line.tag, target_line.valid, target_line.dirty, target_line.domain_id, target_line.is_sensitive)
            evicted.in_private_cache = target_line.in_private_cache
        
        target_line.tag = tag
        target_line.valid = True
        target_line.dirty = False
        target_line.domain_id = domain_id
        target_line.is_sensitive = is_sensitive
        target_line.last_access_time = current_time
        target_line.access_count = 1
        target_line.in_private_cache = False
        
        return False, evicted, set_idx

    def invalidate(self, addr: int) -> bool:
        tag, set_idx, _ = self.parse_address(addr)
        for line in self.sets[set_idx]:
            if line.valid and line.tag == tag:
                line.valid = False
                return True
        return False


class BufferEntry:
    """Represents an entry inside the Eviction-Hidden Buffer (EHB)."""
    def __init__(self, block_addr: int, block: CacheBlock, current_time: int, is_sensitive: bool = False):
        self.block_addr = block_addr
        self.block = block
        self.domain_id = block.domain_id
        self.insertion_time = current_time
        self.last_access_time = current_time
        self.freq_counter = 1            # 4-bit saturating counter (0-15)
        self.is_sensitive = is_sensitive or block.is_sensitive
        self.sensitivity_score = 3.0 if self.is_sensitive else 1.0


class EvictionHiddenBuffer:
    """
    Standard TreasureCache Eviction-Hidden Buffer (EHB).
    - Fully-associative buffer.
    - Parameterized capacity (default 64 lines = 4 KB for 2-core model).
    - Domain ownership quota: Each domain can own up to capacity // num_domains slots.
    - Secure Replacement: Evicts oldest entry belonging to allocating domain, or LRU unowned.
    """
    def __init__(self, capacity_lines: int = 64, hit_latency: int = 40, num_domains: int = 2):
        self.capacity = capacity_lines
        self.hit_latency = hit_latency
        self.num_domains = num_domains
        self.domain_quota = max(1, capacity_lines // num_domains)
        self.entries: Dict[int, BufferEntry] = {}
        
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def contains(self, block_addr: int) -> bool:
        return block_addr in self.entries

    def access(self, block_addr: int, current_time: int) -> bool:
        if block_addr in self.entries:
            self.hits += 1
            entry = self.entries[block_addr]
            entry.last_access_time = current_time
            if entry.freq_counter < 15:
                entry.freq_counter += 1
            return True
        self.misses += 1
        return False

    def insert(self, block_addr: int, block: CacheBlock, current_time: int, is_sensitive: bool = False) -> Optional[int]:
        if block_addr in self.entries:
            self.entries[block_addr].last_access_time = current_time
            return None

        evicted_addr = None
        domain_id = block.domain_id

        if len(self.entries) >= self.capacity:
            # Standard TreasureCache Ownership Replacement Policy:
            # When capacity is exceeded, evict the LRU block among eligible entries
            domain_entries = [k for k, v in self.entries.items() if v.domain_id == domain_id]
            if len(domain_entries) >= self.domain_quota:
                evict_candidate = min(domain_entries, key=lambda k: self.entries[k].last_access_time)
            else:
                evict_candidate = min(self.entries.keys(), key=lambda k: self.entries[k].last_access_time)
            
            del self.entries[evict_candidate]
            self.evictions += 1
            evicted_addr = evict_candidate

        self.entries[block_addr] = BufferEntry(block_addr, block, current_time, is_sensitive)
        return evicted_addr

    def remove(self, block_addr: int) -> bool:
        if block_addr in self.entries:
            del self.entries[block_addr]
            return True
        return False


class AdaptiveEvictionHiddenBuffer(EvictionHiddenBuffer):
    """
    Proposed Ada-EHB: Adaptive Frequency-Aware Eviction-Hidden Buffer.
    
    Formal Mathematical Specification:
      1. Retention Score:
         R(k) = [ S(k) * (1 + alpha * F(k)) ] / ln(1 + Age(k) + epsilon)
         where:
           - S(k): Sensitivity weight (3.0 for sensitive/cross-domain blocks, 1.0 for normal)
           - F(k): 4-bit saturating frequency counter (0 <= F(k) <= 15)
           - alpha: Frequency importance weight (0.2)
           - Age(k): current_time - last_access_time (in cycles)
           - epsilon: 1e-5 (prevents division by zero)
      
      2. Replacement Rule:
         When buffer is full, evict the entry with the lowest Retention Score:
         k_evict = argmin_{k in Entries} R(k).
         If all resident blocks have higher retention than the incoming block, the incoming block
         bypasses the buffer to DRAM, preventing attacker thrashing from poisoning the buffer.
      
      3. Burst Rate Limiting:
         Token-bucket rate limiter per domain. Maximum burst allocations M = 8 per window W = 1000 cycles.
         High-rate streaming evictions exceeding M are bypassed directly to DRAM.
    """
    def __init__(self, capacity_lines: int = 64, hit_latency: int = 40, num_domains: int = 2):
        super().__init__(capacity_lines, hit_latency, num_domains)
        self.alpha = 0.2
        self.epsilon = 1e-5
        
        self.burst_tokens = {d: 8.0 for d in range(num_domains)}
        self.last_token_update = {d: 0 for d in range(num_domains)}
        self.max_tokens = 8.0
        self.refill_rate = 1.0 / 125.0

    def _update_tokens(self, domain_id: int, current_time: int):
        elapsed = max(0, current_time - self.last_token_update[domain_id])
        self.burst_tokens[domain_id] = min(
            self.max_tokens,
            self.burst_tokens[domain_id] + elapsed * self.refill_rate
        )
        self.last_token_update[domain_id] = current_time

    def compute_retention_score(self, entry: BufferEntry, current_time: int) -> float:
        age = max(1, current_time - entry.last_access_time)
        numerator = entry.sensitivity_score * (1.0 + self.alpha * entry.freq_counter)
        denominator = math.log(1.0 + age + self.epsilon)
        return numerator / denominator

    def insert(self, block_addr: int, block: CacheBlock, current_time: int, is_sensitive: bool = False) -> Optional[int]:
        if block_addr in self.entries:
            entry = self.entries[block_addr]
            entry.last_access_time = current_time
            if entry.freq_counter < 15:
                entry.freq_counter += 1
            return None

        effective_sensitive = is_sensitive or block.is_sensitive
        domain_id = block.domain_id
        self._update_tokens(domain_id, current_time)

        # Mechanism 3: Burst Rate Limiting
        # Non-sensitive burst evictions from high-churn domains are rate-limited
        if not effective_sensitive and self.burst_tokens[domain_id] < 1.0:
            # Bypass buffer directly to DRAM
            return None

        if not effective_sensitive:
            self.burst_tokens[domain_id] -= 1.0

        new_entry = BufferEntry(block_addr, block, current_time, effective_sensitive)
        new_score = self.compute_retention_score(new_entry, current_time)

        evicted_addr = None
        if len(self.entries) >= self.capacity:
            # Mechanism 2: Retention-Based Replacement
            min_score = float('inf')
            min_key = None
            
            for k, entry in self.entries.items():
                score = self.compute_retention_score(entry, current_time)
                if score < min_score:
                    min_score = score
                    min_key = k

            # Sticky Residency & Bypass Decision:
            # If the candidate to insert has lower retention than all resident blocks,
            # bypass to DRAM rather than displacing a more critical resident line.
            if new_score <= min_score and not effective_sensitive:
                return None

            # Evict lowest retention entry
            del self.entries[min_key]
            self.evictions += 1
            evicted_addr = min_key

        self.entries[block_addr] = new_entry
        return evicted_addr


class MultiCoreCacheSystem:
    def __init__(self, mode: str = 'none', ehb_capacity: int = 64):
        self.mode = mode
        self.current_time = 0
        
        # Latency constants (CPU cycles)
        self.LATENCY_L1 = 4
        self.LATENCY_L2 = 12
        self.LATENCY_LLC = 38
        self.LATENCY_EHB = 40
        self.LATENCY_DRAM = 200
        
        self.l1_cores = [
            SetAssociativeCache("L1_Core0", size_bytes=32 * 1024, ways=8, hit_latency=self.LATENCY_L1),
            SetAssociativeCache("L1_Core1", size_bytes=32 * 1024, ways=8, hit_latency=self.LATENCY_L1)
        ]
        
        self.l2_cores = [
            SetAssociativeCache("L2_Core0", size_bytes=256 * 1024, ways=8, hit_latency=self.LATENCY_L2),
            SetAssociativeCache("L2_Core1", size_bytes=256 * 1024, ways=8, hit_latency=self.LATENCY_L2)
        ]
        
        self.llc = SetAssociativeCache("LLC_Shared", size_bytes=2 * 1024 * 1024, ways=16, hit_latency=self.LATENCY_LLC)
        
        self.partition_masks = {
            0: (0, 8),
            1: (8, 16)
        }
        
        if mode == 'treasure_cache':
            self.ehb = EvictionHiddenBuffer(capacity_lines=ehb_capacity, hit_latency=self.LATENCY_EHB, num_domains=2)
        elif mode == 'ada_ehb':
            self.ehb = AdaptiveEvictionHiddenBuffer(capacity_lines=ehb_capacity, hit_latency=self.LATENCY_EHB, num_domains=2)
        else:
            self.ehb = None

    def tick(self, cycles: int = 1):
        self.current_time += cycles

    def read_address(self, core_id: int, addr: int, domain_id: int, is_sensitive: bool = False) -> Tuple[int, str]:
        block_addr = addr >> 6
        
        # 1. Private L1
        l1 = self.l1_cores[core_id]
        l1_hit, _, _ = l1.access(addr, domain_id, self.current_time, is_sensitive=is_sensitive)
        if l1_hit:
            self.tick(self.LATENCY_L1)
            return self.LATENCY_L1, "L1_HIT"
        
        # 2. Private L2
        l2 = self.l2_cores[core_id]
        l2_hit, _, _ = l2.access(addr, domain_id, self.current_time, is_sensitive=is_sensitive)
        if l2_hit:
            self.tick(self.LATENCY_L2)
            return self.LATENCY_L2, "L2_HIT"
        
        # 3. Check EHB
        if self.ehb and self.ehb.contains(block_addr):
            self.ehb.access(block_addr, self.current_time)
            latency = self.LATENCY_EHB + random.choice([0, 1, 2])
            self.tick(latency)
            # Bring block into L1/L2 on hit
            l1.access(addr, domain_id, self.current_time, is_sensitive=is_sensitive)
            l2.access(addr, domain_id, self.current_time, is_sensitive=is_sensitive)
            return latency, "EHB_HIT"
        
        # 4. Check Shared LLC
        way_mask = self.partition_masks[domain_id] if self.mode == 'partitioned' else None
        llc_hit, evicted_block, set_idx = self.llc.access(addr, domain_id, self.current_time, way_mask=way_mask, is_sensitive=is_sensitive)
        
        # Handle LLC eviction: inclusive back-invalidation & EHB secure placement
        if evicted_block is not None:
            evicted_addr = (evicted_block.tag << (self.llc.set_bits + self.llc.offset_bits)) | (set_idx << self.llc.offset_bits)
            
            # Inclusive back-invalidation to L1 & L2
            for c_idx in range(2):
                self.l1_cores[c_idx].invalidate(evicted_addr)
                self.l2_cores[c_idx].invalidate(evicted_addr)
            
            # Secure Placement Policy (TreasureCache Condition 1 & 2):
            if self.ehb is not None:
                if evicted_block.domain_id == 0 or evicted_block.is_sensitive:
                    cloned_block = CacheBlock(evicted_block.tag, True, False, evicted_block.domain_id, evicted_block.is_sensitive)
                    self.ehb.insert(evicted_addr >> 6, cloned_block, self.current_time, is_sensitive=evicted_block.is_sensitive)

        if llc_hit:
            if self.ehb and self.ehb.contains(block_addr):
                self.ehb.remove(block_addr)
            self.tick(self.LATENCY_LLC)
            return self.LATENCY_LLC, "LLC_HIT"
        
        # 5. Miss -> DRAM access
        if self.ehb and self.ehb.contains(block_addr):
            self.ehb.remove(block_addr)
            
        latency = self.LATENCY_DRAM + random.randint(-4, 8)
        self.tick(latency)
        return latency, "DRAM_MISS"

    def clflush(self, core_id: int, addr: int) -> int:
        block_addr = addr >> 6
        was_cached = False
        
        for c in range(2):
            if self.l1_cores[c].invalidate(addr) or self.l2_cores[c].invalidate(addr):
                was_cached = True
        if self.llc.invalidate(addr):
            was_cached = True
        if self.ehb and self.ehb.remove(block_addr):
            was_cached = True
            
        if self.mode in ['treasure_cache', 'ada_ehb']:
            flush_latency = 70 + random.choice([0, 1])
        else:
            flush_latency = 95 if was_cached else 45
            
        self.tick(flush_latency)
        return flush_latency
