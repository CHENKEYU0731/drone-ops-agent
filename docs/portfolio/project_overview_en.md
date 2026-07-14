# drone-ops-agent Project Overview

## Summary

`drone-ops-agent` is an offline-first decision-support platform for UAV operations and maintenance. It imports local sample, mock, sanitized, or explicitly registered upstream log fixtures and produces flight summaries, anomalies, diagnostic hypotheses, maintenance recommendations, evidence-linked reports, audit records, and draft work orders for human review.

The project is a decision-support and quality-gate system, not a flight-control system. It does not connect to a real drone, execute MAVLink commands, launch a simulator, write flight-controller parameters, or dispatch maintenance work automatically.

## Engineering Highlights

- Unified offline parsing for CSV, JSON, PX4 ULog, and ArduPilot BIN inputs.
- Evidence-linked anomaly, diagnosis, maintenance, report, and audit outputs.
- Deterministic simulation validation across 14 mock scenarios and four result classes.
- Report and work-order quality gates with explicit human-review requirements.
- Fleet health aggregation and a local read-only dashboard bundle.
- Fifteen golden/mock case studies with expected-status and evidence-coverage metrics.
- Pinned and license-documented upstream ULog compatibility fixtures without committed binary caches.
- Clean-environment installation, wheel/sdist smoke tests, and checksum-protected release artifacts.

## Demonstration

```bash
python scripts/build_portfolio_showcase.py --out portfolio_showcase
```

The generated package contains a PDF operations report, evidence index, simulation rule results, draft work orders, fleet health output, case-study metrics, dashboard data, screenshots, and portfolio guides.

## Evidence Boundary

The repository's 1.0 expected-status match and evidence-coverage results apply only to its deterministic golden/mock cases. The three upstream ULog fixtures demonstrate parser compatibility, while `real_world_flight_verified=false` remains explicit. Neither result is a claim of real-world detection accuracy, airworthiness, maintenance authorization, or flight authorization.

All outputs remain offline-only, advisory-only, and human-review-required.
