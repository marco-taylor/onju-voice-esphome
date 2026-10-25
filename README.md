# Onju Voice: Tetele ADF production milestone

ESPHome **2026.10.0** configuration for the original ESP32-S3 Onju Voice PCB.
This is a **pre-hardware-test milestone**, not a stable release. It replaces this
fork's earlier full-duplex/AEC experiment with the current Tetele ADF port.
No rmeissn audio, microphone, I2S, AEC or media-player architecture is imported
by the touch adaptation.

Touch status: **implemented / build validated, physical hardware validation pending**.
A successful build does not establish physical touch, acoustic quality or
end-to-end Home Assistant behavior. No OTA is performed by the build commands.

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

## Touch and later physical validation

| Pin | Function |
| --- | --- |
| GPIO4 | VOL−, native player −0.05; hold repeats |
| GPIO3 | Action, existing VA/player behavior |
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
- Check boot, Wi-Fi/API, ADF/microphone and both native wakeword/pipeline slots.
- Check STT, TTS/player, confirmation sound, delay and recovery after END/ERROR.
- Check VOL−, Action, VOL+ including hold and release.
- Read `touch_diag_snapshot` at idle and during touch; check both thresholds agree.
- Observe at least two minutes without resets or unintended touch events.

## Provenance and licenses

Based on [Tetele](https://github.com/tetele/onju-voice-satellite),
[gnumpi's ADF components](https://github.com/gnumpi/esphome_audio), ESPHome and
[rmeissn](https://github.com/rmeissn/onju-voice-esphome).
The original upstream README is preserved in [./docs/UPSTREAM_README.md](./docs/UPSTREAM_README.md)
for attribution; its old architecture and hardware claims do not describe this
milestone. Original license notices are retained. See
[./DEPENDENCIES.md](./DEPENDENCIES.md) for exact SDK revisions, overlays and
third-party terms. No final/stable release or firmware binaries are published.
