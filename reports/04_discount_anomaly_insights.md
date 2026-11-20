# InsightPilot - Sales Trend & Anomaly Detection

## Dataset

Synthetic retail transactions covering January 2025 to October 2026.

## Detection Method

Electronics monthly average discount rates are compared against historical months before September 2026.

An observation is flagged if its average discount exceeds the historical mean plus three standard deviations.

This is a one-sided statistical rule, not proof of fraud or wrongdoing.

## Findings

- Historical discount: 5.07%
- Alert threshold: 6.52%
- September 2026 discount: 30.22%
- September anomaly score: 52.04
- Historical average monthly margin: 47.38%
- September profit margin: 27.91%

## Detected Anomalies

- 2026-09: 30.22% average discount.

## Business Recommendation

Review unusual discount activity, promotional campaigns, approval controls, and category profit margins before drawing conclusions.

The margin comparison is descriptive and does not establish that discounts alone caused a margin change.

## Limitations

The September 2026 discount anomaly was intentionally injected into synthetic data. The historical baseline is selected before the simulated event, so this is a demonstration rather than independent discovery of an unknown anomaly.
