# Onju Voice – 1.2.0

Production release of the hardware-accepted `1.2.0-rc.2` functionality
(source `78bf58dbcc1f1ece2daa4957776cb3608fc0d7fb`). Only release/version metadata
changes from RC2. Historical known-good releases remain unchanged.
See [managed-update and migration documentation](./docs/MANAGED_UPDATES.md).

Hardware-tested firmware for the original ESP32-S3 Onju Voice PCB with 8 MB
PSRAM, built with **ESPHome 2026.10.2 / ESP-IDF 5.5.6**. Distributed as a
**production release 1.2.0**.

**HARDWARE TESTED:** Okay Nabu / slot 1 and Alexa / slot 2 concurrently; correct
dual-pipeline routing, STT, conversation/intent, immediate TTS, media-player
handover, VA-IDLE END recovery and MWW DETECTING_WAKE_WORD. Dynamic touch,
timers, Center-touch timer dismissal, MWW after timer, and the local Voice-PE
wake and new timer sounds were also confirmed on the real device.

**AVAILABLE:** five selectable wakewords and two native slots. This does not
claim that every possible model pair was individually hardware tested. The
15-minute timer safety limit and 10-second player-IDLE fault recovery are
implemented/build validated; dedicated real-time/fault-injection tests are not
newly claimed by this milestone.

**BUILD VALIDATED:** Config PASS, Codegen PASS, fresh Clean Build PASS with
ESPHome 2026.10.2; see [./docs/VALIDATION.md](./docs/VALIDATION.md).

The Tetele-derived ADF architecture is retained. No AEC, rmeissn FIR or
48-kHz microphone path is enabled.

## Software Mute — hardware tested

Home Assistant exposes **Mute** under the device's **Configuration** entities
(`entity_category: config`). Native `microphone.mute` / `microphone.unmute`
silence microphone PCM delivered to consumers. Wakewords cannot start Assist
while muted. The existing LED state machine shows solid red. Unmute restores
normal microWakeWord operation without changing either wakeword/pipeline slot.
Mute starts **OFF** after reboot. No mute sounds added.

Hardware tested: actual microphone silence, no wakeword response while muted,
repeated mute/unmute, Okay Nabu and Alexa/pipeline 2 after unmute, red indication,
and media player and timer operation while muted. This is software muting of
microphone data, not an electrical microphone disconnect.

## Local wakeword startup and persistent sensitivity

ESPHome 2026.10.2 known-good milestone: the user confirmed wakeword operation
on the installed firmware. The local startup reconciler runs after switch restore
and component setup. It honors **Use Wake Word OFF**, hardware mute and software
mute, leaves microphone startup to microWakeWord, and verifies actual audio and
successful wakeword inference. Readiness failures use at most two bounded attempts
(15-second check, 10-second release, 45-second overall deadline), never an endless
restart loop. Listening does not require a VA client to subscribe first. The
normal VA-IDLE/TTS handover and recovery remain unchanged.

**Wake word sensitivity is persistent.** The same three options and cutoff table
use a versioned preference isolated from obsolete four-option indices. First use
defaults to Moderate only if no valid new preference exists. Actual user changes
are saved and synchronized after saving; repeating the same value does not write
again. The normal global 60-second preference policy remains unchanged. Other
switch/model changes should be allowed to sync before hard power removal.

Automated startup/restore/persistence, mute, TTS and timer tests pass. The user
confirmed wakeword, Assist/TTS, mute, timer/touch, real cold boot and sensitivity
retention on two devices. This does not claim every offline/model-pair test.

**Home Assistant Managed Updates:** native HA firmware entity,
GitHub-latest manifest, HTTPS OTA and a checked per-device identity/network profile.
Direct Home Assistant installation was hardware tested; bootstrap and retention
were also verified on a second device. Native ESPHome OTA remains. Never install
a generic image on a legacy private
node before its one-time migration has been confirmed. No automatic installation.

## Architecture

- Local Tetele-derived ADF components and all 16 required ADF SDK components.
- ADF microphone and player paths at **16 kHz**, LEFT channel, 32-bit I2S data/slots.
- Integer DC correction before runtime microphone gain and clipping.
- Runtime microphone gain, wakeword sensitivity and existing cutoff settings.
- Five pinned selectable models: **Okay Nabu**, **Hey Jarvis**, **Hey Mycroft**,
  **Hey Home Assistant** (official experimental model), and **Alexa**, plus VAD.
  Hey Home Assistant and Alexa retain their official manifest cutoffs.
