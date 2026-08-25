#!/usr/bin/env python3
"""
Anion Gap Calculator

Real clinical calculator for acid-base interpretation using:
  - Anion Gap (AG)
  - Albumin-Corrected Anion Gap
  - Potassium-Adjusted Anion Gap
  - Delta Gap and Delta Ratio
  - Osmolal Gap

All formulas based on standard clinical references.
Python stdlib only.

Author: Dr. Abu Suraih Sakhri
License: MIT
"""

from typing import Dict, Any, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AG_NORMAL_LOW = 8.0    # mEq/L  (commonly cited range 8-12)
AG_NORMAL_HIGH = 12.0  # mEq/L
AG_REFERENCE = 12.0    # midpoint used in delta-ratio denominator
HCO3_REFERENCE = 24.0  # mEq/L  normal bicarbonate
ALBUMIN_NORMAL = 4.0   # g/dL
OSMOLAL_GAP_NORMAL = 10.0  # mOsm/kg


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

def anion_gap(na: float, cl: float, hco3: float) -> float:
    """
    Standard Anion Gap.

    AG = Na - (Cl + HCO3)

    Parameters
    ----------
    na   : Sodium in mEq/L
    cl   : Chloride in mEq/L
    hco3 : Bicarbonate in mEq/L

    Returns
    -------
    Anion gap in mEq/L (rounded to 2 decimals).
    """
    return round(na - (cl + hco3), 2)


def anion_gap_with_potassium(na: float, k: float, cl: float, hco3: float) -> float:
    """
    Potassium-Adjusted Anion Gap.

    AG_k = (Na + K) - (Cl + HCO3)

    Some institutions include potassium in the calculation.
    """
    return round((na + k) - (cl + hco3), 2)


def corrected_anion_gap(ag: float, albumin: float) -> float:
    """
    Albumin-Corrected Anion Gap.

    AG_corrected = AG + 2.5 * (4.0 - albumin)

    Albumin is a major unmeasured anion. Hypoalbuminemia lowers the AG,
    potentially masking a clinically significant elevated gap.  Adding
    2.5 mEq/L for every 1 g/dL below 4.0 corrects for this effect.

    Parameters
    ----------
    ag      : Measured anion gap (mEq/L)
    albumin : Serum albumin in g/dL

    Returns
    -------
    Corrected anion gap in mEq/L.
    """
    return round(ag + 2.5 * (ALBUMIN_NORMAL - albumin), 2)


def delta_gap(ag: float, reference_ag: float = AG_REFERENCE) -> float:
    """
    Delta Gap = AG - reference_AG (default 12).

    Represents the increase in unmeasured anions above normal.
    """
    return round(ag - reference_ag, 2)


def delta_ratio(ag: float, hco3: float,
                reference_ag: float = AG_REFERENCE,
                reference_hco3: float = HCO3_REFERENCE) -> Dict[str, Any]:
    """
    Delta Ratio = (AG - ref_AG) / (ref_HCO3 - HCO3).

    Interpretation:
      < 1.0  : Mixed high-AG + non-AG metabolic acidosis
      1.0-2.0: Pure high-AG metabolic acidosis
      > 2.0  : Concurrent metabolic alkalosis

    Parameters
    ----------
    ag           : Anion gap (mEq/L)
    hco3         : Bicarbonate (mEq/L)
    reference_ag : Normal AG (default 12)
    reference_hco3: Normal HCO3 (default 24)

    Returns
    -------
    Dict with 'delta_gap', 'delta_ratio', and 'interpretation'.
    """
    dg = ag - reference_ag
    denom = reference_hco3 - hco3

    if denom == 0:
        # HCO3 is normal — ratio is undefined
        return {
            "delta_gap": round(dg, 2),
            "delta_ratio": None,
            "interpretation": "HCO3 is at reference; delta ratio undefined",
        }

    ratio = dg / denom

    if ratio < 1.0:
        interp = "Mixed high-anion-gap + non-anion-gap metabolic acidosis"
    elif ratio <= 2.0:
        interp = "Pure high-anion-gap metabolic acidosis"
    else:
        interp = "Concurrent metabolic alkalosis"

    return {
        "delta_gap": round(dg, 2),
        "delta_ratio": round(ratio, 3),
        "interpretation": interp,
    }


def osmolal_gap(measured_osm: float, na: float, glucose: float,
                bun: float, ethanol: float = 0.0) -> Dict[str, Any]:
    """
    Osmolal Gap = Measured Osm - Calculated Osm.

    Calculated Osm = 2*Na + Glucose/18 + BUN/2.8 + EtOH/4.6

    An elevated osmolal gap (>10 mOsm/kg) suggests the presence of
    unmeasured osmoles such as methanol, ethylene glycol, or isopropanol.

    Parameters
    ----------
    measured_osm : Measured serum osmolality in mOsm/kg
    na           : Sodium in mEq/L
    glucose      : Glucose in mg/dL
    bun          : Blood urea nitrogen in mg/dL
    ethanol      : Ethanol in mg/dL (default 0)

    Returns
    -------
    Dict with calculated_osm, osmolal_gap, and interpretation.
    """
    calc_osm = 2.0 * na + glucose / 18.0 + bun / 2.8 + ethanol / 4.6
    gap = measured_osm - calc_osm

    if gap <= OSMOLAL_GAP_NORMAL:
        interp = "Normal osmolal gap"
    elif gap <= 20:
        interp = "Mildly elevated osmolal gap; consider early toxic alcohol ingestion"
    else:
        interp = "Significantly elevated osmolal gap; suspect toxic alcohol ingestion (methanol, ethylene glycol, isopropanol)"

    return {
        "calculated_osm": round(calc_osm, 2),
        "measured_osm": round(measured_osm, 2),
        "osmolal_gap": round(gap, 2),
        "interpretation": interp,
    }


