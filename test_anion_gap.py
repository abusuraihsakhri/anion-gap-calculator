#!/usr/bin/env python3
"""
Tests for the Anion Gap Calculator.

Covers:
  - Normal anion gap
  - Elevated anion gap (DKA, lactic acidosis, uremia)
  - Albumin-corrected AG
  - Potassium-adjusted AG
  - Delta gap and delta ratio interpretation
  - Osmolal gap calculation
  - Edge cases (missing values, extreme values, zero denominator)
  - Full interpret() and calculate() integration
  - CLI argument parsing

Run: python -m pytest test_anion_gap.py -v
  or: python -m unittest test_anion_gap -v
"""

import unittest
import json
import csv
import os
import tempfile

import anion_gap
from cli import build_parser


class TestAnionGapBasic(unittest.TestCase):
    """Test the core anion_gap() function."""

    def test_normal_ag(self):
        """Na=140, Cl=100, HCO3=24 -> AG=16 (within normal-ish range)."""
        result = anion_gap.anion_gap(140, 100, 24)
        self.assertEqual(result, 16.0)

    def test_textbook_normal(self):
        """Na=140, Cl=105, HCO3=24 -> AG=11 (textbook normal)."""
        result = anion_gap.anion_gap(140, 105, 24)
        self.assertEqual(result, 11.0)

    def test_low_normal_boundary(self):
        """AG at lower boundary: Na=140, Cl=108, HCO3=24 -> AG=8."""
        result = anion_gap.anion_gap(140, 108, 24)
        self.assertEqual(result, 8.0)

    def test_high_normal_boundary(self):
        """AG at upper boundary: Na=140, Cl=104, HCO3=24 -> AG=12."""
        result = anion_gap.anion_gap(140, 104, 24)
        self.assertEqual(result, 12.0)

    def test_rounding(self):
        """Verify rounding to 2 decimals."""
        result = anion_gap.anion_gap(140.5, 100.3, 23.7)
        self.assertEqual(result, 16.5)


class TestAnionGapElevated(unittest.TestCase):
    """Test elevated AG scenarios (DKA, lactic acidosis, uremia)."""

    def test_dka(self):
        """DKA: Na=140, Cl=95, HCO3=10 -> AG=35."""
        result = anion_gap.anion_gap(140, 95, 10)
        self.assertEqual(result, 35.0)
        self.assertGreater(result, anion_gap.AG_NORMAL_HIGH)

    def test_lactic_acidosis(self):
        """Lactic acidosis: Na=145, Cl=100, HCO3=12 -> AG=33."""
        result = anion_gap.anion_gap(145, 100, 12)
        self.assertEqual(result, 33.0)
        self.assertGreater(result, anion_gap.AG_NORMAL_HIGH)

    def test_uremia(self):
        """Uremia: Na=138, Cl=98, HCO3=14 -> AG=26."""
        result = anion_gap.anion_gap(138, 98, 14)
        self.assertEqual(result, 26.0)
        self.assertGreater(result, anion_gap.AG_NORMAL_HIGH)

    def test_salicylate_poisoning(self):
        """Salicylate: Na=142, Cl=102, HCO3=15 -> AG=25."""
        result = anion_gap.anion_gap(142, 102, 15)
        self.assertEqual(result, 25.0)

    def test_ethylene_glycol(self):
        """Ethylene glycol: Na=144, Cl=100, HCO3=8 -> AG=36."""
        result = anion_gap.anion_gap(144, 100, 8)
        self.assertEqual(result, 36.0)


class TestAnionGapLow(unittest.TestCase):
    """Test low anion gap scenarios."""

    def test_hypoalbuminemia(self):
        """Hypoalbuminemia can lower AG: Na=140, Cl=110, HCO3=26 -> AG=4."""
        result = anion_gap.anion_gap(140, 110, 26)
        self.assertEqual(result, 4.0)
        self.assertLess(result, anion_gap.AG_NORMAL_LOW)

    def test_multiple_myeloma(self):
        """Multiple myeloma: Na=135, Cl=108, HCO3=25 -> AG=2."""
        result = anion_gap.anion_gap(135, 108, 25)
        self.assertEqual(result, 2.0)


class TestAnionGapWithPotassium(unittest.TestCase):
    """Test potassium-adjusted anion gap."""

    def test_normal_with_k(self):
        """AG_k = (140+4) - (100+24) = 20."""
        result = anion_gap.anion_gap_with_potassium(140, 4, 100, 24)
        self.assertEqual(result, 20.0)

    def test_hyperkalemia(self):
        """AG_k with high K: (140+7) - (100+24) = 23."""
        result = anion_gap.anion_gap_with_potassium(140, 7, 100, 24)
        self.assertEqual(result, 23.0)

    def test_hypokalemia(self):
        """AG_k with low K: (140+2.5) - (100+24) = 18.5."""
        result = anion_gap.anion_gap_with_potassium(140, 2.5, 100, 24)
        self.assertEqual(result, 18.5)


