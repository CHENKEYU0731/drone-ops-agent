# Offline Operations Report

## Diagnosis

- `FAULT-BATTERY-001` identifies a high confidence battery low state of charge condition.

## Maintenance Recommendations

- `MAINT-BATTERY-001` asks for battery inspection before the next flight.

## Evidence

- `BATTERY_LOW_SOC` is referenced by `FAULT-BATTERY-001` and `MAINT-BATTERY-001`.

## Safety Boundary

- This report is offline-only and advisory-only.
- 该报告仅用于离线质量门禁，所有结论默认需要人工复核。
- It does not connect to a real drone, flight controller, MAVLink endpoint, PX4, ArduPilot, Gazebo, or SITL.
