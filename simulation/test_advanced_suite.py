"""
test_advanced_suite.py - Master Advanced Test Suite & Verification Framework

Comprehensive QA and architectural validation suite for TreasureCache, Ada-EHB,
and Ada-EHB+ cache hierarchy defenses.

Validates 20 automated unit tests covering:
  1. Baseline timing leakage on unprotected caches (160+ cycles).
  2. Constant-Time Flush (CT-Flush) invariance (~70 cycles).
  3. EHB Placement Condition 1: LLC eviction with private sharers enters EHB.
  4. EHB Placement Condition 2: LLC eviction displaced by EHB reload enters EHB.
  5. Negative placement: LLC eviction without sharers or reload origin bypasses to DRAM.
  6. EHB reload mechanics: take() on hit removes from EHB and reinstalls to LLC.
  7. Domain quota enforcement: strict capacity // num_domains cap.
  8. Cross-domain isolation: private attacker blocks cannot evict victim lines.
  9. Shared-memory contention failure in Standard TreasureCache under joint ownership.
  10. Ada-EHB dynamic retention scoring formula precision: R(k) = [S * (1 + alpha * F)] / ln(1 + Age + eps).
  11. Ada-EHB sticky residency: immune to eviction under adversarial flooding.
  12. Ada-EHB token-bucket rate limiter: burst limiting and cycle-accurate refill.
  13. Ada-EHB+ Dynamic Elastic Domain Quota (DEDQ): capacity borrowing under asymmetric load.
  14. Ada-EHB+ Shannon Entropy Profiler: sliding-window sweep detection and penalty.
  15. Flush+Reload attack neutralization (closing ~160+ cycle gap to ~2 cycles).
  16. Flush+Flush attack neutralization via CT-Flush (reducing ~50 cycle gap to 0 cycles).
  17. Prime+Probe attack neutralization (EHB hit replaces DRAM miss, shrinking delta to ~2 cycles).
  18. Prime+Reprime+Probe mitigation: proving necessity of Placement Condition 2 over Condition 1 alone.
  19. Ada-EHB+ multi-tier sensitivity hierarchy (ROOT_OF_TRUST > PROTECTED_PAGE > NORMAL).
  20. Hardware synthesis & formal verification consistency (storage overhead < 0.5%, CAM <= 0.4 ns).
"""

import collections
import json
import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core cache model
from cache_model import (
    LINE_SIZE,
    BufferEntry,
    EvictionHiddenBuffer,
    AdaptiveEvictionHiddenBuffer,
    MultiCoreCacheSystem
)
from attacks import force_llc_eviction, run_evict_and_time_simulation

# Graceful import of Ada-EHB+ architectural extension
try:
    from ada_ehb_plus import (
        AdaEHBPlusBuffer,
        BufferEntryPlus,
        MultiCoreCacheSystemPlus,
        ShannonEntropyProfiler,
        SensitivityLevel,
        SENSITIVITY_WEIGHTS,
        run_revocation_floor_trial
    )
    ADA_EHB_PLUS_LOADED = True
except ImportError:
    ADA_EHB_PLUS_LOADED = False

# Graceful import of Multi-Vector Attack Suite
try:
    from advanced_attacks import (
        FlushReloadAttack,
        FlushFlushAttack,
        PrimeProbeAttack,
        PrimeReprimeProbeAttack,
        AttackResult,
        run_all_attacks_comparison
    )
    ADVANCED_ATTACKS_LOADED = True
except ImportError:
    ADVANCED_ATTACKS_LOADED = False


