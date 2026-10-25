# Pre-hardware-test validation — 2026-10-25

- ESPHome: **2026.10.0**, ESP-IDF **5.5.6**.
- Public configuration with dummy Wi-Fi credentials: **Config PASS**.
- Source generation: **Codegen PASS**.
- Full compilation in a fresh isolated build directory: **Clean Build PASS**.
- Build timestamp: 2026-10-25 11:51:47 +0100.
- All 68 local component source files match the production snapshot unchanged;
  all 45 compiled local C++/header files match the published component inputs.
- Reconstructed SDK: **841 files**, every size/hash matches the production SDK.
- No functional YAML changes for publication. Device identity is generic and
  the private static network settings are replaced by DHCP; secret references
  remain unresolved in the published source.
- Confirmed: 16-kHz ADF, DC correction, runtime gain, three wakewords, two native
  slots, MWW→VA handover, END/ERROR recovery, local confirmation sound, Assist
  delay, listening light, native player volume, dynamic touch and snapshot API.
- Removed audio probe symbols absent from the ELF; unused ADF-VAD define absent.
- Public dummy build linker use: 1,524,687 bytes flash, 125,295 bytes static RAM.
  This is not a physical-device RAM or stability measurement.
- Security: reviewed final source tree for known local secrets, credentials,
  tokens, private network addresses and forbidden build/backup files.
- No firmware binaries, private backups, build outputs or capture data published.

Public `onju-voice.yaml` SHA256:
`bf8d0fed872a90405ca18dd5eba3519887d3c3fdaaa2abd5460bdc8a1919282c`

SDK manifest SHA256:
`d7dba3e2d2445785b034d3f09dc9029e4dec830d9dc4940f9a94de51c98396f5`

Touch: **implemented / build validated, physical hardware validation pending**.

Touch hardware validated: **NO**. OTA performed: **NO**.
No final/stable release. The private production device configuration and the
previously installed firmware are unchanged by this publication.
