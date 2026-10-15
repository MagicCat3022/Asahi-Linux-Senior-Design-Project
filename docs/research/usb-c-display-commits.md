# Display over USB-C: Current Commits and Upstream PRs

Branch: `fairydust` in this fork.
Fork: `MagicCat3022/Asahi-Linux-Senior-Design-Project`
Upstream: `AsahiLinux/linux`, branch `fairydust`.

> Most DP-altmode support lives as `HACK` commits on the upstream
> `fairydust` branch, not as merged PRs. Links below map each local
> commit to its upstream counterpart where one exists.

## Local commits on `fairydust`

All hashes link to this fork on GitHub.

### TIPD driver (2)

| Commit | Subject |
|---|---|
| [`296c91a`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/296c91ac1fa51a21117524561cd77eaf0c7fe62a) | `usb: typec: tipd: Track data_status changes for CD321x` |
| [`9c16792`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/9c16792154f8454ccbc6a28309d57d531ced015a) | `usb: typec: tipd: HACK: Use drm oob hotplug event` |

`296c91a` adds `data_status_changed` tracking so HPD can be debounced.
`9c16792` forwards HPD via `drm_connector_oob_hotplug_event()` using the
`displayport` phandle from the connector node.

Upstream ancestors:

* [`6cdd428`](https://github.com/AsahiLinux/linux/commit/6cdd428045c5091a59ad5281bb6897873ca684c0) — `TIPD WIP needs splitting / Forward HPD events to DRM`
* [`ca77753`](https://github.com/AsahiLinux/linux/pull/572/commits/ca77753b966c8ce4e9412b0863de0c4d89b147fe) in PR #572 — same `Track data_status changes` patch

Proper upstreaming is in progress on the mailing list (Sven Peter,
Sep 2025): `tipd: Read data status in probe`, `tipd: Trace data status
for CD321x`, `Apple Silicon USB3 support - TIPD changes`.

### Device-tree DP enable (5)

| Commit | Subject |
|---|---|
| [`7eb5629`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/7eb5629306578387dbee2add2ee4ec00239f723d) | `arm64: dts: apple: t8103: Add dp-altmode dts hacks` |
| [`bd43520`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/bd435201b52785b50b511ae7df87d1f9a8a2714e) | `arm64: dts: apple: t8112: Add dp-altmode dts hacks` |
| [`eebf132`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/eebf132beaf1f0c73b1471fa8f9b1f03aeb5f499) | `arm64: dts: apple: t60xx: j[34]1[46]: Add dp-altmode hacks` |
| [`0b0e4af`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/0b0e4af50f8cd1ccbec26265dab4de388a238182) | `arm64: dts: apple: t60xx: j[34]75: Add dp-altmode hacks` |
| [`b4a562f`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/b4a562f643bba937229e21994069c4ee291c3510) | `arm64: dts: apple: t6020-j474s: Add dp-altmode hacks` |

Pattern: add `displayport = <&dcpext>` (or `<&dcp>` on j473),
enable `dcpext`, `dcpext_dart`, `dispext0_dart`, wire `atcphy1` as
DP PHY, enable `dpaudio0/1`.

Upstream equivalents are the same patches on `fairydust`, visible in
PR #572 (commits `0861f4a`, `741278b`, `10cf5d5`, `a162796`, `eb8089b`).

### Power workaround (4)

| Commit | Subject |
|---|---|
| [`7003fe0`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/7003fe04cb40b6e16ca44726857fac2cba99ec43) | `HACK: t8103: Mark ps_atc1_common as always on` |
| [`6f72fa4`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/6f72fa4b26b42f8a88f1d17f4f0d2d482c1e93a8) | `HACK: t8112: Mark ps_atc1_common as always on` |
| [`a54f5fe`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/a54f5fe496c3fdee2615e42c8aa4018ed9f7f807) | `HACK: t60xx j[34]1[46]: Mark ps_atc1_common as always on` |
| [`cf8f098`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/cf8f09832bde2851528598ebbc3c59528348ea23) | `HACK: t60xx j[34]75: Mark ps_atc1_common as always on` |

All set `apple,always-on` on `ps_atc1_common`. Reason: missing
suspend/resume handling in ATC PHY for DP-altmode.

Upstream equivalents in PR #572: `65c58b6`, `d346775`, `eb7a134`, `90b97d8`.

### SIO audio fix (1)

| Commit | Subject |
|---|---|
| [`ce9f2eb`](https://github.com/MagicCat3022/Asahi-Linux-Senior-Design-Project/commit/ce9f2eba72c061a50b2d790450e90af3439d8c24) | `arm64: dts: apple: t8103: Add SIO alias` |

Adds `sio = &sio` alias so m1n1 injects SIO firmware. Tested on J313:
enables `apple-sio` RTKit + DP audio. This is the t8103 analog of the
upstream t8112-j493 fix below. No upstream PR for the t8103 variant;
it is novel to this fork.

## Upstream PRs in `AsahiLinux/linux`

| PR | Title | Relevance | State |
|---|---|---|---|
| [#572](https://github.com/AsahiLinux/linux/pull/572) | `t8112-j493: Enable SIO for DP audio` | Umbrella for 11/12 local commits. Manually merged as [`ad272ad`](https://github.com/AsahiLinux/linux/commit/ad272ad5d6742869cdd13320e43f9ed01bd1fb33) into [`96775a0`](https://github.com/AsahiLinux/linux/commit/96775a0e72995e79e13b93755d456cb128dcdc81) on `fairydust`. Contains `b40d412` SIO fix, `ca77753` data_status tracking, and all dp-altmode + always-on DTS hacks. | Closed |
| [#476](https://github.com/AsahiLinux/linux/pull/476) | `Enable dp-altmode for M1 Pro/Max MacBook Pro` | Moves `ENABLE_DCPEXT_TYPEC` per-machine for j314/j316 + pipehandler timeout bump. Overlaps `eebf132`. | Closed, not merged |
| [#622](https://github.com/AsahiLinux/linux/pull/622) | `Fix external display hotplug on DP alt mode` | Follow-up: DCP swap completion + ATC PIPE park before mux switch. Tested on j413. | Closed (AI policy) |
| [#236](https://github.com/AsahiLinux/linux/pull/236) | `dcp dptx hotplug fixes/changes` | Foundational DCP/DPTX hotplug, modeset, and ATC DP-PHY fixes by `jannau`. | Merged |
| [#515](https://github.com/AsahiLinux/linux/pull/515) | `atc: Fall back to USB2 when pipehandler state is DUMMY` | Keeps USB2 alive when SS lanes are taken by DP. Tested on j413 `fairydust`. | Closed |
| [#399](https://github.com/AsahiLinux/linux/pull/399) | `Add reset and UART VDM support to tipd` | Related TIPD work for Apple CD321x. | Closed |
| [#510](https://github.com/AsahiLinux/linux/pull/510) | `quiesce inactive DCPs on suspend, fix resume crash` | Suspend/resume path for secondary DCP. Alternative to always-on workaround. Tested on J313 `fairydust`. | Open |

Upstream branches:

* [`fairydust`](https://github.com/AsahiLinux/linux/tree/fairydust) — experimental USB-C DP output. One blessed port per machine.
* [`dp-altmode-WIP`](https://github.com/AsahiLinux/linux/tree/dp-altmode-WIP) — older DP-altmode staging.
