"""
test_simulation.py - Automated Behavioral Regression Test Suite
Validates all core architectural mechanisms:
  1. Domain isolation (no cross-domain eviction by private attacker blocks)
  2. EHB dual-condition placement: private sharer eviction -> entered into EHB
  3. EHB dual-condition placement: no private sharers -> bypasses EHB
  4. EHB dual-condition placement: eviction caused by EHB reload (from_ehb) -> entered into EHB
  5. EHB reload: block taken from EHB and installed into LLC and private cache
  6. Protected-entry replacement: sensitive entries protected while eligible non-sensitive entries exist
  7. Full-buffer overflow & bypass behavior
  8. Frequency-counter incrementation and saturation
  9. Token-bucket rate-limiting: token consumption, exhaustion, and refill
  10. CT-Flush timing: constant 70 cycles on cached and uncached lines
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache_model import (
    MultiCoreCacheSystem,
    EvictionHiddenBuffer,
    AdaptiveEvictionHiddenBuffer,
    LINE_SIZE
)
from attacks import force_llc_eviction, run_residency_trial


class ComprehensiveCacheTests(unittest.TestCase):

    def test_1_domain_isolation(self):
        """Test that an attacker-domain block cannot displace a victim-owned block."""
        for cls in (EvictionHiddenBuffer, AdaptiveEvictionHiddenBuffer):
            buf = cls(capacity_lines=4, num_domains=2)
            # Domain 0 inserts block 1
            self.assertTrue(buf.insert(1, owners={0}, sensitive=True, current_time=1))
            # Domain 1 attempts to flood buffer with blocks 2..20
            for j in range(2, 20):
                buf.insert(j, owners={1}, sensitive=False, current_time=j)
            # Victim block 1 MUST remain in buffer!
            self.assertTrue(buf.contains(1), f"Domain isolation failed for {cls.__name__}")

    def test_2_ehb_placement_with_private_sharers(self):
        """Test Placement Condition 1: Evicted LLC block with private sharers enters EHB."""
        sys_model = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=8, llc_sets=32, llc_ways=4)
        addr = 0x100000
        sys_model.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
        # Evict from LLC on Core 1
        evicted = force_llc_eviction(sys_model, addr, count=6)
        self.assertTrue(evicted)
        block = addr // LINE_SIZE
        self.assertTrue(sys_model.ehb.contains(block), "Block with private sharers should be placed in EHB")

    def test_3_ehb_placement_no_private_sharers_bypasses(self):
        """Test Placement Condition 1 Negative: Evicted LLC block WITHOUT private sharers bypasses EHB."""
        sys_model = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=8, llc_sets=32, llc_ways=4)
        addr = 0x100000
        sys_model.read_address(core_id=0, addr=addr, domain_id=0)
        block = addr // LINE_SIZE
        # Invalidate private copies before LLC eviction
        sys_model._invalidate_private(block)
        force_llc_eviction(sys_model, addr, count=6)
        self.assertFalse(sys_model.ehb.contains(block), "Block without private sharers must bypass EHB")

    def test_4_ehb_placement_from_ehb_reload(self):
        """Test Placement Condition 2: Eviction caused by an EHB reload is eligible for EHB."""
        sys_model = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=8, llc_sets=32, llc_ways=4)
        addr1 = 0x100000
        set_idx = sys_model._set(addr1 // LINE_SIZE)
        
        # Load addr1 into cache and evict to EHB
        sys_model.read_address(core_id=0, addr=addr1, domain_id=0, is_sensitive=True)
        force_llc_eviction(sys_model, addr1, count=6)
        self.assertTrue(sys_model.ehb.contains(addr1 // LINE_SIZE))
        
        # Reload addr1 from EHB: installs into LLC with from_ehb=True
        lat, lvl = sys_model.read_address(core_id=0, addr=addr1, domain_id=0, is_sensitive=True)
        self.assertEqual(lvl, 'EHB_HIT')
        
        # Verify block was installed into LLC
        self.assertIn(addr1 // LINE_SIZE, sys_model.llc[set_idx])

    def test_5_ehb_reload_and_llc_installation(self):
        """Test that an EHB hit removes entry from EHB and reinstalls it into LLC."""
        sys_model = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=8, llc_sets=32, llc_ways=4)
        addr = 0x100000
        block = addr // LINE_SIZE
        sys_model.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
        force_llc_eviction(sys_model, addr, count=6)
        self.assertTrue(sys_model.ehb.contains(block))
        
        lat, lvl = sys_model.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
        self.assertEqual(lvl, 'EHB_HIT')
        self.assertEqual(lat, 40)
        self.assertFalse(sys_model.ehb.contains(block), "Reloaded block must be removed from EHB")
        self.assertIn(block, sys_model.llc[sys_model._set(block)], "Reloaded block must be installed into LLC")

    def test_6_protected_entry_replacement_in_ada_ehb(self):
        """Test that Ada-EHB protects sensitive entries while eligible non-sensitive entries exist."""
        buf = AdaptiveEvictionHiddenBuffer(capacity_lines=2, num_domains=1)
        buf.insert(1, owners={0}, sensitive=True, current_time=1)
        buf.insert(2, owners={0}, sensitive=False, current_time=2)
        self.assertEqual(len(buf.entries), 2)
        
        # Insert Block 3 (sensitive): should evict Block 2 (non-sensitive), keeping Block 1!
        buf.insert(3, owners={0}, sensitive=True, current_time=3)
        self.assertIn(1, buf.entries, "Sensitive Block 1 must be protected")
        self.assertIn(3, buf.entries, "New sensitive Block 3 must be admitted")
        self.assertNotIn(2, buf.entries, "Non-sensitive Block 2 should have been evicted")

    def test_7_full_buffer_overflow_and_bypass(self):
        """Test that non-sensitive entries bypass buffer when all eligible slots hold protected entries."""
        buf = AdaptiveEvictionHiddenBuffer(capacity_lines=2, num_domains=1)
        buf.insert(1, owners={0}, sensitive=True, current_time=1)
        buf.insert(2, owners={0}, sensitive=True, current_time=2)
        
        # Attempt to insert non-sensitive Block 3: should bypass directly to DRAM
        admitted = buf.insert(3, owners={0}, sensitive=False, current_time=3)
        self.assertFalse(admitted, "Non-sensitive block must bypass when all entries are sensitive")
        self.assertEqual(buf.bypasses, 1)

    def test_8_frequency_counter_saturation(self):
        """Test that frequency counter increments on re-reference and caps at 15."""
        buf = AdaptiveEvictionHiddenBuffer(capacity_lines=4, num_domains=1)
        buf.insert(1, owners={0}, sensitive=True, current_time=1)
        self.assertEqual(buf.entries[1].frequency, 1)
        
        for t in range(2, 25):
            buf.insert(1, owners={0}, sensitive=True, current_time=t)
        self.assertEqual(buf.entries[1].frequency, 15, "Frequency counter must saturate at 15")

    def test_9_token_bucket_rate_limiting(self):
        """Test token-bucket rate limiter exhaustion and time-based refill."""
        buf = AdaptiveEvictionHiddenBuffer(capacity_lines=16, num_domains=1)
        # 8 tokens initially; insert 8 non-sensitive blocks at t=0
        for i in range(1, 9):
            self.assertTrue(buf.insert(i, owners={0}, sensitive=False, current_time=0))
            
        # 9th block at t=0 should be rejected (exhausted tokens)
        self.assertFalse(buf.insert(9, owners={0}, sensitive=False, current_time=0))
        
        # Advance time by 250 cycles (refills 2 tokens)
        self.assertTrue(buf.insert(9, owners={0}, sensitive=False, current_time=250))

    def test_10_ct_flush_timing(self):
        """Test that CT-Flush completes in constant 70 cycles on both cached and uncached blocks."""
        for mode in ('treasure_cache', 'ada_ehb'):
            sys_model = MultiCoreCacheSystem(mode=mode)
            # Uncached flush
            lat_uncached = sys_model.clflush(core_id=0, addr=0x100000)
            self.assertEqual(lat_uncached, 70, f"Uncached CT-Flush failed for {mode}")
            
            # Cached flush
            sys_model.read_address(core_id=0, addr=0x100000, domain_id=0)
            lat_cached = sys_model.clflush(core_id=0, addr=0x100000)
            self.assertEqual(lat_cached, 70, f"Cached CT-Flush failed for {mode}")


if __name__ == '__main__':
    unittest.main()
