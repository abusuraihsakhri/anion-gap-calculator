# Anion Gap Calculator

A pure Python clinical nephrology, critical care, and emergency medicine acid-base diagnostic engine implementing:
- **Standard Serum Anion Gap:** $\text{AG} = [\text{Na}^+] - ([\text{Cl}^-] + [\text{HCO}_3^-])$
- **Potassium-Adjusted Anion Gap:** $\text{AG}_{\text{K}} = ([\text{Na}^+] + [\text{K}^+]) - ([\text{Cl}^-] + [\text{HCO}_3^-])$
- **Albumin-Corrected Anion Gap (Figge-Jabor-Kazda-Fencl Formula):**
  $$\text{AG}_{\text{corr}} = \text{AG} + 2.5 \times (4.0 - \text{Albumin [g/dL]})$$
  *Hypoalbuminemia markedly reduces unmeasured anions, masking high anion gap metabolic acidosis.*
- **Delta Gap ($\Delta\text{AG}$) and Delta Ratio ($\Delta/\Delta$):**
  $$\Delta\text{AG} = \text{AG} - 12, \quad \Delta\text{Ratio} = \frac{\Delta\text{AG}}{24 - [\text{HCO}_3^-]}$$
  - **$< 0.4 - 0.8$:** Mixed high-AG and non-anion gap (hyperchloremic) metabolic acidosis (e.g. diarrhea, RTA).
  - **$0.8 - 2.0$:** Pure high anion gap metabolic acidosis (e.g. DKA, lactic acidosis, toxic alcohol ingestion).
  - **$> 2.0$:** High anion gap metabolic acidosis with concurrent metabolic alkalosis or pre-existing respiratory acidosis compensation.
- **Serum Osmolal Gap Calculation:**
  $$\text{Osm}_{\text{calc}} = 2 \times [\text{Na}^+] + \frac{\text{Glucose}}{18} + \frac{\text{BUN}}{2.8} + \frac{\text{EtOH}}{4.6}$$
  $$\text{Osmolal Gap} = \text{Measured Osm} - \text{Osm}_{\text{calc}}$$
  *Flags toxic alcohol ingestion (methanol, ethylene glycol, isopropanol) when osmolal gap $> 10 - 15\text{ mOsm/kg}$.*
- **High-Throughput Batch CSV Processing:** Evaluates metabolic panels across emergency and ICU patient cohorts.

Requires Python standard library only (zero external runtime dependencies).

---

## Acid-Base Differential & Mnemonic Diagnostic Tiers

| Clinical Classification | Criteria | Common Etiologies / Mnemonic |
|:------------------------|:---------|:-----------------------------|
| **High Anion Gap Metabolic Acidosis (HAGMA)** | $\text{AG} > 12\text{ mEq/L}$ | **GOLD MARK / MUDPILES:** Glycols, Oxoproline, L-lactate, D-lactate, Methanol, Aspirin, Renal failure, Ketoacidosis |
| **Normal Anion Gap (NAGMA)** | $\text{AG} \le 12$, low $\text{HCO}_3^-$ | **HARDCARP:** Hyperalimentation, Acetazolamide, Renal tubular acidosis, Diarrhea, Ureteroenterostomy, Pancreatic fistula |
| **Elevated Osmolal Gap** | $\text{Gap} > 10\text{ mOsm/kg}$ | Methanol, Ethylene glycol, Isopropanol, Propylene glycol, Ketoacidosis |

---

## Features

- **Albumin Correction:** Prevents missed metabolic acidosis in critically ill and septic patients with hypoalbuminemia.
- **Triple Acid-Base Disorder Detection:** Synthesizes AG, corrected AG, and Delta Ratio to detect concurrent non-gap acidosis and metabolic alkalosis.
- **Toxic Ingestion Screening:** Integrates measured osmolality, serum ethanol, glucose, and BUN to isolate occult alcohol ingestions.
- **Batch CSV Processing:** High-throughput batch evaluation with detailed interpretive summaries.

---

## Installation & Requirements

- Python 3.10+ (tested on 3.10, 3.11, 3.12)
- Zero external runtime dependencies. `pytest` is optional for running tests.

```bash
git clone https://github.com/abusuraihsakhri/anion-gap-calculator.git
cd anion-gap-calculator
```

---

## CLI Usage

### 1. Standard Anion Gap Evaluation
```bash
python cli.py calculate --na 140 --cl 100 --hco3 24 --json
```

### 2. Albumin-Corrected & Delta Ratio Evaluation
```bash
python cli.py calculate --na 135 --cl 98 --hco3 12 --albumin 2.5 --json
```

### 3. Toxic Ingestion / Osmolal Gap Evaluation
```bash
python cli.py calculate --na 140 --cl 100 --hco3 15 --measured-osm 325 --glucose 110 --bun 18 --json
```

### 4. Batch CSV Processing
```bash
python cli.py batch --input sample.csv --output results.csv
```

---

## Python API Quickstart

```python
import anion_gap

# Comprehensive evaluation
res = anion_gap.calculate(
    na=135.0,
    cl=98.0,
    hco3=12.0,
    albumin=2.5,
    measured_osm=320.0,
    glucose=180.0,
    bun=28.0,
)

print(f"Measured AG: {res['anion_gap']} mEq/L")
print(f"Albumin-Corrected AG: {res['corrected_anion_gap']} mEq/L")
print(f"Delta Ratio: {res['delta_ratio']} ({res['delta_ratio_interpretation']})")
if 'osmolal_gap' in res:
    print(f"Osmolal Gap: {res['osmolal_gap']['osmolal_gap']} mOsm/kg")
print(f"Summary: {res['summary']}")
```

---

## Running Tests

Run the test suite using standard `unittest` or `pytest`:

```bash
pytest -v
```