class TestCorrectedAnionGap(unittest.TestCase):
    """Test albumin-corrected anion gap."""

    def test_normal_albumin(self):
        """Normal albumin (4.0) -> no correction."""
        result = anion_gap.corrected_anion_gap(12.0, 4.0)
        self.assertEqual(result, 12.0)

    def test_low_albumin(self):
        """Albumin 2.0 -> add 2.5*(4-2) = 5.0."""
        result = anion_gap.corrected_anion_gap(12.0, 2.0)
        self.assertEqual(result, 17.0)

    def test_very_low_albumin(self):
        """Albumin 1.0 -> add 2.5*(4-1) = 7.5."""
        result = anion_gap.corrected_anion_gap(10.0, 1.0)
        self.assertEqual(result, 17.5)

    def test_high_albumin(self):
        """Albumin 5.0 -> subtract 2.5."""
        result = anion_gap.corrected_anion_gap(12.0, 5.0)
        self.assertEqual(result, 9.5)

    def test_masking_hypoalbuminemia(self):
        """
        Clinically important: AG=10 with albumin=2.0 looks normal,
        but corrected AG=15 is actually elevated.
        """
        ag = 10.0
        cag = anion_gap.corrected_anion_gap(ag, 2.0)
        self.assertEqual(cag, 15.0)
        self.assertLess(ag, anion_gap.AG_NORMAL_HIGH)  # appears normal
        self.assertGreater(cag, anion_gap.AG_NORMAL_HIGH)  # actually elevated


class TestDeltaGapAndRatio(unittest.TestCase):
    """Test delta gap and delta ratio interpretation."""

    def test_pure_ag_acidosis(self):
        """Delta ratio 1.0-2.0 -> pure AG metabolic acidosis.
        AG=24, HCO3=12 -> delta_gap=12, denom=12, ratio=1.0"""
        result = anion_gap.delta_ratio(24, 12)
        self.assertEqual(result["delta_gap"], 12.0)
        self.assertEqual(result["delta_ratio"], 1.0)
        self.assertIn("Pure", result["interpretation"])

    def test_pure_ag_ratio_mid(self):
        """AG=20, HCO3=18 -> delta_gap=8, denom=6, ratio=1.333."""
        result = anion_gap.delta_ratio(20, 18)
        self.assertAlmostEqual(result["delta_ratio"], 1.333, places=3)
        self.assertIn("Pure", result["interpretation"])

    def test_mixed_acidosis(self):
        """Delta ratio < 1 -> mixed AG + non-AG acidosis.
        AG=18, HCO3=14 -> delta_gap=6, denom=10, ratio=0.6"""
        result = anion_gap.delta_ratio(18, 14)
        self.assertEqual(result["delta_ratio"], 0.6)
        self.assertIn("Mixed", result["interpretation"])

    def test_concurrent_alkalosis(self):
        """Delta ratio > 2 -> concurrent metabolic alkalosis.
        AG=30, HCO3=20 -> delta_gap=18, denom=4, ratio=4.5"""
        result = anion_gap.delta_ratio(30, 20)
        self.assertEqual(result["delta_ratio"], 4.5)
        self.assertIn("alkalosis", result["interpretation"])

    def test_hco3_at_reference(self):
        """HCO3=24 (reference) -> denominator=0, ratio undefined."""
        result = anion_gap.delta_ratio(15, 24)
        self.assertIsNone(result["delta_ratio"])
        self.assertIn("undefined", result["interpretation"])

    def test_custom_references(self):
        """Custom reference values."""
        result = anion_gap.delta_ratio(20, 18, reference_ag=10, reference_hco3=25)
        # delta_gap = 20-10=10, denom = 25-18=7, ratio = 10/7 = 1.429
        self.assertAlmostEqual(result["delta_ratio"], 1.429, places=3)


