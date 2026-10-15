# Hardware inventory

Every machine, cable, monitor, and adapter used in a test gets an ID here.
Experiment reports and failure entries refer to hardware **only** by these IDs,
so results from different people and days can be compared. Standardizing
test hardware is a Phase 1 goal of the project.

**ID prefixes:** `MAC` test Macs · `PC` controller PCs · `CAB` cables ·
`MON` monitors · `ADP` adapters, hubs, and docks. Never reuse an ID. If an item
is lost or broken, mark it *retired* and keep the row.

## Test Macs

| ID | Model | Board | Software | Ports | Holder | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `MAC-01` | MacBook Air (13-inch, M2, 2022) | J413 (`apple,j413`), t8112 | Fedora Asahi Remix 44 KDE; installed kernel `7.1.13-fairydust+` | ATC0 = left-back, next to MagSafe (m1n1 proxy); ATC1 = left-front (DP under test); MagSafe (power) | | Port labels from the J413 device tree (`typec0` "USB-C Left-back", `typec1` "USB-C Left-front") |

## Controller PCs

| ID | OS | WSL distribution | usbipd-win | Holder | Notes |
| --- | --- | --- | --- | --- | --- |
| `PC-01` | Windows | Ubuntu 26.04.1 LTS, WSL kernel 6.18.33.2 | 5.3.0 | | Uses Clang 22 with a rust-lld shim for m1n1's host stubs |

## Cables

| ID | Description | Rated for | Notes |
| --- | --- | --- | --- |
| | | | |

## Monitors

| ID | Make and model | Inputs | Max mode | Notes |
| --- | --- | --- | --- | --- |
| | | | | |

## Adapters, hubs, and docks

| ID | Make and model | Chipset (if known) | Outputs | Notes |
| --- | --- | --- | --- | --- |
| | | | | |
