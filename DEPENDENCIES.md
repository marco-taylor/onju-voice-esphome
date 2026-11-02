# Pinned dependencies and source provenance

| Dependency | Reference | Role / terms |
| --- | --- | --- |
| ESPHome | 2026.10.0 | Python MIT; C++ runtime GPLv3 |
| ESP-IDF | 5.5.6, resolved by ESPHome | Espressif toolchain / Apache-2.0 and included notices |
| ESP-ADF | `302f9a2c113d302776b896149fbcdd6d718438da` | 16 local ADF components, upstream notices retained |
| esp-adf-libs | `3b34541c9212faa50c252f5fd00c36b6077ee96d` | Original upstream prebuilt libraries and license terms |
| esp-sr | `0c1eecaac259af95f76723b61d4e16cef5904fc7` | Required SDK component; upstream Espressif restrictions/notices |
| micro-wake-word-models | `40ff33f57f8fc6ad71a75ef085abbf742495b225` | Okay Nabu, Hey Jarvis, Hey Mycroft, experimental Hey Home Assistant, Alexa and VAD; upstream model licenses |
| Idskov timer principle | `6b1809d780e0c741a5ef7b1b79b2ccbfc73e8f6f` | Timer-only adaptation; MIT, Copyright 2026 Nico Idskov |
| rmeissn touch principle | `09b3b65c237e8dc42c40677492965865429fe12e` | MIT; original ./LICENSE retained |

The Python/C++ components under
`onju-voice-assets/tetele-production/components/` are the current production
sources, including ESPHome API compatibility, DC correction, gain and native
slot/handover patches. The complete Tetele component MIT notice is retained in
`onju-voice-assets/tetele-production/LICENSE`; ESPHome-derived C++ retains its
upstream license obligations. The root MIT license does not override the
licenses of ESPHome, Espressif, models, audio or bundled third-party code.

The exact SDK input is recorded in
`onju-voice-assets/tetele-production/sdk-manifest.json`: full commit URLs,
archive SHA256 values, every selected SDK file's SHA256 and size, and source
overlay mapping. `tools/bootstrap_sdk.py` reconstructs these inputs in the
ignored `onju-voice-assets/tetele-production/sdk/esp-adf/` directory. Local SDK
compatibility patches and the existing flash-stream shim/sound header are
published under `onju-voice-assets/tetele-production/sdk-overlay/`.
All generated SDK files must match the manifest before use.

The current wake and timer sounds are the official Voice-PE sounds pinned to
commit d4e6fa43d6a1a7d342b7d4d403567e06516719de, with sound-specific copyright
© 2024 Clayton Charles Tapp and CC BY 4.0 license. They are not covered merely
by the general upstream MIT notice. Original FLACs, exact hardware-tested MP3s,
SHA256, encoder parameters and attribution are under
`./onju-voice-assets/tetele-production/voicepe-sounds/`. The existing generic
Tetele error MP3 is byte-unchanged and local; its separate UNIVERSFIELD
attribution and historical license evidence are documented there. No unused
Voice-PE sounds are distributed. Encoding only; no DSP/gain/trim/fade changes.

The timer principle remains attributed to Idskov at the pinned commit above;
the original MIT notice is in ./docs/IDSKOV_LICENSE.txt. Timer control, repeat,
dismiss and safety logic are unchanged. The former generated CC0 timer signal
is retained in history; it is no longer the active timer audio.

The generated IDF dependency lock is recorded in `docs/idf-dependencies.lock`.
Its local path entries are relative to the repository; its managed package
versions/hashes are retained. The build must still download ESPHome toolchain,
IDF registry dependencies and pinned model assets. ESPHome pins the framework
and SDK inputs, but no bit-identical BIN across timestamps, toolchain hosts,
device names or credentials is promised. Never publish a credential-containing
firmware image.

The older full-duplex `esp_audio_stack` / `esp_aec` / `proxy_speaker` components
are no longer part of the active source tree. Historical upstream sources and
attributions remain available through Git history and `docs/UPSTREAM_README.md`.
