# Experimental Onju — two WakeNet10 models / AFE, 2026-11-25

This candidate supersedes the three-model experiment. Production v1.2.0 and the
working direct WN9 fallback remain unchanged. No device has run this candidate.

Base: production v1.2.0 at 133cd1024a7a53551fb4367be7ed44216d9c7b2e, through
WN9 fallback a972d6f8cba5f96d61024ce04134e24408f74b09 and three-model checkpoint
8553c6800fa027412314833d7f4c07536cc29cd7. Branch experiment/wakenet10-afe-two;
source of truth ./onju-voice.yaml; project 1.3.0-wakenet10-afe.2.
ESPHome 2026.10.2 / ESP-IDF 5.5.6.

## Models and routing

ESP-SR 2.6.2, pinned official development commit
bb552f1a559396a17681299cb3e199a0f1a4520a; no SDK/library patch.
Exactly two models, both WakeNet10:

| AFE ID | Model | Phrase | Intended native HA pipeline slot | Raw bytes |
|---|---|---|---|---:|
| 1 | wn10_alexa | Alexa | 1 | 1,564,918 |
| 2 | wn10_de_halloesp | Hallo ESP | 2 | 823,074 |

The native HA catalog has exactly these two entries in this order and retains
max_active_wake_words=2. AFE IDs return the matching phrase to the unchanged
VA-start path; HA owns the actual pipeline IDs/assignments. The requested
Alexa/slot-1 and Hallo-ESP/slot-2 pairing must be present in HA during the later
hardware test. No live HA setting was read or changed in this build-only task,
and catalog ordering is not claimed to overwrite a user's HA assignments.
Both words can trigger Assist when selected. There is no third routing layer.

Jarvis, its third registration and its catalog/detection ID are removed. Exactly
the two native configuration slots are used. No add_wakenet_model() call exists
in the consumer. The public reset-to-default threshold API checks both populated
slots before claiming readiness; a partial native initialization fails closed.
It retains the freshly loaded official defaults and introduces no application
cutoffs. The native implementation was inspected: missing slot returns -1,
valid slot restores its initial defaults and returns 1.

The persistent two-bit selection has a new key and migrates the previous mask
by preserving its remaining bits (discarding Jarvis), or the previous Alexa
boolean. Fresh devices default to both words; intentionally disabled selections
remain disabled. Use Wake Word and Mute preferences are untouched. Saving occurs
only for actual changes through the existing Preferences batching.

## AFE and preserved behavior

One existing 16-kHz / 32-bit LEFT I2S → ADF → DC correction → runtime gain →
signed16 mono microphone source feeds one AFE, format M, AFE_TYPE_SR / LOW_COST.
WakeNet ON; VAD/NS/AEC/AGC/SE OFF. No playback reference, no new processing model,
no resampling, no second microphone or direct detector. Feed/fetch frame sizes
are queried and validated; fetch is mono s16/16 kHz.

Existing bounded local startup/recovery, OFF/Mute gates, feed/fetch task teardown,
physical microphone release before VA, wake tone, VA-IDLE TTS barrier, timer,
touch, LEDs and sounds remain. Sparing diagnostics preserve DC, raw/AC RMS,
peak, clipping, PCM/feed/fetch counters, detections and model ID. First-second
then ten-second aggregates; no raw capture. Fetch timing includes waiting and
must not be reported as isolated inference time.

## What remains of WN9

No WN9 model weights, model metadata, model initialization or direct WN9 adapter
are embedded/used. The exact old wn9_alexa, wn9_jarvis_tts and wn9_mycroft_tts
weight data are absent from the final Application. microWakeWord/TFLite and the
six baseline TFLite arrays are also absent.

**The executable is not WN9-code-free.** The official AFE calls the generic
esp_wn_handle_from_name() in the single prebuilt libwakenet.a. Its unchanged
selector references WN9/WN9l/WN9s/WN10 interfaces unconditionally. The final link
map retains these WN9-family members:

| Member | Accounted flash bytes |
|---|---:|
| wakenet9_quantized.c.obj | 6,147 |
| wakenet9l_quantized.c.obj | 6,649 |
| wakenet9s_quantized_mc.c.obj | 6,061 |
| Total WN9-family kernel/interface code | 18,857 |

These are generic inference kernels/interface tables, not embedded WN9 models or
live WN9 detectors. There is no separate WN9-only CMake library target that can
simply be removed: removing libwakenet.a would also remove WakeNet10. No supported
per-generation trimming switch exists in this pinned prebuilt integration.
Removing those references would require a vendor selector/archive modification
or a different upstream binary, outside this reduction. No linker stubs,
wrappers, symbol aliases or archive surgery were introduced. The active engine
and both runtime model instances are exclusively WakeNet10.

Official dependency registration:
https://github.com/espressif/esp-sr/blob/bb552f1a559396a17681299cb3e199a0f1a4520a/CMakeLists.txt
Local library/CMake bytes match the clean pinned official checkout.

## Build and host validation

Config PASS; Codegen PASS; CLEAN BUILD PASS; Link PASS; Host tests PASS.

- Actual consumer, threaded RTOS/AFE mocks, ASan/UBSan: both IDs emit their exact
  phrases; invalid/removed IDs rejected; no third registration; selection
  persistence and migration; Mute/OFF; late cancellation; task teardown; OTA
  gating; partial model initialization and memory/format failure cleanup.
