"""
cache_model.py - Hardware Cache Hierarchy and TreasureCache Simulation Model
Models multi-level inclusive cache hierarchy (L1/L2 private, LLC shared)
and implements:
  1. Standard Unprotected LRU Cache
  2. Baseline Partitioned Cache (Way-Partitioning / Intel CAT style)
  3. TreasureCache with Eviction-Hidden Buffer (EHB) & Constant-Time Flush
  4. Proposed Adaptive Eviction-Hidden Buffer (Ada-EHB)
"""

import math
import random
from typing import Dict, List, Optional, Tuple, Set


class CacheBlock:
    """Represents a single cache block/line."""
    def __init__(self, tag: int = 0, valid: bool = False, dirty: bool = False, domain_id: int = 0):
        self.tag: int = tag
        self.valid: bool = valid
        self.dirty: bool = dirty
        self.domain_id: int = domain_id  # 0: victim, 1: attacker
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
        
        # sets[set_idx] = list of CacheBlock (length = ways)
        self.sets: List[List[CacheBlock]] = [
            [CacheBlock() for _ in range(ways)] for _ in range(self.num_sets)
        ]
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def parse_address(self, addr: int) -> Tuple[int, int, int]:
        """Splits address into tag, set_index, offset."""
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

    def access(self, addr: int, domain_id: int, current_time: int, way_mask: Optional[Tuple[int, int]] = None) -> Tuple[bool, Optional[CacheBlock], int]:
        """
        Simulates access.
        way_mask: optional (start_way, end_way) for cache partitioning.
        Returns: (is_hit, evicted_block, set_idx)
        """
        tag, set_idx, _ = self.parse_address(addr)
        lines = self.sets[set_idx]
        start_way, end_way = (0, self.ways) if way_mask is None else way_mask
        
        # Check Hit in allocated ways (or all ways if shared)
        for idx in range(start_way, end_way):
            line = lines[idx]
            if line.valid and line.tag == tag:
                self.hits += 1
                line.last_access_time = current_time
                line.access_count += 1
                return True, None, set_idx
        
        # Miss: Find invalid block or LRU victim strictly within allocated ways
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
            evicted = CacheBlock(target_line.tag, target_line.valid, target_line.dirty, target_line.domain_id)
            evicted.in_private_cache = target_line.in_private_cache
        
        target_line.tag = tag
        target_line.valid = True
        target_line.dirty = False
        target_line.domain_id = domain_id
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


class EvictionHiddenBuffer:
    """
    TreasureCache Eviction-Hidden Buffer (EHB).
    Fully-associative buffer that hides sensitive evictions.
    Access latency: matched to LLC hit (~40 cycles).
    """
    def __init__(self, capacity_lines: int = 64, hit_latency: int = 40):
        self.capacity = capacity_lines
        self.hit_latency = hit_latency
        self.entries: Dict[int, CacheBlock] = {}
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def contains(self, block_addr: int) -> bool:
        return block_addr in self.entries

    def access(self, block_addr: int, current_time: int) -> bool:
        if block_addr in self.entries:
            self.hits += 1
            self.entries[block_addr].last_access_time = current_time
            self.entries[block_addr].access_count += 1
            return True
        self.misses += 1
        return False

    def insert(self, block_addr: int, block: CacheBlock, current_time: int) -> Optional[int]:
        evicted_addr = None
        if len(self.entries) >= self.capacity and block_addr not in self.entries:
            lru_key = min(self.entries.keys(), key=lambda k: self.entries[k].last_access_time)
            del self.entries[lru_key]
            self.evictions += 1
            evicted_addr = lru_key
        
        block.last_access_time = current_time
        self.entries[block_addr] = block
        return evicted_addr

    def remove(self, block_addr: int) -> bool:
        if block_addr in self.entries:
            del self.entries[block_addr]
            return True
        return False


class AdaptiveEvictionHiddenBuffer(EvictionHiddenBuffer):
    """
    Our Proposed Extension: Adaptive Frequency-Aware Eviction-Hidden Buffer (Ada-EHB).
    Addresses the vulnerability where an attacker rapidly flushes/primes lines to saturate
    and thrash the small fixed EHB.
    """
    def __init__(self, capacity_lines: int = 64, hit_latency: int = 40):
        super().__init__(capacity_lines, hit_latency)
        self.sensitivity_scores: Dict[int, float] = {}

    def insert_adaptive(self, block_addr: int, block: CacheBlock, current_time: int, is_victim_critical: bool) -> Optional[int]:
        evicted_addr = None
        score = 3.0 if is_victim_critical else 1.0
        self.sensitivity_scores[block_addr] = score
        
        if len(self.entries) >= self.capacity and block_addr not in self.entries:
            def replacement_priority(k):
                age = max(1, current_time - self.entries[k].last_access_time)
                sens = self.sensitivity_scores.get(k, 1.0)
                return sens / math.log1p(age)
            
            evict_candidate = min(self.entries.keys(), key=replacement_priority)
            del self.entries[evict_candidate]
            if evict_candidate in self.sensitivity_scores:
                del self.sensitivity_scores[evict_candidate]
            self.evictions += 1
            evicted_addr = evict_candidate

        block.last_access_time = current_time
        self.entries[block_addr] = block
        return evicted_addr


