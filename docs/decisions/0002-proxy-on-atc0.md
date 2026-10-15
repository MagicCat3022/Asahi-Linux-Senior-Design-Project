# 0002: m1n1 proxy cable on ATC0 for DP tests on J413

**Date:** 2026-10-14 · **Status:** accepted · **Deciders:** Mustafa Maras (full-team review pending)

## Context

m1n1 drives its USB proxy through one of the Mac's Type-C ports, and while the
hypervisor runs it removes that port's USB controller and PHY from the Linux
guest. On J413 (MacBook Air M2), fairydust's device tree routes external
DisplayPort through `atcphy1`, the left-front port.

With the proxy on ATC1, the baseline guest's DCP driver deferred forever with
`Failed to get dp-phy: -517`, and the live driver check failed
([2026-10-14-baseline-hv](../experiments/2026-10-14-baseline-hv/)). With the
proxy on ATC0, every DP driver bound
([2026-10-14-tipd-oob-fixes](../experiments/2026-10-14-tipd-oob-fixes/)).

The alternatives were to force Linux to reclaim the proxy's PHY, or to unbind
its controller. Both would cut the hypervisor's own connection.

## Decision

For DP testing on J413, the proxy cable goes on **ATC0** (left-back, next to
MagSafe) and the display under test on **ATC1** (left-front). The launcher
enforces this: with the `j413-usbc-dp` profile it requires iodev 4 and refuses
to start the guest otherwise.

## Consequences

- Only ATC1 can be tested for DP on J413 while running under HV. This matches
  fairydust's single "blessed" port
  ([F-007](../failures/F-007-single-blessed-dp-port.md)).
- Move the cable only while the Mac is off. If a failed HV start disabled the
  other port, restart into proxy mode with the cable already in place.
- Other boards need their own decision: check which `atcphy` the DTS routes
  DP through.
