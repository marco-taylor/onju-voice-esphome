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

## Using with ESPHome

### One source, two supported update paths

**Recommended production path:** install the release factory image → provision
Wi-Fi with Improv Serial → add the device to Home Assistant → use its firmware
update entity. Updates come from GitHub
[releases/latest](https://github.com/marco-taylor/onju-voice-esphome/releases/latest),
using [the native manifest](https://github.com/marco-taylor/onju-voice-esphome/releases/latest/download/onju-voice.manifest.json).
No ESPHome container is required for these updates.

**Advanced ESPHome path:** clone this repository → optionally configure local
secrets → validate/compile in ESPHome → use native ESPHome OTA. This remains
supported for self-builders, developers, customization, debugging and recovery.
Local changes are replaced by a later generic managed update; keep using your
own builds if you need custom behavior.

**Source of truth:** [./onju-voice.yaml](./onju-voice.yaml), together with its
local components, SDK manifest/overlays, pinned models and local sound assets.
Tag **v1.2.0** contains the exact generic source used for the final 1.2.0 build.
There is no separate simplified example or independently maintained HA firmware.
The compatibility entry points [./main.yaml](./main.yaml) and
[./onju_duplex_i2s.yaml](./onju_duplex_i2s.yaml) include this same YAML; the latter
name does not enable AEC or a different audio architecture.

### Clone and validate with Docker

Release 1.2.0 was tested with **ESPHome 2026.10.2 / ESP-IDF 5.5.6**. Pin this
version rather than an evolving `stable` or `latest` container tag. The commands
below run from the repository root on a Docker host; the SDK bootstrap and first
build need Internet access and space for toolchain/registry dependencies.
Linux `--network=host` allows local-device access for upload/logs. On other Docker
platforms, use their supported networking and specify the device's reachable
address explicitly. Bind-mounted files may be owned by the container's user.

```sh
git clone https://github.com/marco-taylor/onju-voice-esphome.git
cd onju-voice-esphome
git checkout v1.2.0

docker run --rm --entrypoint python3 -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 /config/tools/bootstrap_sdk.py

docker run --rm --network=host -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 config /config/onju-voice.yaml

docker run --rm --network=host -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 compile /config/onju-voice.yaml
```

The bootstrap verifies pinned upstream archive SHA256 values and reconstructs
all 843 SDK files against the production manifest and overlays. Run it before
validation/build; its generated SDK and cache are ignored. No firmware is
installed by these commands. The resulting files are under
`./.esphome/build/onju-voice/build/`: `firmware.factory.bin` and
`firmware.ota.bin`. See [./DEPENDENCIES.md](./DEPENDENCIES.md) for exact inputs
and [./tools/prepare_managed_release.py](./tools/prepare_managed_release.py) for
release packaging from that same build.

Without Docker, use Python 3.12–3.14, install
[./requirements.txt](./requirements.txt), run `python3 ./tools/bootstrap_sdk.py`,
then `esphome config ./onju-voice.yaml` and
`esphome compile ./onju-voice.yaml`. Do not mix ESPHome versions within a build.

### Wi-Fi and local secrets

**The unmodified release YAML requires no secrets entries.** It intentionally
has no compiled Wi-Fi station, password, API key or OTA password. Provision Wi-Fi
via Improv Serial after USB installation; later generic images load native
saved Wi-Fi settings. No dummy Wi-Fi credentials are compiled into 1.2.0.

For a deliberately private self-build with compiled credentials, copy
[./secrets.example.yaml](./secrets.example.yaml) to `./secrets.yaml`, replace its
two placeholders locally, then add these fields to the **existing** `wifi:`
block in your local copy of [./onju-voice.yaml](./onju-voice.yaml):

```yaml
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  reboot_timeout: 0s
```

This is an optional local overlay of the production configuration, not another
firmware line. `./secrets.yaml` is gitignored. Never publish the resulting BIN,
expanded config output or logs containing credentials. No API/OTA secret entry
is required by the base configuration.

**Managed-update boundary:** a compiled-station build uses a different native
Wi-Fi preference key from the zero-station shared image. Merely compiling
credentials does not migrate them to the shared image. Before returning to a
generic managed image, ensure credentials exist under its Improv/native saved
Wi-Fi key, and confirm any required identity/network migration. Custom static
network settings are likewise not automatically converted into a persisted
profile. Keep a working recovery path. The generic factory build contains no
private Wi-Fi data and uses DHCP.

### Device name and identity

On a **new, unprofiled** device, the `name` and `friendly_name` substitutions at
the top of [./onju-voice.yaml](./onju-voice.yaml) set the base names. The existing
identity component appends a MAC-derived suffix. Keep
`name_add_mac_suffix: false`: this project's identity component supplies it.
For example, compile with overrides without editing the shared YAML:

```sh
docker run --rm --network=host -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 \
  -s name my-onju -s friendly_name "My Onju" compile /config/onju-voice.yaml
```

A valid existing MAC-bound identity profile takes precedence over these
substitutions. Changing them does not rename a migrated device. Unprofiled
custom base names are not automatically retained by a later generic image.
For a display-only change, use Home Assistant's device name. Do not erase NVS
or reuse another device's profile. Private per-device bootstrap configurations
are not distributed here; see [migration details](./docs/MANAGED_UPDATES.md).

### First installation, classic OTA and logs

For USB first installation/recovery, use the full
`./.esphome/build/onju-voice/build/firmware.factory.bin` from your build (or the
matching release factory asset). Flash at **0x0** with an ESP32-S3-compatible
USB flashing tool, then configure Wi-Fi through Improv Serial. Factory flashing
is not the normal update path for an existing configured device.

For an existing compatible node, replace `DEVICE_ADDRESS` with that device's
reachable hostname/IP. The commands below upload only the last compiled OTA
application, then allow log inspection; they do not compile a different image.
Always verify the intended device and identity before upload.

```sh
docker run --rm --network=host -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 upload /config/onju-voice.yaml --device DEVICE_ADDRESS

docker run --rm --network=host -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 logs /config/onju-voice.yaml --device DEVICE_ADDRESS
```

Never upload the full factory image through an OTA-only path. Native API logs
show initialization, MWW startup and errors; the existing
`touch_diag_snapshot` action provides an on-demand touch snapshot. Avoid
publishing private logs. USB serial logs additionally require mapping your
actual serial device into the container. Existing legacy/private firmware may
need a verified one-time migration before generic OTA; preserve identity,
network settings and NVS as described in the migration guide.

These CLI commands also apply to a persistent ESPHome container when the
**entire repository** is mounted at its configuration root. Keep the YAML,
local components, assets and bootstrapped SDK together. Point the dashboard at
this YAML rather than copying it alone into an unrelated configuration folder.

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

Download the factory BIN and SHA256SUMS from the matching GitHub release.
Verify SHA256, then use an ESP32-compatible USB flashing tool to write the full
factory image at **0x0** (ESP32-S3, 16-MB flash). It contains the bootloader,
partition table, OTA data and application; do not treat it as an OTA-only image.
This publication does not itself test USB recovery/first installation.

Use **Improv Serial** to provision personal Wi-Fi credentials after USB
installation. The distributed image uses generic MAC-based identity/DHCP and no
compiled Wi-Fi station. No API keys, encryption keys or personal network settings
are included. Use Home Assistant Managed Updates for routine production updates;
native ESPHome OTA remains available for self-builds. Never install the full
factory image through an OTA-only path.

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
release asset with SHA256SUMS, not committed to Git. Release 1.2.0 is a normal
production release.
The factory image includes Improv Serial for Wi-Fi provisioning and OTA.
It has no compiled Wi-Fi station; provision real credentials locally. USB installation itself has not been exercised by this publication.
