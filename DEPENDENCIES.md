# Pinned dependencies and source provenance

| Dependency | Reference | Role / terms |
| --- | --- | --- |
| ESPHome | 2026.10.0 | Python MIT; C++ runtime GPLv3 |
| ESP-IDF | 5.5.6, resolved by ESPHome | Espressif toolchain / Apache-2.0 and included notices |
| ESP-ADF | `302f9a2c113d302776b896149fbcdd6d718438da` | 16 local ADF components, upstream notices retained |
| esp-adf-libs | `3b34541c9212faa50c252f5fd00c36b6077ee96d` | Original upstream prebuilt libraries and license terms |
| esp-sr | `0c1eecaac259af95f76723b61d4e16cef5904fc7` | Required SDK component; upstream Espressif restrictions/notices |
| micro-wake-word-models | `40ff33f57f8fc6ad71a75ef085abbf742495b225` | Okay Nabu, Hey Jarvis, Hey Mycroft and VAD; upstream model licenses |
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

The local wakeup sound is the official Home Assistant Voice PE
`sounds/wake_word_triggered.flac`, pinned at commit
`d4e6fa43d6a1a7d342b7d4d403567e06516719de`, converted offline to MP3
without trim, gain, fade, normalization or effects and embedded in the existing
source header. Original FLAC SHA256:
`5c26cad33931670f2b62db5d2ed35c562b162e819ade38e646680065ad1b055f`.
Embedded MP3 SHA256:
`ecee971a3ebd377afab133d0baa776bb179bcee0580304ced05f75b3985ccef9`.
Source: https://github.com/esphome/home-assistant-voice-pe/blob/d4e6fa43d6a1a7d342b7d4d403567e06516719de/sounds/wake_word_triggered.flac .
The upstream license assigns non-runtime assets to MIT; the complete original
notice is retained in `docs/VOICE_PE_LICENSE.txt`. The unchanged production YAML retains a historical Freesound comment on the
flash URL; the embedded header and hashes above identify the actual asset. Error/timer sounds retain the existing
Tetele public URLs. No replacement sound or audio processing is introduced
for publication.

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