# ---------------------------------------------------------------------------
# Full interpretation
# ---------------------------------------------------------------------------

def interpret(ag: float, hco3: float, albumin: Optional[float] = None,
              na: Optional[float] = None, cl: Optional[float] = None,
              k: Optional[float] = None,
              measured_osm: Optional[float] = None,
              glucose: Optional[float] = None,
              bun: Optional[float] = None,
              ethanol: Optional[float] = None) -> Dict[str, Any]:
    """
    Full acid-base interpretation combining all available parameters.

    Returns a dict with all computed values and clinical interpretation.
    """
    result: Dict[str, Any] = {}

    # --- Anion Gap ---
    result["anion_gap"] = ag
    if ag < AG_NORMAL_LOW:
        result["ag_status"] = "low"
    elif ag <= AG_NORMAL_HIGH:
        result["ag_status"] = "normal"
    else:
        result["ag_status"] = "elevated"

    # --- Albumin-corrected AG ---
    if albumin is not None:
        cag = corrected_anion_gap(ag, albumin)
        result["corrected_anion_gap"] = cag
        if cag < AG_NORMAL_LOW:
            result["corrected_ag_status"] = "low"
        elif cag <= AG_NORMAL_HIGH:
            result["corrected_ag_status"] = "normal"
        else:
            result["corrected_ag_status"] = "elevated"
        # Use corrected AG for delta ratio if albumin available
        ag_for_delta = cag
    else:
        ag_for_delta = ag

    # --- Potassium-adjusted AG ---
    if k is not None and na is not None and cl is not None:
        ag_k = anion_gap_with_potassium(na, k, cl, hco3)
        result["anion_gap_k"] = ag_k

    # --- Delta Gap & Delta Ratio ---
    dr = delta_ratio(ag_for_delta, hco3)
    result["delta_gap"] = dr["delta_gap"]
    result["delta_ratio"] = dr["delta_ratio"]
    result["delta_ratio_interpretation"] = dr["interpretation"]

    # --- Osmolal Gap ---
    if all(v is not None for v in (measured_osm, na, glucose, bun)):
        og = osmolal_gap(measured_osm, na, glucose, bun,
                         ethanol if ethanol is not None else 0.0)
        result["osmolal_gap"] = og

    # --- Clinical summary ---
    summary_parts = []

    if result["ag_status"] == "elevated":
        summary_parts.append(
            "Elevated anion gap metabolic acidosis (MUDPILES: "
            "Methanol, Uremia, DKA, Propylene glycol, Isoniazid/INH, "
            "Lactic acidosis, Ethylene glycol, Salicylates)"
        )
    elif result["ag_status"] == "normal":
        summary_parts.append("Normal anion gap; consider non-AG acidosis if acidemic")
    elif result["ag_status"] == "low":
        summary_parts.append(
            "Low anion gap; consider hypoalbuminemia, "
            "multiple myeloma, lithium, or bromide intoxication"
        )

    summary_parts.append(dr["interpretation"])

    if "osmolal_gap" in result:
        summary_parts.append(result["osmolal_gap"]["interpretation"])

    result["summary"] = " | ".join(summary_parts)

    return result


# ---------------------------------------------------------------------------
# Convenience: compute from raw lab values
# ---------------------------------------------------------------------------

def calculate(na: float, cl: float, hco3: float,
              albumin: Optional[float] = None,
              k: Optional[float] = None,
              measured_osm: Optional[float] = None,
              glucose: Optional[float] = None,
              bun: Optional[float] = None,
              ethanol: Optional[float] = None) -> Dict[str, Any]:
    """
    All-in-one calculation from raw lab values.

    Parameters
    ----------
    na           : Sodium (mEq/L) — required
    cl           : Chloride (mEq/L) — required
    hco3         : Bicarbonate (mEq/L) — required
    albumin      : Serum albumin (g/dL) — optional
    k            : Potassium (mEq/L) — optional
    measured_osm : Measured osmolality (mOsm/kg) — optional
    glucose      : Glucose (mg/dL) — optional
    bun          : BUN (mg/dL) — optional
    ethanol      : Ethanol (mg/dL) — optional

    Returns
    -------
    Dict with all computed values and clinical interpretation.
    """
    ag = anion_gap(na, cl, hco3)
    return interpret(
        ag=ag, hco3=hco3, albumin=albumin, na=na, cl=cl, k=k,
        measured_osm=measured_osm, glucose=glucose, bun=bun, ethanol=ethanol,
    )