class TestOsmolalGap(unittest.TestCase):
    """Test osmolal gap calculation."""

    def test_normal_osmolal_gap(self):
        """Normal: measured=290, Na=140, glucose=100, BUN=15.
        Calc = 2*140 + 100/18 + 15/2.8 = 280 + 5.56 + 5.36 = 290.91
        Gap = 290 - 290.91 = -0.91 (normal)"""
        result = anion_gap.osmolal_gap(290, 140, 100, 15)
        self.assertAlmostEqual(result["calculated_osm"], 290.91, places=1)
        self.assertAlmostEqual(result["osmolal_gap"], -0.91, places=1)
        self.assertIn("Normal", result["interpretation"])

    def test_elevated_osmolal_gap_methanol(self):
        """Methanol ingestion: measured=340, Na=140, glucose=100, BUN=15.
        Calc ~290.91, Gap ~49.09 -> significantly elevated."""
        result = anion_gap.osmolal_gap(340, 140, 100, 15)
        self.assertGreater(result["osmolal_gap"], 10)
        self.assertIn("Significantly", result["interpretation"])

    def test_ethanol_present(self):
        """With ethanol: measured=320, Na=140, glucose=100, BUN=15, EtOH=200.
        Calc = 280 + 5.56 + 5.36 + 200/4.6 = 280 + 5.56 + 5.36 + 43.48 = 334.39
        Gap = 320 - 334.39 = -14.39 (normal when ethanol accounted for)"""
        result = anion_gap.osmolal_gap(320, 140, 100, 15, ethanol=200)
        self.assertAlmostEqual(result["calculated_osm"], 334.39, places=1)
        self.assertIn("Normal", result["interpretation"])

    def test_mildly_elevated(self):
        """Mildly elevated: gap between 10-20.
        Measured=305, Na=140, glucose=100, BUN=15 -> calc~290.91, gap~14.09"""
        result = anion_gap.osmolal_gap(305, 140, 100, 15)
        self.assertGreater(result["osmolal_gap"], 10)
        self.assertLessEqual(result["osmolal_gap"], 20)
        self.assertIn("Mildly", result["interpretation"])


class TestInterpretFunction(unittest.TestCase):
    """Test the full interpret() function."""

    def test_elevated_ag_no_albumin(self):
        """Elevated AG without albumin correction."""
        result = anion_gap.interpret(ag=25, hco3=12)
        self.assertEqual(result["anion_gap"], 25)
        self.assertEqual(result["ag_status"], "elevated")
        self.assertIn("MUDPILES", result["summary"])
        self.assertNotIn("corrected_anion_gap", result)

    def test_normal_ag(self):
        """Normal AG."""
        result = anion_gap.interpret(ag=11, hco3=24)
        self.assertEqual(result["ag_status"], "normal")
        self.assertIn("Normal", result["summary"])

    def test_low_ag(self):
        """Low AG."""
        result = anion_gap.interpret(ag=4, hco3=26)
        self.assertEqual(result["ag_status"], "low")
        self.assertIn("Low", result["summary"])

    def test_with_albumin_correction(self):
        """AG with albumin correction."""
        result = anion_gap.interpret(ag=10, hco3=18, albumin=2.0)
        self.assertEqual(result["corrected_anion_gap"], 15.0)
        self.assertEqual(result["corrected_ag_status"], "elevated")

    def test_with_potassium(self):
        """AG with potassium adjustment."""
        result = anion_gap.interpret(ag=16, hco3=20, na=140, cl=100, k=4.5)
        self.assertEqual(result["anion_gap_k"], 24.5)

    def test_with_osmolal_gap(self):
        """AG with osmolal gap."""
        result = anion_gap.interpret(
            ag=25, hco3=12, na=140, cl=100,
            measured_osm=340, glucose=100, bun=15
        )
        self.assertIn("osmolal_gap", result)
        self.assertGreater(result["osmolal_gap"]["osmolal_gap"], 10)

    def test_full_calculation(self):
        """Full calculation with all parameters."""
        result = anion_gap.calculate(
            na=140, cl=100, hco3=12, albumin=3.0, k=4.5,
            measured_osm=320, glucose=250, bun=30
        )
        self.assertEqual(result["anion_gap"], 28.0)
        self.assertIn("corrected_anion_gap", result)
        self.assertIn("anion_gap_k", result)
        self.assertIn("osmolal_gap", result)
        self.assertIn("summary", result)