- **Two native pipeline/wakeword slots**, managed by the Home Assistant voice
  assistant protocol. Each offers no wakeword or any of the five models. Only
  selected models are enabled: at most two different models simultaneously.
  Identical selections enable one model; slot 1 retains routing priority.
- MWW → VA handover waits for MWW teardown and microphone release, rechecks
  ownership, and retains END/ERROR recovery. END recovery waits for actual
  VA IDLE before it may stop/release consumers, preserving pending TTS START.
- Local flash-resident wakeword confirmation sound and configurable Assist
  start delay; Wake Word Listening Light and existing LED behavior.
- Native ADF media-player volume; no additional volume Number entity.
- Dynamic S3 touch calibration, adapted from rmeissn commit
  `09b3b65c237e8dc42c40677492965865429fe12e` to ESPHome 2026.10.2 / IDF 5.5.6.
- Native Voice Assistant timers: proportional LED countdown, optional **Timer LED**
  switch (default ON), repeated local flash MP3 alarm and Center-touch dismissal.
- No old PCM/raw capture probes or audio diagnostic buffers.

The microphone source ID `mww_probe_source` is retained for compatibility; it
is the functional microphone source, not an audio capture probe.

## Build the known-good source

Use Python 3.12–3.14 and the pinned ESPHome 2026.10.2 environment
for compilation. ESPHome 2026.10.2 selects ESP-IDF 5.5.6. The native ESP-IDF
builder/toolchain and IDF Component Manager require network access and disk
space for their dependencies. See [./DEPENDENCIES.md](./DEPENDENCIES.md).

```sh
python3 tools/bootstrap_sdk.py
python3 -m pip install -r requirements.txt
cp secrets.example.yaml secrets.yaml
# Edit secrets.yaml locally before using real hardware.
esphome config onju-voice.yaml
esphome compile --only-generate onju-voice.yaml
esphome clean onju-voice.yaml
esphome compile onju-voice.yaml
```

The bootstrap downloads three exact Espressif commits, checks archive SHA256,
then reconstructs every SDK file against the production manifest and local
source overlays. Generated SDK files and downloads are ignored. Espressif's
upstream archives include prebuilt libraries; they are fetched from their
original source, not rehosted as firmware in this repository.

The public YAML uses `!secret wifi_ssid` / `!secret wifi_password`, a generic
device name and DHCP. Set credentials only in your ignored local secret file.
The public-source build is checked with dummy credentials. No personal device
configuration, tokens, backups, firmware BINs or build outputs are versioned.

`./main.yaml` and `./onju_duplex_i2s.yaml` remain compatibility entry points to
`./onju-voice.yaml`; the latter filename is historical and does not enable AEC
or a different full-duplex architecture.

## Voice Assistant timers

Create timers through Home Assistant Assist, for example “Set a timer for
10 minutes”. The earliest active timer drives an orange proportional bar on
the four top LEDs; the partial pixel dims as the remaining fraction shrinks.
Paused, zero-length and expired entries do not drive the bar. Native timer
updates, pause/resume and cancellation remain owned by Home Assistant.

**Timer LED** defaults to ON and toggles the running countdown only. An expired
timer still produces a red alarm animation and repeated local
`flash://onju-timer.mp3` playback when the existing VA/player is idle. No runtime
HTTP download, new decoder, RTTTL or Idskov audio architecture is introduced.
The existing MP3 decoder and 16-kHz ADF output path are retained.

Center touch dismisses a ringing alarm immediately; releasing that press does
not also launch the previous Center action. Otherwise the existing Center
behavior is unchanged. VOL−/+ and dynamic touch detection are unchanged.
Normal media-player STOP also dismisses the alarm during silent repeat gaps;
a new VA session or media/TTS URL takes over without a later timer stop
interrupting that new playback. Volume changes do not dismiss the alarm.

The timer waits behind existing media/TTS instead of forcibly interrupting it.
LED priority is temporary volume feedback, Assist activity, timer alarm,
existing media/notification visuals, countdown, then the existing idle/wakeword
state. Cleanup releases owned timer playback and uses the existing recovery
when no VA session has taken ownership. The original local confirmation tone,
DC/gain, native slots and existing guarded handover/recovery are preserved.

A ringing session is limited to **15 minutes**, including time waiting for the
player. Additional expired timers do not extend that session. The timeout uses
the same central `dismiss()` cleanup as manual dismissal; a new session starts
a fresh deadline. Cleanup waits at most **10 seconds** for player IDLE, then
logs one WARN and continues the existing recovery if no active VA owns it.
The existing recovery retains its own bounded waits and ownership guards.
No persistent media-player repeat mode or additional stop wakeword is used.

