# F-007: DisplayPort works on only one "blessed" port

| Field | Value |
| --- | --- |
| Status | upstream-reported |
| Class | Display routing |
| Hardware | All fairydust machines; on `MAC-01` the DP port is ATC1 |
| Setup | Any display on a port other than the blessed one |
| Rate | By design in current fairydust |
| Upstream | Issue [#637](https://github.com/AsahiLinux/linux/issues/637) (closed as not planned) |
| Owner | Unassigned |

## Symptom

Fairydust statically routes DisplayPort to one USB-C port per machine. Other
ports never get display output.

## Reproduction

Connect a display to any non-blessed port. On `MAC-01` that is ATC0, which the
team also uses for the m1n1 proxy; see
[decision 0002](../decisions/0002-proxy-on-atc0.md).

## Evidence

| Date | Experiment | Result |
| --- | --- | --- |
| — | — | — |

## Cause

**Confirmed (by design).** The device tree wires one port's PHY and crossbar
to `dcpext`. A contributor experimentally switched DCP routing between ports,
with hot-plug and cold-plug reported working. The remaining work is proper
per-port DRM connectors, dynamic DCP/DCPEXT assignment, crossbar routing,
power-domain management, correct device-tree bindings, and HDMI coexistence.

## Fix

Upstream closed #637 as "not planned" on 2026-09-26 because Asahi developers
intend to implement the proper solution themselves. That makes it a poor
primary target for the team, but useful to validate later, for example on a
Mac mini.

## History

- 2026-10-14: entry created from the fairydust research notes.
