# Anion Gap Calculator

A command-line tool for calculating and interpreting anion gap and related acid-base parameters. Python stdlib only — no external dependencies.

## What It Does

This calculator takes basic metabolic panel values (sodium, chloride, bicarbonate) and optionally additional labs (albumin, potassium, osmolality, glucose, BUN, ethanol) to compute:

| Metric | Formula | Clinical Use |
|--------|---------|-------------|
| **Anion Gap (AG)** | `Na - (Cl + HCO3)` | Identifies high-anion-gap metabolic acidosis |
| **Corrected AG** | `AG + 2.5 × (4.0 - albumin)` | Adjusts for hypoalbuminemia which can mask an elevated gap |
| **AG with Potassium** | `(Na + K) - (Cl + HCO3)` | Alternative AG used by some institutions |
| **Delta Gap** | `AG - 12` | Magnitude of unmeasured anion excess |
| **Delta Ratio** | `(AG - 12) / (24 - HCO3)` | Differentiates pure AG acidosis from mixed disorders |
| **Osmolal Gap** | `Measured Osm - (2×Na + Glucose/18 + BUN/2.8 + EtOH/4.6)` | Screens for toxic alcohol ingestion |

### Delta Ratio Interpretation

| Delta Ratio | Interpretation |
|:-----------:|----------------|
| < 1.0 | Mixed high-AG + non-AG metabolic acidosis |
| 1.0 – 2.0 | Pure high-AG metabolic acidosis |
| > 2.0 | Concurrent metabolic alkalosis |

### Anion Gap Status

| AG (mEq/L) | Status |
|:-----------:|--------|
| < 8 | Low (consider hypoalbuminemia, myeloma, lithium) |
| 8 – 12 | Normal |
| > 12 | Elevated (MUDPILES: Methanol, Uremia, DKA, Propylene glycol, Isoniazid, Lactic acidosis, Ethylene glycol, Salicylates) |

### Osmolal Gap Interpretation

| Gap (mOsm/kg) | Interpretation |
|:-------------:|----------------|
| ≤ 10 | Normal |
| 10 – 20 | Mildly elevated; consider early toxic alcohol ingestion |
| > 20 | Significantly elevated; suspect methanol, ethylene glycol, or isopropanol |

## Installation

No installation required. Uses only Python standard library (Python 3.8+).

```bash
git clone <repo-url>
cd anion-gap-calculator
```

## Usage

### Single Calculation

```bash
# Basic (Na, Cl, HCO3 required)
python cli.py calculate --na 140 --cl 100 --hco3 24

# With albumin correction
python cli.py calculate --na 140 --cl 100 --hco3 24 --albumin 3.5

# With potassium
python cli.py calculate --na 140 --cl 100 --hco3 24 --albumin 3.5 --k 4.5

# With osmolal gap
python cli.py calculate --na 140 --cl 100 --hco3 24 --measured-osm 310 --glucose 100 --bun 15

# JSON output
python cli.py calculate --na 140 --cl 100 --hco3 24 --json
```

### Batch Processing

Create a CSV with columns `na`, `cl`, `hco3` (required) and optionally `albumin`, `k`, `measured_osm`, `glucose`, `bun`, `ethanol`:

```csv
na,cl,hco3,albumin,k,glucose,bun
140,100,24,4.0,4.5,100,15
135,95,10,2.5,5.0,350,30
145,110,26,3.0,4.0,90,12
```

Run:

```bash
python cli.py batch --input sample_input.csv --output results.csv
```

### Python API

```python
import anion_gap

# Simple calculation
result = anion_gap.calculate(na=140, cl=100, hco3=24, albumin=3.5)
print(result["anion_gap"])           # 16.0
print(result["corrected_anion_gap"]) # 17.25
print(result["summary"])             # Clinical interpretation

# Individual functions
ag = anion_gap.anion_gap(140, 100, 24)           # 16.0
cag = anion_gap.corrected_anion_gap(ag, 3.5)     # 17.25
dr = anion_gap.delta_ratio(ag, 24)               # dict with ratio + interpretation
og = anion_gap.osmolal_gap(290, 140, 100, 15)    # dict with osmolal gap
```

## Running Tests

```bash
python -m pytest test_anion_gap.py -v
# or
python -m unittest test_anion_gap -v
```

## Clinical Disclaimer

This tool is for **educational and clinical decision support purposes only**. It does not replace clinical judgment. Always interpret results in the context of the complete clinical picture, arterial blood gas analysis, and patient history.

## License

MIT License. See [LICENSE](LICENSE) for details.
