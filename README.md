# Onju Voice: Tetele ADF production milestone

ESPHome **2026.10.0** configuration for the original ESP32-S3 Onju Voice PCB.
This is a **timer-safety development milestone**, not a stable release. It replaces this
fork's earlier full-duplex/AEC experiment with the current Tetele ADF port.
No rmeissn audio, microphone, I2S, AEC or media-player architecture is imported
by the touch adaptation.

**BUILD VALIDATED:** ESPHome Config PASS, Codegen PASS, Clean Build PASS.

**BOOT / HARDWARE INITIALIZATION VALIDATED:** the production Timer-Safety build
was installed successfully. Boot without bootloop, Wi-Fi/Home Assistant API,
8 MB PSRAM, ADF/microphone RUNNING and MWW DETECTING_WAKE_WORD were observed.
Voice Assistant, media player, timer and GPIO4/3/2 touch initialized; both native
pipeline/wakeword slot pairs and all three model definitions were present.
Passive stability: **125 seconds PASS**, without critical or repeated audio errors.

**FUNCTIONAL HARDWARE TESTS PENDING:** timer countdown, alarm/repetition,
Center-touch dismissal, the real-time 15-minute timeout, recovery from a real
stuck player, dynamic touch operation, both pipeline routes and acoustic
recognition of all three wakewords. Initialization does not establish these
functions or audio quality. No OTA is performed by the build commands.

## Architecture

- Local Tetele-derived ADF components and all 16 required ADF SDK components.
- ADF microphone and player paths at **16 kHz**, LEFT channel, 32-bit I2S data/slots.
- Integer DC correction before runtime microphone gain and clipping.
- Runtime microphone gain, wakeword sensitivity and existing cutoff settings.
- Three pinned models: **Okay Nabu**, **Hey Jarvis**, **Hey Mycroft**, plus VAD.
- **Two native pipeline/wakeword slots**, managed by the Home Assistant voice
  assistant protocol. Choose distinct wakewords to address the two slots.
- MWW → VA handover waits for MWW teardown and microphone release, rechecks
  ownership, and retains END/ERROR recovery.
- Local flash-resident wakeword confirmation sound and configurable Assist
  start delay; Wake Word Listening Light and existing LED behavior.
- Native ADF media-player volume; no additional volume Number entity.
- Dynamic S3 touch calibration, adapted from rmeissn commit
  `09b3b65c237e8dc42c40677492965865429fe12e` to ESPHome 2026.10.0 / IDF 5.5.6.
- Native Voice Assistant timers: proportional LED countdown, optional **Timer LED**
  switch (default ON), repeated local flash MP3 alarm and Center-touch dismissal.
- No old PCM/raw capture probes or audio diagnostic buffers.

The microphone source ID `mww_probe_source` is retained for compatibility; it
is the functional microphone source, not an audio capture probe.

## Build the milestone

Use Python 3.12–3.14 and the pinned ESPHome 2026.10.0 environment
for compilation. ESPHome 2026.10.0 selects ESP-IDF 5.5.6. The native ESP-IDF
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
DC/gain, MWW models, native slots and handover/recovery logic remain unchanged.

A ringing session is limited to **15 minutes**, including time waiting for the
player. Additional expired timers do not extend that session. The timeout uses
the same central `dismiss()` cleanup as manual dismissal; a new session starts
a fresh deadline. Cleanup waits at most **10 seconds** for player IDLE, then
logs one WARN and continues the existing recovery if no active VA owns it.
The existing recovery retains its own bounded waits and ownership guards.
No persistent media-player repeat mode or additional stop wakeword is used.

Timer behavior follows the principle from
[Idskov/onju-voice-esphome](https://github.com/Idskov/onju-voice-esphome/tree/6b1809d780e0c741a5ef7b1b79b2ccbfc73e8f6f),
adapted to our existing architecture. Physical validation is pending.

## Touch and later physical validation

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

Physical test checklist (pending):

- Install only a separately approved OTA build; boot without touching the pads.
- Boot/initialization and 125-second idle stability passed; test both native
  wakeword/pipeline routes functionally.
- Check STT, TTS/player, confirmation sound, delay and recovery after END/ERROR.
- Check VOL−, Action, VOL+ including hold and release.
- Read `touch_diag_snapshot` at idle and during touch; check both thresholds agree.
- Test timer start/update/pause/resume/cancel, two timers, countdown toggle,
  local alarm repetition, Center-touch dismiss and HA STOP during sound/gaps.
- Check the 15-minute safety deadline and player-IDLE timeout under a controlled
  fault; recheck voice/player recovery and at least two minutes of stability.

## Provenance and licenses

Based on [Tetele](https://github.com/tetele/onju-voice-satellite),
[gnumpi's ADF components](https://github.com/gnumpi/esphome_audio), ESPHome and
[rmeissn](https://github.com/rmeissn/onju-voice-esphome).
The original upstream README is preserved in [./docs/UPSTREAM_README.md](./docs/UPSTREAM_README.md)
for attribution; its old architecture and hardware claims do not describe this
milestone. Original license notices are retained. See
[./DEPENDENCIES.md](./DEPENDENCIES.md) for exact SDK revisions, overlays and
third-party terms. No final/stable release or firmware binaries are published.