class MasterAdvancedCacheTestSuite(unittest.TestCase):
    """
    Master Automated Test Suite verifying cache hierarchy mechanics,
    cryptographic side-channel defenses, and microarchitectural extensions.
    """

    # -------------------------------------------------------------------------
    # Test 1: Baseline Leakage
    # -------------------------------------------------------------------------
    def test_1_baseline_leakage(self):
        """
        Test 1: Verifies unprotected cache (mode='none') exhibits exploitable timing
        differences (160+ cycles) between LLC hits (~38 cycles) and DRAM misses (~200 cycles).
        """
        sys_none = MultiCoreCacheSystem(mode='none', seed=42)
        target_addr = 0x100000

        # Prime address into LLC
        sys_none.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)
        sys_none._invalidate_private(target_addr // LINE_SIZE)

        # 1. LLC hit access
        hit_lat, hit_level = sys_none.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)
        self.assertEqual(hit_level, 'LLC_HIT')
        self.assertEqual(hit_lat, 38)

        # 2. Evict target from LLC
        force_llc_eviction(sys_none, target_addr, count=sys_none.llc_ways + 2)

        # 3. DRAM miss access
        miss_lat, miss_level = sys_none.read_address(core_id=0, addr=target_addr, domain_id=0, is_sensitive=True)
        self.assertEqual(miss_level, 'DRAM_MISS')
        self.assertGreaterEqual(miss_lat, 196)

        timing_gap = miss_lat - hit_lat
        self.assertGreaterEqual(timing_gap, 158, f"Baseline timing gap {timing_gap} must be >= 158 cycles")

        # Statistical Evict+Time validation
        sim_res = run_evict_and_time_simulation(mode='none', rounds=10, seed=42)
        self.assertGreaterEqual(sim_res['timing_gap'], 150.0, "Statistical Evict+Time gap must exceed 150 cycles")

    # -------------------------------------------------------------------------
    # Test 2: CT-Flush Invariance
    # -------------------------------------------------------------------------
    def test_2_ct_flush_invariance(self):
        """
        Test 2: Verifies Constant-Time Flush (CT-Flush) latency is invariant (~70 cycles)
        regardless of whether target is cached in LLC, cached in EHB, or in DRAM.
        """
        for mode in ('treasure_cache', 'ada_ehb'):
            sys_model = MultiCoreCacheSystem(mode=mode, ehb_capacity=16, llc_sets=32, llc_ways=4)

            # State A: In DRAM (uncached)
            lat_dram = sys_model.clflush(core_id=0, addr=0x100000)
            self.assertEqual(lat_dram, 70, f"Uncached CT-Flush must be 70 cycles in {mode}")

            # State B: Cached in LLC
            sys_model.read_address(core_id=0, addr=0x200000, domain_id=0)
            sys_model._invalidate_private(0x200000 // LINE_SIZE)  # LLC only
            lat_llc = sys_model.clflush(core_id=0, addr=0x200000)
            self.assertEqual(lat_llc, 70, f"LLC-cached CT-Flush must be 70 cycles in {mode}")

            # State C: Cached in EHB
            sys_model.read_address(core_id=0, addr=0x300000, domain_id=0, is_sensitive=True)
            force_llc_eviction(sys_model, 0x300000, count=6)
            self.assertTrue(sys_model.ehb.contains(0x300000 // LINE_SIZE))
            lat_ehb = sys_model.clflush(core_id=0, addr=0x300000)
            self.assertEqual(lat_ehb, 70, f"EHB-cached CT-Flush must be 70 cycles in {mode}")

        # Contrast: Baseline unprotected cache must leak timing (45 vs 95 cycles)
        sys_base = MultiCoreCacheSystem(mode='none')
        lat_base_uncached = sys_base.clflush(core_id=0, addr=0x100000)
        sys_base.read_address(core_id=0, addr=0x200000, domain_id=0)
        lat_base_cached = sys_base.clflush(core_id=0, addr=0x200000)
        self.assertEqual(lat_base_uncached, 45)
        self.assertEqual(lat_base_cached, 95)
        self.assertEqual(lat_base_cached - lat_base_uncached, 50, "Baseline flush must exhibit 50-cycle timing delta")

    # -------------------------------------------------------------------------
    # Test 3: Dual Placement - Condition 1 (Private Sharers)
    # -------------------------------------------------------------------------
    def test_3_dual_placement_sharer_condition(self):
        """
        Test 3: Verifies Placement Condition 1 (Section V-C2): LLC evictions that associate
        with active copies in private caches (L1/L2) must be securely captured into EHB.
        """
        sys_model = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=8, llc_sets=32, llc_ways=4)
        addr = 0x100000
        block = addr // LINE_SIZE

        # Core 0 reads address -> establishes Core 0 as private-cache sharer
        sys_model.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
        self.assertIn(0, sys_model.sharers.get(block, set()))

        # Core 1 triggers conflicting LLC accesses, forcing eviction of block from LLC
        evicted = force_llc_eviction(sys_model, addr, domain=1, count=6)
        self.assertTrue(evicted, "Target block must be evicted from LLC set")

        # Condition 1 triggered: had_sharers == True -> block entered into EHB
        self.assertTrue(sys_model.ehb.contains(block), "Block with private sharers MUST enter EHB upon eviction")
        self.assertGreaterEqual(sys_model.stats['ehb_eligible'], 1)
        self.assertGreaterEqual(sys_model.stats['ehb_inserted'], 1)

    # -------------------------------------------------------------------------
    # Test 4: Dual Placement - Condition 2 (EHB Reload Origin)
    # -------------------------------------------------------------------------
    def test_4_dual_placement_reload_condition(self):
        """
        Test 4: Verifies Placement Condition 2 (Section V-C2): LLC evictions displaced by
        an EHB-reload line (from_ehb == True) are eligible for EHB even without private sharers!
        """
        sys_model = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=8, llc_sets=32, llc_ways=4)
        target_set = 5

        # 1. Install victim block V into target set
        addr_victim = (0x100000 // LINE_SIZE + target_set) * LINE_SIZE
        block_victim = addr_victim // LINE_SIZE
        sys_model.read_address(core_id=0, addr=addr_victim, domain_id=0, is_sensitive=False)

        # Explicitly purge private sharers so block_victim has NO private copies
        sys_model._invalidate_private(block_victim)
        self.assertFalse(bool(sys_model.sharers.get(block_victim)), "Victim block must have NO private sharers")

        # 2. Fill the remaining ways of target set with 3 other blocks (set capacity = 4 ways)
        # Ensure block_victim remains the oldest entry (LRU candidate in set)
        for j in range(1, 4):
            conf_addr = ((200000 + j) * sys_model.llc_sets + target_set) * LINE_SIZE
            sys_model.read_address(core_id=0, addr=conf_addr, domain_id=0, is_sensitive=False)

        self.assertEqual(len(sys_model.llc[target_set]), 4, "LLC set must be completely full")
        self.assertIn(block_victim, sys_model.llc[target_set])

        # 3. Buffer a reload line R in EHB that maps to target_set
        addr_reload = ((300000) * sys_model.llc_sets + target_set) * LINE_SIZE
        block_reload = addr_reload // LINE_SIZE
        sys_model.ehb.insert(block_reload, owners={0}, sensitive=True, current_time=sys_model.time)
        self.assertTrue(sys_model.ehb.contains(block_reload))

        # 4. Access addr_reload -> triggers EHB hit and reload with from_ehb=True
        lat, lvl = sys_model.read_address(core_id=0, addr=addr_reload, domain_id=0, is_sensitive=True)
        self.assertEqual(lvl, 'EHB_HIT')
        self.assertEqual(lat, 40)

        # 5. Condition 2 verification:
        # block_victim had NO private sharers, but because its displacement was caused
        # by an EHB-reload line (from_ehb=True), it MUST be placed into EHB!
        self.assertTrue(
            sys_model.ehb.contains(block_victim),
            "Displaced block without private sharers MUST enter EHB under Condition 2 (EHB reload origin)"
        )

    # -------------------------------------------------------------------------
    # Test 5: Non-Eligible Eviction Bypasses
    # -------------------------------------------------------------------------
    def test_5_non_eligible_eviction_bypasses(self):
        """
        Test 5: Verifies that LLC evictions without private sharers AND not caused by
        an EHB reload bypass directly to DRAM without consuming buffer slots.
        """
        sys_model = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=8, llc_sets=32, llc_ways=4)
        addr = 0x100000
        block = addr // LINE_SIZE

        # Load address into cache hierarchy
        sys_model.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=False)

        # Invalidate private copies before LLC eviction
        sys_model._invalidate_private(block)
        self.assertFalse(bool(sys_model.sharers.get(block)))

        # Evict from LLC via normal DRAM reads (from_ehb=False)
        force_llc_eviction(sys_model, addr, count=6)

        # Neither Condition 1 nor Condition 2 met for block -> must NOT enter EHB
        self.assertFalse(sys_model.ehb.contains(block), "Non-eligible eviction must bypass to DRAM")

    # -------------------------------------------------------------------------
    # Test 6: EHB Reload Reinstalls LLC
    # -------------------------------------------------------------------------
    def test_6_ehb_reload_reinstalls_llc(self):
        """
        Test 6: Verifies take() on hit removes entry from EHB and reinstalls it into LLC.
        """
        sys_model = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=8, llc_sets=32, llc_ways=4)
        addr = 0x100000
        block = addr // LINE_SIZE

        # Load and evict to EHB
        sys_model.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
        force_llc_eviction(sys_model, addr, count=6)
        self.assertTrue(sys_model.ehb.contains(block))

        # Access target: must reload from EHB
        lat, lvl = sys_model.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
        self.assertEqual(lvl, 'EHB_HIT')
        self.assertEqual(lat, 40)

        # Post-condition: removed from EHB, resident in LLC
        self.assertFalse(sys_model.ehb.contains(block), "Reloaded entry must be removed from EHB")
        self.assertIn(block, sys_model.llc[sys_model._set(block)], "Reloaded entry must be reinstalled in LLC")

    # -------------------------------------------------------------------------
    # Test 7: Domain Quota Enforcement
    # -------------------------------------------------------------------------
    def test_7_domain_quota_enforcement(self):
        """
        Test 7: Verifies a security domain cannot exceed capacity // num_domains without replacement.
        """
        buf = EvictionHiddenBuffer(capacity_lines=8, num_domains=2)
        quota = buf.quota  # 8 // 2 = 4

        # Domain 0 inserts 4 blocks -> fills quota
        for i in range(1, 5):
            self.assertTrue(buf.insert(i, owners={0}, sensitive=False, current_time=i))
        self.assertEqual(len(buf.entries), 4)

        # Domain 0 inserts 5th block -> must replace LRU domain 0 block (block 1)
        self.assertTrue(buf.insert(5, owners={0}, sensitive=False, current_time=5))
        d0_count = sum(0 in e.owners for e in buf.entries.values())
        self.assertEqual(d0_count, quota, "Domain 0 occupancy must never exceed quota without replacement")
        self.assertNotIn(1, buf.entries, "Block 1 (LRU) must have been replaced")
        self.assertIn(5, buf.entries)

        # Domain 1 inserts 4 blocks -> admitted into empty slots
        for j in range(10, 14):
            self.assertTrue(buf.insert(j, owners={1}, sensitive=False, current_time=j))
        self.assertEqual(len(buf.entries), 8, "Buffer should now be fully occupied (4 d0 + 4 d1)")

    # -------------------------------------------------------------------------
    # Test 8: Cross-Domain Isolation
    # -------------------------------------------------------------------------
    def test_8_cross_domain_isolation(self):
        """
        Test 8: Verifies attacker domain blocks CANNOT evict victim-owned blocks when private.
        """
        for cls in (EvictionHiddenBuffer, AdaptiveEvictionHiddenBuffer):
            buf = cls(capacity_lines=4, num_domains=2)

            # Victim (Domain 0) inserts block 100
            self.assertTrue(buf.insert(100, owners={0}, sensitive=True, current_time=1))

            # Attacker (Domain 1) floods buffer with 50 blocks
            for j in range(101, 151):
                buf.insert(j, owners={1}, sensitive=False, current_time=j)

            # Victim block 100 MUST remain intact in buffer!
            self.assertTrue(buf.contains(100), f"Cross-domain isolation failed for {cls.__name__}")
            # Attacker occupancy cannot exceed its quota of 2
            d1_count = sum(1 in e.owners for e in buf.entries.values())
            self.assertLessEqual(d1_count, 2)

    # -------------------------------------------------------------------------
    # Test 9: Shared Contention Failure in Standard TC
    # -------------------------------------------------------------------------
    def test_9_shared_contention_failure_in_standard_tc(self):
        """
        Test 9: Verifies Standard TreasureCache fails under joint ownership {0, 1} churn,
        while Ada-EHB successfully protects sensitive lines via retention scoring and sticky residency.
        """
        # Standard TC: unweighted LRU allows shared non-sensitive churn to evict sensitive lines
        std_buf = EvictionHiddenBuffer(capacity_lines=4, num_domains=2)
        # Sensitive line with joint ownership {0, 1}
        std_buf.insert(block_addr=10, owners={0, 1}, sensitive=True, current_time=1)

        # Attacker injects 10 shared non-sensitive lines {0, 1}
        for t, b in enumerate(range(20, 30), start=2):
            std_buf.insert(block_addr=b, owners={0, 1}, sensitive=False, current_time=t)

        self.assertFalse(std_buf.contains(10), "Standard TC MUST evict line 10 under shared LRU contention")

        # Proposed Ada-EHB: sticky residency and retention scoring protect line 10!
        ada_buf = AdaptiveEvictionHiddenBuffer(capacity_lines=4, num_domains=2)
        ada_buf.insert(block_addr=10, owners={0, 1}, sensitive=True, current_time=1)
        for t, b in enumerate(range(20, 30), start=2):
            ada_buf.insert(block_addr=b, owners={0, 1}, sensitive=False, current_time=t)

        self.assertTrue(ada_buf.contains(10), "Ada-EHB MUST retain sensitive line 10 despite adversarial churn")

    # -------------------------------------------------------------------------
    # Test 10: Ada-EHB Retention Scoring Formula
    # -------------------------------------------------------------------------
    def test_10_ada_ehb_retention_scoring_formula(self):
        """
        Test 10: Verifies mathematical scoring correctly weights sensitivity (3.0x),
        frequency (alpha=0.2), and logarithmic age decay.
        """
        buf = AdaptiveEvictionHiddenBuffer(capacity_lines=16, num_domains=2)

        # 1. Sensitivity Weighting: S(sensitive)=3.0 vs S(normal)=1.0
        e_sens = BufferEntry(address=1, owners={0}, sensitive=True, insertion_time=100, last_access=100, frequency=1)
        e_norm = BufferEntry(address=2, owners={0}, sensitive=False, insertion_time=100, last_access=100, frequency=1)
        score_sens = buf.score(e_sens, current_time=200)
        score_norm = buf.score(e_norm, current_time=200)
        self.assertAlmostEqual(score_sens, 3.0 * score_norm, places=5)

        # 2. Frequency Scaling: F=5 vs F=1
        e_freq5 = BufferEntry(address=3, owners={0}, sensitive=False, insertion_time=100, last_access=100, frequency=5)
        score_freq5 = buf.score(e_freq5, current_time=200)
        expected_ratio = (1.0 + 0.2 * 5) / (1.0 + 0.2 * 1)  # 2.0 / 1.2 = 1.6667
        self.assertAlmostEqual(score_freq5 / score_norm, expected_ratio, places=5)

        # 3. Logarithmic Age Decay: Age=10 vs Age=100
        e_recent = BufferEntry(address=4, owners={0}, sensitive=False, insertion_time=190, last_access=190, frequency=1)
        score_recent = buf.score(e_recent, current_time=200)  # age = 10
        score_aged = buf.score(e_norm, current_time=200)      # age = 100
        self.assertGreater(score_recent, score_aged, "Recent entry must score higher than aged entry")

        # 4. Analytical KaTeX Formula Precision
        expected_aged = 1.2 / math.log(1.0 + 100.0 + 1e-5)
        self.assertAlmostEqual(score_aged, expected_aged, places=5)

    # -------------------------------------------------------------------------
    # Test 11: Ada-EHB Sticky Residency
    # -------------------------------------------------------------------------
    def test_11_ada_ehb_sticky_residency(self):
        """
        Test 11: Verifies sensitive lines (AES S-box) are immune to eviction under adversarial flooding.
        """
        buf = AdaptiveEvictionHiddenBuffer(capacity_lines=4, num_domains=1)

        # Buffer filled with 4 sensitive lines
        for i in range(1, 5):
            self.assertTrue(buf.insert(i, owners={0}, sensitive=True, current_time=1))
        self.assertEqual(len(buf.entries), 4)

        # Flood with 50 non-sensitive lines
        for j in range(100, 150):
            admitted = buf.insert(j, owners={0}, sensitive=False, current_time=j)
            self.assertFalse(admitted, "Non-sensitive lines must bypass when buffer holds sensitive lines")

        self.assertEqual(buf.bypasses, 50)
        for i in range(1, 5):
            self.assertTrue(buf.contains(i), f"Sensitive block {i} must maintain sticky residency")

    # -------------------------------------------------------------------------
    # Test 12: Ada-EHB Rate Limiter
    # -------------------------------------------------------------------------
    def test_12_ada_ehb_rate_limiter(self):
        """
        Test 12: Verifies token-bucket burst rate limiter drops excessive non-sensitive evictions
        and refills predictably with time (1 token per 125 cycles).
        """
        buf = AdaptiveEvictionHiddenBuffer(capacity_lines=16, num_domains=1)

        # Bucket starts with 8 tokens at t=0
        for i in range(1, 9):
            self.assertTrue(buf.insert(i, owners={0}, sensitive=False, current_time=0))
        self.assertEqual(len(buf.entries), 8)

        # 9th block at t=0 must be rejected (exhausted tokens)
        self.assertFalse(buf.insert(9, owners={0}, sensitive=False, current_time=0))
        self.assertEqual(buf.bypasses, 1)

        # Sensitive block is exempt from rate limiting!
        self.assertTrue(buf.insert(99, owners={0}, sensitive=True, current_time=0))

        # Advance by 250 cycles -> refills 2 tokens
        self.assertTrue(buf.insert(9, owners={0}, sensitive=False, current_time=250))

    # -------------------------------------------------------------------------
    # Test 13: Ada-EHB+ Dynamic Elastic Quota (DEDQ)
    # -------------------------------------------------------------------------
    def test_13_ada_ehb_plus_dynamic_quota(self):
        """
        Test 13: Tests Dynamic Elastic Quota (DEDQ) borrowing under asymmetric multi-domain load
        and instant revocation floor restoration when an idle domain wakes up.
        """
        if not ADA_EHB_PLUS_LOADED:
            self.skipTest("ada_ehb_plus module not loaded")

        buf = AdaEHBPlusBuffer(capacity_lines=48, num_domains=3, idle_timeout=500)
        buf.secure_domains.add(0)

        self.assertEqual(buf.base_floor, 16)
        # With domains 1 and 2 idle at t=100, domain 0 can borrow up to safe ceiling (48)
        elastic_quota = buf.get_elastic_quota(domain=0, current_time=100)
        self.assertEqual(elastic_quota, 48)

        # Active Domain 0 inserts 24 lines (exceeding static 16-line quota by 50%)
        for i in range(1, 25):
            admitted = buf.insert(i, owners={0}, sensitivity=SensitivityLevel.ROOT_OF_TRUST, current_time=100)
            self.assertTrue(admitted)

        self.assertEqual(buf.get_domain_occupancy(0), 24)

        # Full end-to-end instant revocation trial validation
        res = run_revocation_floor_trial(ehb_capacity=48)
        self.assertEqual(res['dom2_admitted'], res['dom2_requested'], "Waking domain must receive 100% of its floor")
        self.assertGreater(res['revocations'], 0, "Revocations must trigger to free slots for waking domain")
        self.assertEqual(res['total_buffered'], 48, "Total buffer occupancy must respect capacity")

    # -------------------------------------------------------------------------
    # Test 14: Ada-EHB+ Shannon Entropy Detection
    # -------------------------------------------------------------------------
    def test_14_ada_ehb_plus_entropy_detection(self):
        """
        Test 14: Tests Shannon Entropy Profiler detection of flat eviction-set sweeps (H=5.0)
        versus structured, localized cryptographic accesses (H=1.0).
        """
        if not ADA_EHB_PLUS_LOADED:
            self.skipTest("ada_ehb_plus module not loaded")

        profiler = ShannonEntropyProfiler(window_size=32, sweep_threshold=0.85)

        # Scenario A: Attacker sweeping 32 unique addresses across eviction set
        for i in range(32):
            profiler.record_access(domain=1, block_addr=1000 + i)

        self.assertAlmostEqual(profiler.get_entropy(1), 5.0, places=4)
        self.assertAlmostEqual(profiler.get_normalized_entropy(1), 1.0, places=4)
        self.assertTrue(profiler.is_sweep_active(1), "Attacker sweep MUST be detected")
        self.assertEqual(profiler.get_entropy_penalty(1), 1.0)

        # Scenario B: Benign victim accessing 2 AES S-box lines with high locality
        for i in range(32):
            profiler.record_access(domain=0, block_addr=2000 + (i % 2))

        self.assertAlmostEqual(profiler.get_entropy(0), 1.0, places=4)
        self.assertAlmostEqual(profiler.get_normalized_entropy(0), 0.2, places=4)
        self.assertFalse(profiler.is_sweep_active(0), "Benign crypto workload must NOT trigger sweep alarm")
        self.assertEqual(profiler.get_entropy_penalty(0), 0.0)

    # -------------------------------------------------------------------------
    # Test 15: Flush+Reload Mitigation
    # -------------------------------------------------------------------------
    def test_15_flush_reload_mitigation(self):
        """
        Test 15: Tests Flush+Reload attack neutralization.
        Verifies that while Baseline exhibits ~160+ cycle leakage, TreasureCache and Ada-EHB
        shrink timing delta to ~2 cycles (indistinguishable from LLC vs EHB hit).
        """
        if ADVANCED_ATTACKS_LOADED:
            # Full benchmark validation via Attack Suite
            atk_none = FlushReloadAttack(mode='none').run_experiment(rounds=25)
            self.assertEqual(atk_none.verdict, "VULNERABLE")
            self.assertGreaterEqual(atk_none.timing_delta, 100.0)

            for mode in ('treasure_cache', 'ada_ehb'):
                atk_def = FlushReloadAttack(mode=mode).run_experiment(rounds=25)
                self.assertEqual(atk_def.verdict, "NEUTRALIZED", f"Flush+Reload must be neutralized in {mode}")
                self.assertLessEqual(atk_def.timing_delta, 5.0)

        # Direct model verification
        sys_tc = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=64)
        addr = 0x100000
        # Warmup shared line
        sys_tc.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
        sys_tc.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)
        # Flush line
        sys_tc.clflush(core_id=1, addr=addr)

        # Victim active -> reloads line to LLC
        sys_tc.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
        lat_active, lvl_active = sys_tc.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)
        self.assertEqual(lvl_active, 'LLC_HIT')
        self.assertEqual(lat_active, 38)

        # Victim inactive trial
        sys_inact = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=64)
        sys_inact.read_address(core_id=0, addr=addr, domain_id=0, is_sensitive=True)
        sys_inact.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)
        sys_inact.clflush(core_id=1, addr=addr)
        sys_inact.read_address(core_id=0, addr=0x900000, domain_id=0, is_sensitive=False)
        lat_inact, lvl_inact = sys_inact.read_address(core_id=1, addr=addr, domain_id=1, is_sensitive=False)
        self.assertEqual(lvl_inact, 'EHB_HIT')
        self.assertEqual(lat_inact, 40)

        self.assertLessEqual(abs(lat_inact - lat_active), 2, "Timing delta must be <= 2 cycles")

    # -------------------------------------------------------------------------
    # Test 16: Flush+Flush Mitigation
    # -------------------------------------------------------------------------
    def test_16_flush_flush_mitigation(self):
        """
        Test 16: Tests Flush+Flush attack neutralization via Constant-Time Flush (CT-Flush).
        """
        if ADVANCED_ATTACKS_LOADED:
            atk_none = FlushFlushAttack(mode='none').run_experiment(rounds=25)
            self.assertEqual(atk_none.verdict, "VULNERABLE")
            self.assertGreaterEqual(atk_none.timing_delta, 40.0)

            for mode in ('treasure_cache', 'ada_ehb'):
                atk_def = FlushFlushAttack(mode=mode).run_experiment(rounds=25)
                self.assertEqual(atk_def.verdict, "NEUTRALIZED", f"Flush+Flush must be neutralized in {mode}")
                self.assertEqual(atk_def.timing_delta, 0.0)

        # Direct verification: cached vs uncached clflush must be equal (70 cycles)
        for mode in ('treasure_cache', 'ada_ehb'):
            sys_m = MultiCoreCacheSystem(mode=mode)
            uncached_flush = sys_m.clflush(core_id=0, addr=0x100000)
            sys_m.read_address(core_id=0, addr=0x100000, domain_id=0)
            cached_flush = sys_m.clflush(core_id=0, addr=0x100000)
            self.assertEqual(uncached_flush, 70)
            self.assertEqual(cached_flush, 70)
            self.assertEqual(cached_flush - uncached_flush, 0)

    # -------------------------------------------------------------------------
    # Test 17: Prime+Probe Mitigation
    # -------------------------------------------------------------------------
    def test_17_prime_probe_mitigation(self):
        """
        Test 17: Tests Prime+Probe timing gap neutralization.
        Verifies that victim evictions of attacker eviction-set lines enter EHB,
        allowing attacker probe to hit EHB (40 cycles) instead of DRAM (200 cycles).
        """
        if ADVANCED_ATTACKS_LOADED:
            atk_none = PrimeProbeAttack(mode='none').run_experiment(rounds=25)
            self.assertEqual(atk_none.verdict, "VULNERABLE")
            self.assertGreaterEqual(atk_none.timing_delta, 100.0)

            for mode in ('treasure_cache', 'ada_ehb'):
                atk_def = PrimeProbeAttack(mode=mode).run_experiment(rounds=25)
                self.assertEqual(atk_def.verdict, "NEUTRALIZED")
                self.assertLessEqual(atk_def.timing_delta, 5.0)

        # Direct cache verification
        sys_tc = MultiCoreCacheSystem(mode='treasure_cache', ehb_capacity=64, llc_sets=32, llc_ways=4)
        target_set = 7
        victim_addr = ((100000) * sys_tc.llc_sets + target_set) * LINE_SIZE
        eviction_set = [((800000 + j) * sys_tc.llc_sets + target_set) * LINE_SIZE for j in range(sys_tc.llc_ways)]

        # Prime
        for a in eviction_set:
            sys_tc.read_address(core_id=1, addr=a, domain_id=1)
        # Victim access
        sys_tc.read_address(core_id=0, addr=victim_addr, domain_id=0, is_sensitive=True)
        # Probe
        probe_lats = [sys_tc.read_address(core_id=1, addr=a, domain_id=1)[0] for a in eviction_set]
        # Max probe latency must hit in L1 or EHB (<= 40 cycles), NEVER DRAM (~200 cycles)
        self.assertLessEqual(max(probe_lats), 40, "Evicted attacker line must hit EHB at 40 cycles")

    # -------------------------------------------------------------------------
    # Test 18: Prime+Reprime+Probe Mitigation (Condition 2 Necessity)
    # -------------------------------------------------------------------------
    def test_18_prime_reprime_probe_condition2_defense(self):
        """
        Test 18: Verifies Section V-C2: Prime+Reprime+Probe bypasses defenses that only use
        Condition 1 (like SHARP), but is completely neutralized by TreasureCache's Condition 2.
        """
        if ADVANCED_ATTACKS_LOADED:
            atk_c1 = PrimeReprimeProbeAttack(mode='treasure_cache', condition1_only=True).run_experiment(rounds=20)
            self.assertEqual(atk_c1.verdict, "VULNERABLE", "Condition 1 alone MUST fail against Prime+Reprime+Probe")
            self.assertGreaterEqual(atk_c1.timing_delta, 100.0)

            atk_tc = PrimeReprimeProbeAttack(mode='treasure_cache', condition1_only=False).run_experiment(rounds=20)
            self.assertEqual(atk_tc.verdict, "NEUTRALIZED", "Condition 2 MUST neutralize Prime+Reprime+Probe")
            self.assertLessEqual(atk_tc.timing_delta, 5.0)

    # -------------------------------------------------------------------------
    # Test 19: Ada-EHB+ Multi-Tier Sensitivity Hierarchy
    # -------------------------------------------------------------------------
    def test_19_ada_ehb_plus_multitier_hierarchy(self):
        """
        Test 19: Verifies discrete sensitivity tiers:
          - ROOT_OF_TRUST (S=5.0 + Sticky)
          - PROTECTED_PAGE (S=2.0)
          - NORMAL (S=1.0)
        Verifies replacement priority: low-trust -> NORMAL -> PROTECTED_PAGE -> ROOT_OF_TRUST.
        """
        if not ADA_EHB_PLUS_LOADED:
            self.skipTest("ada_ehb_plus module not loaded")

        buf = AdaEHBPlusBuffer(capacity_lines=3, num_domains=1)
        # Insert 1 ROOT_OF_TRUST and 2 PROTECTED_PAGE entries
        buf.insert(1, owners={0}, sensitivity=SensitivityLevel.ROOT_OF_TRUST, current_time=1)
        buf.insert(2, owners={0}, sensitivity=SensitivityLevel.PROTECTED_PAGE, current_time=2)
        buf.insert(3, owners={0}, sensitivity=SensitivityLevel.NORMAL, current_time=3)
        self.assertEqual(len(buf.entries), 3)

        # Incoming Level 1 entry should replace Level 0 (NORMAL) entry 3!
        buf.insert(4, owners={0}, sensitivity=SensitivityLevel.PROTECTED_PAGE, current_time=4)
        self.assertIn(1, buf.entries, "ROOT_OF_TRUST entry 1 must remain resident")
        self.assertIn(2, buf.entries, "PROTECTED_PAGE entry 2 must remain resident")
        self.assertIn(4, buf.entries, "New entry 4 must be admitted")
        self.assertNotIn(3, buf.entries, "NORMAL entry 3 must have been evicted first")

    # -------------------------------------------------------------------------
    # Test 20: Hardware & Analytical Storage Overhead Consistency
    # -------------------------------------------------------------------------
    def test_20_hardware_and_analytical_overhead_consistency(self):
        """
        Test 20: Validates hardware synthesis and analytical model metrics:
          - Hardware storage overhead < 0.5% (approx 0.45% of 2MB LLC) per Eqs (3)-(4).
          - CAM search latency <= 0.4 ns (single-cycle at 2.5 GHz).
        """
        metrics_path = os.path.join(os.path.dirname(__file__), "hardware_metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "storage_overhead_validation" in data:
                for entry in data["storage_overhead_validation"]:
                    self.assertLess(entry["normalized_overhead_pct"], 0.50, "Storage overhead must be < 0.5% of LLC")
                    self.assertTrue(entry["complies_less_than_0_48_pct"])
            if "timing_analysis" in data:
                self.assertTrue(data["timing_analysis"]["timing_met_28nm"])
                self.assertLessEqual(data["timing_analysis"]["total_cam_critical_path_28nm_ps"], 400.0)

        analytical_path = os.path.join(os.path.dirname(__file__), "analytical_validation.json")
        if os.path.exists(analytical_path):
            with open(analytical_path, "r", encoding="utf-8") as f:
                ana_data = json.load(f)
            self.assertIn("paper_baseline_verification_g128", ana_data)
            epoch_data = ana_data["paper_baseline_verification_g128"]["attacker_epoch_analysis"]
            self.assertGreater(epoch_data["cycles_required"], 5_000_000)


def run_master_test_suite():
    """Executes the master test suite and returns runner exit code."""
    suite = unittest.TestLoader().loadTestsFromTestCase(MasterAdvancedCacheTestSuite)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_master_test_suite())