- Actual official blob loader with ASan/UBSan, repeated load/deinit: exactly two
  WN10 directories/eight files, bounds/alignment, pointers into original blob.
  Split WN10 metadata is handled correctly. Vendor Xtensa DSP is not executed.
- Existing startup, actual microphone Mute, TTS VA-IDLE barrier and timer host
  regression tests PASS. Protected active ADF/I2S/Mic/DC/Gain, VA processing,
  startup, timer, touch and sound sources are unchanged outside the model catalog.
- One ESP-SR generation, no ABI conflicts or duplicate targets, no new unresolved
  symbols. Production partition table and CSV byte-identical. No model partition.
  Factory Application equals the final OTA/Application bytes.

## Resources

| Build | Flash bytes | Static RAM bytes |
|---|---:|---:|
| A — production MWW 1.2.0 | 1,823,307 | 130,095 |
| B — direct WN9 Alexa | 1,893,083 | 142,915 |
| C — three-model AFE | 4,569,531 | 166,955 |
| D — two-model WN10 AFE | 4278327 | 166955 |
| D minus A | +2455020 | +36860 |
| D minus B | +2385244 | +24040 |
| D minus C | -291204 | 0 |

Raw models total 2,387,992 bytes; aligned Application blob 2,388,432 bytes
(440 bytes table/alignment). Blob SHA256:
8629e6934d6de5fb6d667beb9fa3f15f0b2695161731030b27a28c3a5404a13d.
Application file 4278448 bytes, SHA256 8bfcd73f957a5415eba58251f48b1d1b9289e027b3fb0265451239b76aaf3937.
Existing app slot 8,126,464 bytes; no partition change.

**Why B → C grew:** +2,676,448 bytes total = +2,388,560 bytes packed model data
(89.2%) +287,888 other bytes. The WN10 models are much larger than old wn9_alexa;
AFE adds frontend/shared DSP/NN paths and some static buffers even for disabled
algorithms because of generic factory/interface references. B's ELF already
contained the WN10 interface through the same selector, so the entire difference
must not be attributed to a new WN10 kernel. B has no retained AFE factory; C/D do.

**What Jarvis removal saves:** 291204 bytes total: 291,184 bytes removed
blob data (291,008 raw +176 table/alignment), with -20 bytes
net remaining metadata/code/alignment difference. WN9 kernel code did not vanish;
its 18,857 bytes remain reachable from the vendor selector. Static RAM is unchanged;
no runtime heap/PSRAM saving is fabricated from that static result.

Major real ELF payload sections (sum exactly 4278327 bytes):

| Section | Bytes |
|---|---:|
| .flash.rodata (including 2,388,432-byte blob) | 2,793,768 |
| .flash.text | 1,365,812 |
| .iram0.text + .iram0.vectors | 90,155 |
| .dram0.data | 28,304 |
| .flash.appdesc | 256 |
| .rtc.force_slow | 32 |

.dram0.bss is 64,720 bytes of runtime zeroed memory, not extra file payload.
NOLOAD dummy sections represent linker/MMU/bus address spans and must not be
added as model allocations or flash payload. In particular the 4,194,272-byte
.ext_ram.dummy is not a measured 4-MiB PSRAM allocation. Debug sections in the ELF
also are not the flash image size.

Native esp_idf_size archive attribution (overlaps the sections above, do NOT add
again): ESP-SR/DL/frontend related archives total 526,142 flash-accounted bytes,
41,730 static RAM bytes. Direct AFE archive 15,647 flash /1 static byte;
libwakenet 27,614 flash /0 static; esp_audio_processor 86,099/4,916;
dl_lib 179,906/7,737; esp-dl 152,271/10,008. Generic NS/VAD code may be linked
without those algorithms being enabled; libnsnet3 alone accounts for 19,048
static bytes. These are included totals, not all new costs versus B.

Runtime internal heap, minimum/largest block, PSRAM, AFE/model initialization
peak, inference CPU/time and VA/TTS peaks: UNMEASURED, no device action permitted.
Existing conservative guards remain >=128-KiB internal/64-KiB largest/4-MiB PSRAM
before init, >=96-KiB/48-KiB/2-MiB after init. They are policy gates, not measured
reserves or proof against vendor allocation failure. Runtime validation follows
only after separate hardware authorization.

## Decision

Safe to hardware-test: YES, for a controlled initial hardware/resource test;
not hardware acceptance and not production release approval. No unresolved third
wakeword routing remains. Actual native HA slot assignment must be checked at
that test, since HA owns it. Retained vendor WN9 kernel code is explicitly known;
no WN9 model inference occurs. No acoustic-quality/performance improvement claimed.

Next authorized step would be: only kitchen after explicit permission, verify
both model slots and heap reserves, PCM/feed/fetch/IDs, configure/check native
Alexa slot 1 and Hallo ESP slot 2, test each Assist/STT/TTS path, Mute/OFF/recovery,
and repeated real cold boots. Do not mark physical tests passed from host results.

Kitchen changed NO; living room changed NO; OTA NO; device reboot NO.
main/production release/latest/manifest/assets unchanged. No remote push or tag.
Working WN9 fallback remains at its original commit; three-model checkpoint also
remains preserved. Stop pending explicit hardware permission.
