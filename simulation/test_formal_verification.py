"""
test_formal_verification.py - Unit Test Suite for Mathematical & Paper Fidelity Audit
======================================================================================
Validates all analytical equations, threshold computations, hardware storage models,
and artifact generation against IEEE TDSC 2024 specifications.
"""

import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formal_verification import (
    eq1_pmf_deown,
    eq2_cdf_attacker_tpr,
    calculate_min_k_for_tpr,
    calculate_attacker_epoch,
    eq3_storage_breakdown,
    eq4_llc_normalized_overhead,
    compute_parameter_grid,
    run_monte_carlo_invalidation_experiment,
    generate_analytical_validation,
)


class TestFormalVerification(unittest.TestCase):

    def test_eq1_pmf_properties(self):
        """Validates that Eq. (1) forms a valid geometric probability distribution."""
        g = 128
        # Non-negativity and k=1 base case
        self.assertEqual(eq1_pmf_deown(0, g), 0.0)
        self.assertAlmostEqual(eq1_pmf_deown(1, g), 1.0 / 128.0)
        
        # Sum over first 2000 terms should approach 1.0
        prob_sum = sum(eq1_pmf_deown(k, g) for k in range(1, 2000))
        self.assertAlmostEqual(prob_sum, 1.0, places=5)

    def test_eq2_cdf_and_k89_threshold(self):
        """
        Validates Eq. (2) and strictly verifies paper Section VII-C proof:
        k >= 89 is required for attacker TPR > 0.5 when g = 128.
        """
        g = 128
        tpr_88 = eq2_cdf_attacker_tpr(88, g)
        tpr_89 = eq2_cdf_attacker_tpr(89, g)

        # F_N(88) MUST be strictly below 0.50
        self.assertLess(tpr_88, 0.50, f"F_N(88)={tpr_88} must be < 0.50")
        self.assertAlmostEqual(tpr_88, 0.498524, places=5)

        # F_N(89) MUST be strictly above 0.50
        self.assertGreater(tpr_89, 0.50, f"F_N(89)={tpr_89} must be > 0.50")
        self.assertAlmostEqual(tpr_89, 0.502442, places=5)

        # Automated solver returns exact (89, >0.5)
        k_min, exact_tpr = calculate_min_k_for_tpr(0.5, g)
        self.assertEqual(k_min, 89)
        self.assertGreater(exact_tpr, 0.5)

    def test_attacker_epoch_calculation(self):
        """
        Validates the attacker epoch derivation:
        k=89, rate=0.09 blocks/10,000 cycles => Epoch ~= 9.89 * 10^6 cycles (~1000x baseline).
        """
        epoch = calculate_attacker_epoch(g=128, target_tpr=0.5, ownership_rate_per_10k=0.09)
        self.assertEqual(epoch["k_min_integer"], 89)
        self.assertTrue(epoch["tpr_exceeds_threshold"])
        
        # Cycles = (89 / 0.09) * 10000 = 9888888.89 cycles
        self.assertAlmostEqual(epoch["cycles_required"], 89.0 / 0.09 * 10000.0, places=2)
        self.assertAlmostEqual(epoch["cycles_required"], 9.888889e6, delta=100)

        # Degradation factor vs 10,000 cycles = 988.9x (~1000x)
        self.assertAlmostEqual(epoch["slowdown_factor_vs_10000_cycles"], 988.89, places=1)
        # Degradation factor vs 2,500 cycles = 3955.6x (~4000x)
        self.assertAlmostEqual(epoch["slowdown_factor_vs_2500_cycles"], 3955.56, places=1)

    def test_eq3_hardware_storage_breakdown(self):
        """Validates Eq. (3) storage formula and paper's closed-form approximation."""
        g = 128
        m = 64
        # For c in [1, 2, 4, 8]
        for c in [1, 2, 4, 8]:
            res = eq3_storage_breakdown(c, g, m)
            num_blocks = c * g
            expected_bits = num_blocks * (math.log2(num_blocks) + m + 512) + (c + 1) * math.log2(g)
            self.assertAlmostEqual(res["total_storage_bits"], expected_bits)
            
            # Verify closed-form approximation: c * (9 + log2(c)/64) KB
            paper_kib = res["paper_formula_approx_kib"]
            actual_kib = res["total_storage_kib"]
            self.assertAlmostEqual(actual_kib, paper_kib, delta=0.9)

    def test_eq4_llc_normalized_overhead(self):
        """
        Validates Eq. (4) normalized LLC overhead.
        IEEE TDSC 2024 states overhead is ~0.45% of LLC capacity.
        """
        g = 128
        m = 64
        for c in [1, 2, 4, 8]:
            ovh = eq4_llc_normalized_overhead(c, g, m)
            # Binary LLC overhead should be ~0.445% - 0.447%
            self.assertTrue(ovh["consistent_with_paper_claim"])
            self.assertAlmostEqual(ovh["exact_binary_llc_overhead_pct"], 0.45, delta=0.01)

    def test_parameter_grid_coverage(self):
        """Validates complete evaluation across g in [32..512] and c in [1..8]."""
        grid = compute_parameter_grid(g_values=[32, 64, 128, 256, 512], c_values=[1, 2, 4, 8])
        self.assertEqual(len(grid["grid_entries"]), 20)  # 5 * 4
        self.assertIn("128", grid["by_threshold"])
        self.assertEqual(grid["by_threshold"]["128"]["min_k_tpr_0.5"], 89)

    def test_monte_carlo_goodness_of_fit(self):
        """Validates empirical random invalidation simulation against analytical model."""
        mc = run_monte_carlo_invalidation_experiment(g=128, num_trials=20000, seed=42)
        self.assertAlmostEqual(mc["moments"]["empirical_mean"], 128.0, delta=3.0)
        self.assertLess(mc["goodness_of_fit"]["cdf_mean_absolute_error"], 0.01)
        self.assertAlmostEqual(mc["critical_k_evaluation"]["k_89"]["empirical_cdf"], 0.5024, delta=0.015)

    def test_analytical_validation_json_generation(self):
        """Validates that generate_analytical_validation writes a complete, valid JSON artifact."""
        test_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_analytical_validation.json")
        try:
            report = generate_analytical_validation(output_path=test_json)
            self.assertTrue(os.path.exists(test_json))
            with open(test_json, "r") as f:
                data = json.load(f)
            self.assertIn("paper_baseline_verification_g128", data)
            self.assertEqual(data["audit_summary"]["overall_audit_verdict"], "CONGRUENT_WITH_IEEE_TDSC_2024")
        finally:
            if os.path.exists(test_json):
                os.remove(test_json)


if __name__ == "__main__":
    unittest.main()
