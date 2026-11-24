# Onju Voice WakeNet single-engine experiment

**Local experiment, not production firmware. Do not flash without separate test
approval.** This branch replaces microWakeWord; it does not implement a dual
engine, an engine selector or runtime engine switching.

Base: production **v1.2.0**, commit
`133cd1024a7a53551fb4367be7ed44216d9c7b2e`. Production main, releases, assets,
GitHub latest and manifests remain unchanged. Experimental project version:
**1.3.0-wakenet.1**.

Phase 1 proves a native clean build/link of the existing Onju ADF/I2S/VA stack
with one consistent ESP-SR generation and an in-Application Alexa model.
No device has run this experiment. Wakeword recognition, actual model allocation,
VA/TTS handover and cold-boot behavior still need controlled hardware testing.

## Architecture

- ESPHome **2026.10.2**, ESP-IDF **5.5.6**, ESP32-S3 / 16 MB flash / 8 MB PSRAM.
- Existing 16-kHz, 32-bit LEFT I2S input, ADF microphone, integer DC correction,
  runtime gain and 16-bit mono microphone callbacks; no second hardware reader.
- Only ESP-SR **2.6.2** at `bb552f1a559396a17681299cb3e199a0f1a4520a` enters
  the dependency graph. Its current WakeNet9-family model `wn9_alexa` identifies
  itself as **wakenet9l_v4h8_Alexa_3_0.640_0.650**. Official default thresholds
  are retained. This is not a claim that the older WakeNet9 benchmark describes
  this exact model.
- A 291,056-byte, 16-byte-aligned blob lives in flash `.flash.rodata`.
  Native `srmodel_load()` parses it; no model partition is needed. The loader
  points into the blob instead of copying all weights. Vendor detector workspace
  and initialization peaks remain hardware measurements.
- Dedicated bounded inference task and PCM ring; existing VA/tone/recovery path.
  Mute and Use Wake Word gates, bounded local startup checks and OTA stop/recovery
  hooks. Only Alexa is advertised to the two native HA pipeline slots. No third
  slot, no additional VA, no MWW models or MWW sensitivity entity.
- No active AFE/AEC/VAD/NS stage. Duplex I2S is not AEC.
- Existing timer, touch, LEDs and local sounds are retained. These are build/host
  checks, not new hardware acceptance.
- Native ESPHome OTA and HTTP OTA backends remain compiled; the production
  update-feed entity is deliberately absent. No experimental manifest or release.

The legacy `recorder_sr.c` and `algorithm_stream.c` AFE wrappers are excluded by
**two CMake-only overlays**, because they expect the obsolete AFE handle. They
are not used by the Onju audio/VA path. All active microphone/player/I2S source
files and the VA processing code remain unchanged. No fake symbols or ABI aliases.
The original pinned ADF SDK is reconstructed unchanged; filtered component copies
are generated under the ignored SDK directory.

## Reproduce the build

The source of truth on this branch is [./onju-voice.yaml](./onju-voice.yaml).
Use an isolated checkout and the pinned container. The entire SDK, cache and
build output are ignored; no private credentials or device bootstrap are needed.
Wi-Fi uses the unchanged generic Improv/saved-profile mechanism.

```sh
docker run --rm --entrypoint python3 -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 /config/tools/bootstrap_sdk.py

docker run --rm --entrypoint python3 -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 /config/tools/bootstrap_wakenet.py

docker run --rm -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 config /config/onju-voice.yaml

docker run --rm -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 compile --only-generate /config/onju-voice.yaml

docker run --rm -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 clean /config/onju-voice.yaml

docker run --rm -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 compile /config/onju-voice.yaml
```

The WakeNet bootstrap fetches the exact official ESP-SR Git commit, checks all
three model-file hashes and packs a single aligned Alexa model. ESP-DL 3.3.13,
dl_fft 0.8.0, cjson 1.7.19~2 and esp_new_jpeg 1.0.2 are explicitly pinned.
The resolved dependency lock and build evidence are recorded with the experiment.
No upload/run/flash command is part of this procedure. The default local build
output is under `./.esphome/build/onju-voice/build/`; the investigation uses a
separate `ESPHOME_BUILD_PATH` to avoid touching any other build.

## Host tests

After bootstrapping, these commands compile the actual lifecycle code with
mocked hardware/DSP and test the actual official model-blob loader with ASan/UBSan:

```sh
docker run --rm --entrypoint python3 -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 /config/tools/test_wakenet_lifecycle.py

docker run --rm --entrypoint python3 -v "$PWD":/config \
  ghcr.io/esphome/esphome:2026.10.2 /config/tools/test_wakenet_blob.py
```

Results go to `./.cache/wakenet-tests/`. No S3 inference time or acoustic quality
is inferred from host execution. Existing startup, microphone-mute, TTS-race and
timer tests were also exercised against the experiment; details and limitations
are in [the single-engine report](./docs/experiments/wakenet/SINGLE_ENGINE.md).

The earlier [dual-engine feasibility report](./docs/experiments/wakenet/BERICHT.md)
and its checker are historical evidence for the abandoned design. Their
“runtime unchanged from 1.2.0” assertion intentionally does not apply to this
single-engine replacement. They are not silently made green or used as current
regression results.

## Licensing

[ESP-SR's Espressif MIT license](https://github.com/espressif/esp-sr/blob/bb552f1a559396a17681299cb3e199a0f1a4520a/LICENSE)
limits its grant to Espressif products and requires notice retention. Wakeword
trademark rights are separate; no blanket commercial Alexa-product authorization
is implied. Models/libraries are downloaded from the official source and are not
committed here. Existing ADF/ESPHome notices and Voice-PE sound attribution under
[./DEPENDENCIES.md](./DEPENDENCIES.md) and the asset notices remain applicable.

No publication, productive update source, device OTA, USB flash or reboot is
performed by this experiment. Runtime acceptance requires separate permission.
