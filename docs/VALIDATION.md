# Known-good validation — 2026-11-01

ESPHome 2026.10.0 / ESP-IDF 5.5.6. Publication checks: **Config PASS**, **Codegen PASS**, **Clean Build PASS**
from a fresh isolated build of the generic public source with dummy Wi-Fi credentials.
The factory image is merged from that same build, not a second functional source.

## Source equivalence

The production and public YAML are compared structurally, allowing only device
name/friendly name and removal of private static network settings. All local
component source files and all 842 SDK files match the hardware-tested source.
Five pinned wakeword manifests plus VAD are compiled. Two native slots, at most
two distinct enabled models, VA-IDLE END barrier, ADF/DC, timer safety, dynamic
touch, Improv Serial, OTA and local sounds are verified in generated/linked code.
Temporary capture probes, raw audio, private logs, backups, keys and build outputs
are excluded from Git. Public dummy credentials are not personal secrets.

## Hardware confirmation

User confirmed Okay Nabu/slot 1 and Alexa/slot 2 concurrently, correct routing,
STT/intent, immediate TTS, player handover, VA recovery and MWW DETECTING_WAKE_WORD.
The pending player START overwritten by STOP defect is resolved by waiting for
actual VA IDLE before END recovery. That fix is copied unchanged. Pipeline 2
required correction of a missing STT provider in HA, not a firmware change.

## Limits

Other model pairs, physical timer/touch functions and real-time/fault safety cases
are not claimed newly hardware validated. USB factory installation is not tested
by publication. Generic identity/DHCP/dummy credentials and build metadata mean
the public image is not byte-identical to the private installed image. Functional
source equivalence is verified; no OTA, HA change or other-device change occurs.