Timer behavior follows the principle from
[Idskov/onju-voice-esphome](https://github.com/Idskov/onju-voice-esphome/tree/6b1809d780e0c741a5ef7b1b79b2ccbfc73e8f6f),
adapted to our existing architecture. Timer operation and Center dismissal
are hardware tested with the current local Voice-PE timer asset.

## Touch controls

| Pin | Function |
| --- | --- |
| GPIO4 | VOL−, native player −0.05; hold repeats |
| GPIO3 | Dismiss timer alarm; otherwise existing VA/player behavior |
| GPIO2 | VOL+, native player +0.05; hold repeats |

Each second, calibration reads S3 smooth and benchmark data directly instead
of the event-only `get_value()` cache. A five-sample idle mean determines
`max(100, mean × percentage)` as a **delta** threshold. The threshold is written
to the S3 comparator through the pinned IDF LL accessor without stopping
scanning or resetting the hardware benchmark. Hardware touch detection still
compares smooth data against the hardware benchmark, not the software mean.

The visible **Touch threshold percentage** remains (0.25–5%, default 0.75%).
Calibration freezes during detected touch or a hardware excursion and waits
for two seconds of quiet before resuming. Persistent positive anomalies are
not force-accepted after ten samples. Large lasting upward baseline shifts
may therefore need a restart. A finger already present during boot cannot be
reliably distinguished from the initial baseline: boot with pads untouched.
This implementation depends on S3/IDF internals and must be rechecked on upgrades.

Existing Action behavior is retained; rmeissn's alternative multi-click,
long-press reset, speaker and timer architecture is not imported.

The ESPHome API action `touch_diag_snapshot` provides an on-demand snapshot
for all three pads: raw, smooth, hardware benchmark, signed delta, software
calibration baseline, software/hardware threshold, read status and touch ON/OFF.
Keep `setup_mode: false` for normal use. There is no periodic diagnostic flood.

Hardware-tested: VOL−, Center, VOL+, dynamic touch, timer countdown/alarm,
Center dismissal, and MWW recovery after timer. The existing on-demand
`touch_diag_snapshot` remains available. Further model combinations and
controlled safety/fault tests remain useful future checks.

## Factory installation and OTA

Download the factory BIN and SHA256 file from the matching GitHub prerelease.
Verify SHA256, then use an ESP32-compatible USB flashing tool to write the full
factory image at **0x0** (ESP32-S3, 16-MB flash). It contains the bootloader,
partition table, OTA data and application; do not treat it as an OTA-only image.
This publication does not itself test USB recovery/first installation.

Use **Improv Serial** to provision personal Wi-Fi credentials after USB
installation. The distributed image uses generic identity/DHCP and intentionally
non-personal dummy Wi-Fi values. No API keys, encryption keys or personal network
settings are included. The firmware retains ESPHome OTA support. For later OTA,
use an application/OTA image built from your private local secret configuration;
never install the full factory image through an OTA-only path.

## Local sound assets

Wake and timer use official Voice-PE assets pinned to
`d4e6fa43d6a1a7d342b7d4d403567e06516719de`, converted offline to MP3 for the
existing ADF player. No normalization, gain change, trimming, fades or offline
resampling. The existing generic error sound is also flash-resident, byte
unchanged. Playback has no runtime GitHub dependency. The microphone remains
16 kHz even though original playback assets are 48 kHz.

Voice-PE sounds: © 2024 Clayton Charles Tapp, **CC BY 4.0**, not the repository's
general MIT license. See [asset attribution](./onju-voice-assets/tetele-production/voicepe-sounds/README.md)
and the included sound-specific notice, manifests and originals.

## Provenance and licenses

Based on [Tetele](https://github.com/tetele/onju-voice-satellite),
[gnumpi's ADF components](https://github.com/gnumpi/esphome_audio), ESPHome and
[rmeissn](https://github.com/rmeissn/onju-voice-esphome).
The original upstream README is preserved in [./docs/UPSTREAM_README.md](./docs/UPSTREAM_README.md)
for attribution; its old architecture and hardware claims do not describe this
milestone. Original license notices are retained. See
[./DEPENDENCIES.md](./DEPENDENCIES.md) for exact SDK revisions, overlays and
third-party terms. The full USB factory image is distributed as a GitHub
prerelease asset with SHA256, not committed to Git. No stable/v1.0 release.
The factory image includes Improv Serial for Wi-Fi provisioning and OTA.
Its Wi-Fi placeholders are intentionally non-personal; provision real credentials
locally. USB installation itself has not been exercised by this publication.
