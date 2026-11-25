# Experimental AFE / three-model candidate — 2026-11-25

Production v1.2.0 is unchanged. The direct WN9 fallback remains at
`a972d6f8cba5f96d61024ce04134e24408f74b09`, branch `experiment/wakenet`.
This candidate is on `experiment/wakenet10-afe`, project
`1.3.0-wakenet10-afe.1`, ESPHome 2026.10.2 / IDF 5.5.6.

## Compatibility evidence

Official ESP-SR 2.6.2 commit `bb552f1a559396a17681299cb3e199a0f1a4520a`
contains all three requested model directories. Their exact eleven files match
that checkout. The official wakeword list specifies **Jarvis**, not Hey Jarvis.

The unmodified S3 AFE header defines `AFE_MAX_WAKEWORD_NUM 3`.
The native 1mic/2mic archives independently enforce that limit and return -1
for another registration. Their DWARF has three interface/model-data entries.
The generic `add_wakenet_model` resolves each name through
`esp_wn_handle_from_name`, creates its own matching interface, and increments the
model count only on success. The native single-mic fetch path iterates those
interfaces, resets cached features when the interface changes, and returns
`model_index + 1` separately from the word index. Both WN9 and WN10 interfaces
are present in the same pinned library. No family-homogeneity check, ABI alias,
conversion or SDK modification was introduced.

This establishes API/ABI/build compatibility, **not executed target inference**.
Native AFE creation, all three live handles and recognition still require the
separately authorized hardware test. The candidate fails closed unless the
third registration returns exactly 3. There is one such call and no fourth.

## Models and storage

| AFE ID | Official model | Phrase | Raw bytes |
|---|---|---|---:|
| 1 | wn10_alexa | Alexa | 1,564,918 |
| 2 | wn10_de_halloesp | Hallo ESP | 823,074 |
| 3 | wn9_jarvis_tts | Jarvis | 291,008 |

Total raw: 2,679,000 bytes. Aligned blob: 2,679,616 bytes;
SHA256 `0552c815914b694d09cb74281110aab5abf2ca3efcd8aeac6aacdcbf9a57a090`.
The actual upstream loader passes ASan/UBSan repeated load/deinit tests. It holds
file pointers into the original blob. WN10 split `_MODEL_INFO_p1/p2` deliberately
does not populate generic `_MODEL_INFO_`; this is not rejected as corruption.
Weights are mapped in application flash; vendor tensor/workspace allocation is
not inferred from blob size. No extra partition. Original partition CSV/table
are byte-identical to production. MWW/TFLite and all six baseline TFLite model
arrays are absent.

## Audio, routing and lifecycle

One existing ADF microphone source, 16-kHz s16 mono after unchanged DC/gain.
AFE input `M`, SR/LOW_COST, WakeNet ON, linear gain 1; AEC/NS/VAD/AGC/SE OFF.
No speaker reference and no additional microphone/I2S pipeline. Feed/fetch frame
sizes are obtained from the native instance and validated, not hardcoded.
Fetch returns s16 mono. No resampling stage was added.

Separate feed and fetch tasks share one AFE. No direct detector runs alongside
it. Shutdown cancels detections, drains while feeder exits, joins that task,
destroys AFE, frees configuration/model metadata, then releases the physical
microphone before the existing VA/tone handover. The existing VA processing and
VA-IDLE TTS recovery are unchanged. Existing bounded startup recovery, Mute,
Use Wake Word, timer, touch, LEDs and sounds are preserved.

The two native HA pipeline slots remain. Each of Alexa/Jarvis/Hallo ESP is
available for selection in either slot; **at most two words are assigned to
Assist at a time**. All three AFE models are resident while listening, but
unselected detections are ignored. There is no implicit third-word routing,
third pipeline or local override of HA selection. Supporting three simultaneous
Assist triggers through two slots requires a separate routing decision.

Persisted selection uses a new three-bit mask key, validates at most two enabled
bits, and migrates the previous Alexa boolean. User changes only are saved;
ESPHome Preferences batching is unchanged.

## Validation and resource limits

Config, codegen, clean compile, link: PASS. Source protection, actual-component
threaded lifecycle/ASan/UBSan, native loader/ASan/UBSan, startup, microphone Mute,
TTS barrier and timer host regressions: PASS. Vendor DSP is mocked in lifecycle
tests; these are not hardware acceptance results.

| Build | Flash bytes | Static RAM bytes |
|---|---:|---:|
| Production MWW 1.2.0 | 1,823,307 | 130,095 |
| Direct single WN9 | 1,893,083 | 142,915 |
| AFE three-model candidate | 4,569,531 | 166,955 |
| Delta vs production | +2,746,224 | +36,860 |
| Delta vs single WN9 | +2,676,448 | +24,040 |

Application file: 4,569,648 bytes; SHA256
`31c1000e66a5572a1d0fe289bad03ae130856f0091ef2d0edf548ccdd8adbc51`.
Factory and OTA application bytes agree. Native app slot is 8,126,464 bytes.
There is one current ESP-SR component and no new unresolved symbol or legacy SR
library path. Baseline driver/deprecated-I2S and unused SPIFFS loader warnings
remain; they do not establish runtime safety.

Static DRAM accounting leaves 174,805 bytes of the reported 341,760-byte region;
this is **not measured runtime free heap**. AFE/three-model heap, largest block,
PSRAM and initialization peaks remain unmeasured. Vendor benchmarks use different
models/modes and cannot provide a reliable numeric peak for this combination.
The 2.68-MB mapped blob is not itself a 2.68-MB PSRAM allocation.

The candidate requires before initialization >=128 KiB internal free,
>=64 KiB largest block, >=4 MiB free PSRAM; after native creation, >=96 KiB
internal, >=48 KiB largest, >=2 MiB PSRAM. These are conservative fail-closed
policy gates, not measured peaks or guarantees against vendor allocator failure.
Task stacks are internal (8 KiB fetch + 4 KiB feed); PCM ring is 16 KiB with the
existing allocator preference. No resource value from the old WN9 hardware run
is claimed as a measurement of this candidate.

A first controlled hardware test can evaluate initialization and actual
reserves, then PCM/feed/fetch, IDs, both selected pipeline mappings, Mute/OFF,
VA/TTS recovery and repeated physical cold boots. Three simultaneous native
models have not yet run on a device. No OTA/reboot is authorized by this build
report. No performance or recognition-quality improvement is claimed.