class MultiCoreCacheSystem:
    """
    Simulates a multi-core system with inclusive LLC.
    Defense modes:
      - 'none': Standard inclusive cache, vulnerable to eviction side channels
      - 'partitioned': Static cache way-partitioning (Intel CAT style)
      - 'treasure_cache': TreasureCache EHB + CT-Flush
      - 'ada_ehb': Proposed Adaptive EHB
    """
    def __init__(self, mode: str = 'none', ehb_capacity: int = 64):
        self.mode = mode
        self.current_time = 0
        
        # Latencies in CPU cycles
        self.LATENCY_L1 = 4
        self.LATENCY_L2 = 12
        self.LATENCY_LLC = 38
        self.LATENCY_EHB = 40
        self.LATENCY_DRAM = 200
        
        # Private L1 D-Cache per core (32 KB, 8-way, line=64B)
        self.l1_cores = [
            SetAssociativeCache("L1_Core0", size_bytes=32 * 1024, ways=8, hit_latency=self.LATENCY_L1),
            SetAssociativeCache("L1_Core1", size_bytes=32 * 1024, ways=8, hit_latency=self.LATENCY_L1)
        ]
        
        # Private L2 Cache per core (256 KB, 8-way, line=64B)
        self.l2_cores = [
            SetAssociativeCache("L2_Core0", size_bytes=256 * 1024, ways=8, hit_latency=self.LATENCY_L2),
            SetAssociativeCache("L2_Core1", size_bytes=256 * 1024, ways=8, hit_latency=self.LATENCY_L2)
        ]
        
        # Shared inclusive LLC (2 MB, 16-way, line=64B)
        self.llc = SetAssociativeCache("LLC_Shared", size_bytes=2 * 1024 * 1024, ways=16, hit_latency=self.LATENCY_LLC)
        
        # Partitioning way allocation (if active: Core0/Victim gets 0..7, Core1/Attacker gets 8..15)
        self.partition_masks = {
            0: (0, 8),
            1: (8, 16)
        }
        
        # TreasureCache EHB
        if mode == 'treasure_cache':
            self.ehb = EvictionHiddenBuffer(capacity_lines=ehb_capacity, hit_latency=self.LATENCY_EHB)
        elif mode == 'ada_ehb':
            self.ehb = AdaptiveEvictionHiddenBuffer(capacity_lines=ehb_capacity, hit_latency=self.LATENCY_EHB)
        else:
            self.ehb = None

    def tick(self, cycles: int = 1):
        self.current_time += cycles

    def read_address(self, core_id: int, addr: int, domain_id: int, is_sensitive: bool = False) -> Tuple[int, str]:
        block_addr = addr >> 6
        
        # 1. Private L1
        l1 = self.l1_cores[core_id]
        l1_hit, _, _ = l1.access(addr, domain_id, self.current_time)
        if l1_hit:
            self.tick(self.LATENCY_L1)
            return self.LATENCY_L1, "L1_HIT"
        
        # 2. Private L2
        l2 = self.l2_cores[core_id]
        l2_hit, _, _ = l2.access(addr, domain_id, self.current_time)
        if l2_hit:
            self.tick(self.LATENCY_L2)
            return self.LATENCY_L2, "L2_HIT"
        
        # 3. Check TreasureCache EHB
        # If line is in EHB, it serves the hit at LLC-comparable speed (~40 cycles)
        if self.ehb and self.ehb.contains(block_addr):
            self.ehb.access(block_addr, self.current_time)
            latency = self.LATENCY_EHB + random.choice([0, 1, 2])
            self.tick(latency)
            return latency, "EHB_HIT"
        
        # 4. Check Shared LLC
        way_mask = self.partition_masks[domain_id] if self.mode == 'partitioned' else None
        llc_hit, evicted_block, set_idx = self.llc.access(addr, domain_id, self.current_time, way_mask=way_mask)
        
        # If LLC eviction happened:
        if evicted_block is not None:
            # Reconstruct exact physical address of evicted block
            evicted_addr = (evicted_block.tag << (self.llc.set_bits + self.llc.offset_bits)) | (set_idx << self.llc.offset_bits)
            
            # Inclusive cache requirement: back-invalidate private caches
            for c_idx in range(2):
                self.l1_cores[c_idx].invalidate(evicted_addr)
                self.l2_cores[c_idx].invalidate(evicted_addr)
            
            # TreasureCache Secure Placement:
            # Buffer sensitive/victim evicted lines into EHB
            if self.ehb is not None:
                if evicted_block.domain_id == 0 or is_sensitive:
                    cloned_block = CacheBlock(evicted_block.tag, True, False, evicted_block.domain_id)
                    if self.mode == 'ada_ehb':
                        self.ehb.insert_adaptive(evicted_addr >> 6, cloned_block, self.current_time, is_sensitive)
                    else:
                        self.ehb.insert(evicted_addr >> 6, cloned_block, self.current_time)

        if llc_hit:
            if self.ehb and self.ehb.contains(block_addr):
                self.ehb.remove(block_addr)
            self.tick(self.LATENCY_LLC)
            return self.LATENCY_LLC, "LLC_HIT"
        
        # 5. Miss -> DRAM
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
            # Constant-Time Flush (CT-Flush)
            flush_latency = 70 + random.choice([0, 1])
        else:
            flush_latency = 95 if was_cached else 45
            
        self.tick(flush_latency)
        return flush_latency