class TestCalculateFunction(unittest.TestCase):
    """Test the all-in-one calculate() function."""

    def test_basic(self):
        result = anion_gap.calculate(na=140, cl=105, hco3=24)
        self.assertEqual(result["anion_gap"], 11.0)
        self.assertEqual(result["ag_status"], "normal")

    def test_dka_scenario(self):
        """DKA: high AG, low HCO3."""
        result = anion_gap.calculate(na=135, cl=95, hco3=8)
        self.assertEqual(result["anion_gap"], 32.0)
        self.assertEqual(result["ag_status"], "elevated")
        self.assertIn("MUDPILES", result["summary"])

    def test_with_all_optional(self):
        """All optional parameters provided."""
        result = anion_gap.calculate(
            na=142, cl=102, hco3=15, albumin=2.5, k=5.0,
            measured_osm=350, glucose=180, bun=25, ethanol=100
        )
        self.assertIn("corrected_anion_gap", result)
        self.assertIn("anion_gap_k", result)
        self.assertIn("osmolal_gap", result)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_zero_hco3(self):
        """HCO3=0 -> very high AG."""
        result = anion_gap.anion_gap(140, 100, 0)
        self.assertEqual(result, 40.0)

    def test_zero_sodium(self):
        """Na=0 -> negative AG."""
        result = anion_gap.anion_gap(0, 100, 24)
        self.assertEqual(result, -124.0)

    def test_very_high_values(self):
        """Extreme values."""
        result = anion_gap.anion_gap(180, 80, 5)
        self.assertEqual(result, 95.0)

    def test_negative_gap(self):
        """Negative AG (possible with very high Cl or low Na)."""
        result = anion_gap.anion_gap(130, 115, 25)
        self.assertEqual(result, -10.0)

    def test_albumin_correction_extreme_low(self):
        """Albumin near zero."""
        result = anion_gap.corrected_anion_gap(10.0, 0.5)
        self.assertEqual(result, 18.75)

    def test_delta_ratio_zero_ag(self):
        """AG exactly at reference -> delta_gap=0 -> ratio=0."""
        result = anion_gap.delta_ratio(12, 18)
        self.assertEqual(result["delta_gap"], 0.0)
        self.assertEqual(result["delta_ratio"], 0.0)

    def test_osmolal_gap_zero_ethanol(self):
        """Explicit ethanol=0."""
        result = anion_gap.osmolal_gap(290, 140, 100, 15, ethanol=0)
        self.assertIn("Normal", result["interpretation"])


class TestCLI(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_calculate_args(self):
        parser = build_parser()
        args = parser.parse_args(["calculate", "--na", "140", "--cl", "100", "--hco3", "24"])
        self.assertEqual(args.command, "calculate")
        self.assertEqual(args.na, 140)
        self.assertEqual(args.cl, 100)
        self.assertEqual(args.hco3, 24)
        self.assertIsNone(args.albumin)

    def test_calculate_with_albumin(self):
        parser = build_parser()
        args = parser.parse_args([
            "calculate", "--na", "140", "--cl", "100", "--hco3", "24",
            "--albumin", "3.5"
        ])
        self.assertEqual(args.albumin, 3.5)

    def test_calculate_json_flag(self):
        parser = build_parser()
        args = parser.parse_args([
            "calculate", "--na", "140", "--cl", "100", "--hco3", "24", "--json"
        ])
        self.assertTrue(args.json)

    def test_batch_args(self):
        parser = build_parser()
        args = parser.parse_args(["batch", "--input", "data.csv", "--output", "out.csv"])
        self.assertEqual(args.command, "batch")
        self.assertEqual(args.input, "data.csv")
        self.assertEqual(args.output, "out.csv")


class TestCLIIntegration(unittest.TestCase):
    """Test CLI end-to-end execution."""

    def test_calculate_stdout(self):
        """Run calculate command and verify it produces output."""
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            from cli import main
            ret = main(["calculate", "--na", "140", "--cl", "100", "--hco3", "24"])

        self.assertEqual(ret, 0)
        output = buf.getvalue()
        self.assertIn("Anion Gap", output)
        self.assertIn("16.00", output)

    def test_calculate_json_output(self):
        """Run calculate --json and verify valid JSON."""
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            from cli import main
            ret = main(["calculate", "--na", "140", "--cl", "100", "--hco3", "24", "--json"])

        self.assertEqual(ret, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["anion_gap"], 16.0)

    def test_batch_csv(self):
        """Run batch processing with a temp CSV."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f_in:
            writer = csv.writer(f_in)
            writer.writerow(["na", "cl", "hco3", "albumin"])
            writer.writerow(["140", "105", "24", "4.0"])
            writer.writerow(["135", "95", "10", "2.5"])
            writer.writerow(["145", "110", "26", "3.0"])
            in_path = f_in.name

        out_path = in_path.replace(".csv", "_out.csv")

        try:
            import io
            from contextlib import redirect_stdout

            buf = io.StringIO()
            with redirect_stdout(buf):
                from cli import main
                ret = main(["batch", "--input", in_path, "--output", out_path])

            self.assertEqual(ret, 0)
            self.assertIn("Processed 3", buf.getvalue())

            with open(out_path, newline="") as f_out:
                reader = csv.DictReader(f_out)
                rows = list(reader)

            self.assertEqual(len(rows), 3)
            # Row 1: normal AG
            self.assertEqual(float(rows[0]["anion_gap"]), 11.0)
            self.assertEqual(rows[0]["ag_status"], "normal")
            # Row 2: DKA-like elevated AG
            self.assertEqual(float(rows[1]["anion_gap"]), 30.0)
            self.assertEqual(rows[1]["ag_status"], "elevated")
            # Row 3: normal AG
            self.assertEqual(float(rows[2]["anion_gap"]), 9.0)
            self.assertEqual(rows[2]["ag_status"], "normal")
        finally:
            os.unlink(in_path)
            if os.path.exists(out_path):
                os.unlink(out_path)


if __name__ == "__main__":
    unittest.main()
