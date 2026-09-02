# Anion Gap Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

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

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`anion_gap()`**: Standard Anion Gap.

AG = Na - (Cl + HCO3)

Parameters
----------
na   : Sodium in mEq/L
cl   : Chloride in mEq/L
hco3 : Bicarbonate in mEq/L

Returns
-------
Anion gap in mEq/L (rounded to 2 decimals).
- **`anion_gap_with_potassium()`**: Potassium-Adjusted Anion Gap.

AG_k = (Na + K) - (Cl + HCO3)

Some institutions include potassium in the calculation.
- **`corrected_anion_gap()`**: Albumin-Corrected Anion Gap.

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
- **`delta_gap()`**: Delta Gap = AG - reference_AG (default 12).

Represents the increase in unmeasured anions above normal.
- **`delta_ratio()`**: Delta Ratio = (AG - ref_AG) / (ref_HCO3 - HCO3).

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

---

## 📐 Mathematical Formulation & Logic

```text
  All formulas based on standard clinical references.
  Osmolal Gap = Measured Osm - Calculated Osm.
  Calculated Osm = 2*Na + Glucose/18 + BUN/2.8 + EtOH/4.6
  Dict with calculated_osm, osmolal_gap, and interpretation.
  "calculated_osm": round(calc_osm, 2),
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --na <value> --cl <value> --hco3 <value> --albumin <value>
```

### Parameter Reference
- `--na`: Specifies input measurement or parameter value.
- `--cl`: Specifies input measurement or parameter value.
- `--hco3`: Specifies input measurement or parameter value.
- `--albumin`: Specifies input measurement or parameter value.
- `--k`: Specifies input measurement or parameter value.
- `--measured-osm`: Specifies input measurement or parameter value.
- `--glucose`: Specifies input measurement or parameter value.
- `--bun`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t anion-gap-calculator .
docker run -p 8000:8000 anion-gap-calculator
```
