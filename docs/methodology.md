# IntelliMaint AI — Machine Learning Methodology & Physics Formulation

## 1. Domain Problem Statement

Predictive Maintenance (PdM) represents a paradigm shift from reactive ("run-to-failure") and rigid preventive ("calendar-based") maintenance strategies. In electrical and mechanical manufacturing environments:
- **Reactive maintenance** results in catastrophic spindle seizure, destroyed cutting tools, scrapped workpieces, and hazardous machine stops.
- **Preventive maintenance** discards cutting inserts and mechanical seals prematurely, generating substantial unnecessary tooling overhead.

**IntelliMaint AI** leverages multi-modal sensor telemetry (spindle rotational speed, motor torque, cutting tool wear duration, and process temperatures) to compute instantaneous machine failure probability, identify the physical failure mode, and prescribe actionable corrective maintenance before breakdown occurs.

---

## 2. Physics-Grounded Failure Modes (UCI AI4I 2020)

The core benchmark dataset used is the public **UCI AI4I 2020 Predictive Maintenance Dataset** (Matzka, 2020), which reflects physical machine tool behaviors governed by 5 distinct failure mechanisms:

### A. Tool Wear Failure (TWF)
Cutting tools experience progressive flank and crater wear due to friction, abrasive particles, and cyclic thermal stress.
- When tool wear reaches the critical threshold between **200 and 240 minutes**, micro-chipping occurs, accelerating tool fracture risk.
- In the platform, an alert is raised when tool wear exceeds 160 minutes (advisory) and 200 minutes (critical replace immediately).

### B. Heat Dissipation Failure (HDF)
Cutting heat must be dissipated through coolant flow and ambient air convection.
- Heat dissipation fails when the difference between cutting process temperature and ambient air temperature drops below **8.6 Kelvin** while rotational speed is below **1,380 RPM**:
  $$\Delta T = T_{\text{process}} - T_{\text{air}} < 8.6\text{ K} \quad \text{and} \quad \omega < 1380\text{ RPM}$$
- Inadequate heat dissipation causes thermal expansion of the machine tool spindle, leading to bearing seizure and severe workpiece dimensional error.

### C. Power Failure (PWF)
Electric spindle motors operate within a rated continuous torque-speed mechanical power envelope.
- Mechanical power $P$ is calculated as the product of angular velocity $\omega$ and torque $\tau$:
  $$P = \omega \cdot \tau = \left(\frac{2\pi \cdot \text{RPM}}{60}\right) \cdot \tau \quad \text{[Watts]}$$
- A Power Failure is triggered when mechanical power falls below **3,500 Watts** (spindle stall / slip) or exceeds **9,000 Watts** (overload / excessive cutting depth).

### D. Overstrain Failure (OSF)
Severe mechanical strain arises when high cutting torque is sustained by heavily worn cutting tools.
- The strain product is defined as:
  $$\text{Strain Product} = \tau \times \text{Tool Wear} \quad [\text{Nm}\cdot\text{min}]$$
- If this product exceeds variant-specific limits (**11,000 Nm·min for Type L**, **12,000 for Type M**, and **13,000 for Type H**), catastrophic workpiece stall or spindle arbor deflection occurs.

### E. Random Failure (RNF)
Represents stochastic, unmodeled external electrical surges, power blips, or foreign material collisions (~0.1% baseline incidence).

---

## 3. Mathematical Feature Engineering

Raw sensor telemetry is transformed using domain-specific engineering equations prior to machine learning inference:

| Feature Name | Mathematical Definition | Physical Significance |
| :--- | :--- | :--- |
| `temp_diff` | $T_{\text{process}} - T_{\text{air}}$ | Heat convection rate and thermal equilibrium |
| `power_watts` | $\left(\frac{2\pi \cdot \text{rotational\_speed}}{60}\right) \times \text{torque}$ | Mechanical shaft power delivered to cutting interface |
| `strain_product` | $\text{torque} \times \text{tool\_wear}$ | Mechanical stress coupled with tool flank degradation |
| `temp_ratio` | $T_{\text{process}} / T_{\text{air}}$ | Relative thermodynamic expansion ratio |
| `torque_speed_ratio` | $\text{torque} / (\text{rotational\_speed} + 10^{-5})$ | Specific dynamic mechanical load impedance |

---

## 4. Machine Learning Benchmark & Model Selection

### Class Imbalance & Evaluation Metric Strategy
Industrial machine failure is an uncommon event. In the benchmark dataset of 10,000 records, only **339 failures** exist (**3.39% failure incidence**).

Under extreme class imbalance:
- **Accuracy is misleading:** A trivial null classifier predicting "No Failure" achieves 96.6% accuracy while failing to detect 100% of actual breakdowns.
- **Selected Optimization Metrics:** Models are strictly benchmarked on **F1-Score** (harmonic mean of Precision and Recall) and **PR-AUC / Average Precision** (area under the Precision-Recall curve), alongside ROC-AUC and Confusion Matrix verification.

### Benchmark Comparative Results

The 3 candidate models were trained with stratified 80/20 splitting (8,000 train samples / 2,000 held-out test samples with 68 actual failures).

| Algorithm | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Test Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gradient Boosting (Champion)** | **0.965** | **0.809** | **0.880** | **0.963** | **0.889** | **99.25%** |
| Random Forest (Balanced) | 0.773 | 0.853 | 0.811 | 0.979 | 0.868 | 98.65% |
| Logistic Regression (Baseline) | 0.181 | 0.882 | 0.301 | 0.939 | 0.419 | 86.05% |

### Champion Model Feature Importances
From the Gradient Boosting ensemble, the top driving parameters extracted from tree splits are:
1. **`strain_product` ($\tau \times \text{tool\_wear}$):** 27.2% importance
2. **`power_watts` ($P = \omega \cdot \tau$):** 26.3% importance
3. **`Rotational speed [rpm]`:** 25.7% importance
4. **`temp_ratio`:** 6.3% importance
5. **`Tool wear [min]`:** 3.7% importance

This confirms that the machine learning algorithm learns physical engineering invariants rather than spurious correlations.

---

## 5. Calibrated Risk Tiers & Operational Decision Rules

Model failure probability $P(\text{failure})$ is mapped to three operational decision tiers:

| Risk Tier | Probability Range | Operational Meaning | Suggested Facility Action |
| :--- | :--- | :--- | :--- |
| **Low Risk** | $P < 0.25$ | Nominal operating envelope; wear within tolerance | Continue scheduled operations; routine lubrication |
| **Medium Risk** | $0.25 \le P < 0.65$ | Early degradation detected; marginal convection/wear | Queue inspection; stage replacement tooling; monitor |
| **High Risk** | $P \ge 0.65$ | Severe hazard threshold; imminent breakdown risk | Dispatch corrective work order; inspect tooling immediately |

---

## 6. System Boundaries & Educational Disclaimer

1. **Portfolio & Educational Scope:** IntelliMaint AI is designed as an academic demonstration of predictive maintenance engineering.
2. **Non-Certified Safety System:** Risk scores are decision-support aids and must **never** replace certified safety PLCs, physical interlocks, emergency stop buttons, or manufacturer operating limits.
3. **Hazard Rate vs. RUL:** Failure probability represents an instantaneous likelihood of failure under current operational telemetry, not a deterministic guarantee of hours remaining until breakdown.
