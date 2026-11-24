# WakeNet Machbarkeit für Onju Voice 1.2.0

Stand: 2026-11-24. **Noch keine Dual-Engine-Firmware implementiert; nicht für einen Gerätetest freigegeben.** Der lokale Branch experiment/wakenet basiert exakt auf v1.2.0, Commit 133cd1024a7a53551fb4367be7ed44216d9c7b2e. Runtime-YAML, Komponenten, SDK-Manifest, Modelle, Sounds und produktive Einstellungen wurden nicht verändert. Hinzu kommen nur dieser Bericht und ein reproduzierbarer Host-Prüfer.

WakeNet ist auf ESP32-S3 grundsätzlich möglich. Eine direkte Addition der untersuchten externen Komponente ist für diese Basis jedoch keine saubere Integration. Vor HA-Select und Engine-Start müssen Modellbereitstellung und die Verwendung einer konsistenten ESP-SR-Generation gelöst sein. Die nachgewiesenen Konflikte sind keine Behauptung, Dual-Engine sei generell unmöglich. Es wurden keine Behelfslösungen mit zweitem Mikrofontreiber, blindem Bibliotheksersatz oder neuer produktiver Partitionstabelle eingebaut.

## Quellen und Versionen

- Release-Basis: [v1.2.0](https://github.com/marco-taylor/onju-voice-esphome/tree/v1.2.0), ESPHome 2026.10.2 / ESP-IDF 5.5.6.
- Aktuelles offizielles [ESP-SR](https://github.com/espressif/esp-sr/blob/bb552f1a559396a17681299cb3e199a0f1a4520a/idf_component.yml): master bb552f1a559396a17681299cb3e199a0f1a4520a, Versionsangabe **2.6.2**. Master wurde auf diesen Commit eingefroren; nicht als stabilen Registry-Release ausgeben. Die Registry führt u.a. [2.6.1](https://components.espressif.com/components/espressif/esp-sr/versions/2.6.1/readme).
- SDK aus 1.2.0: ESP-SR 0c1eecaac259af95f76723b61d4e16cef5904fc7, eingebunden durch den ADF-Komponentensatz. Keine automatische Aktualisierung.
- ESP-SR 2.6.2 verlangt IDF >=5.0, esp-dl **3.3.13**, dl_fft >=0.6.0 und cjson ^1.7.19; der Zielchipfilter für esp-dsp 1.8.0 schließt S3 bei dieser zusätzlichen Abhängigkeit aus. IDF 5.5.6 erfüllt die deklarierte Untergrenze; daraus folgt noch keine ADF-/Link-/Laufzeitkompatibilität.
- Untersuchte [externe Komponente](https://github.com/patrick3399/esphome_components/tree/5a44c9f1764260978440e0548df94f2536a119f9/components/esp_sr_wake_word): Commit 5a44c9f1764260978440e0548df94f2536a119f9, **nicht offiziell von ESPHome/Espressif**, pinnt ESP-SR **2.4.4**, verwendet MicrophoneSource und eine eigene Inferenz-Task. Kein WakeNet10-Nachweis durch diesen Pin. Sie fordert eine separat geflashte model-Partition; ihr Beispiel mit 6 MB ist keine Onju-Anforderung.
- ESPHome 2026.10.2 wurde per gepinntem Container geprüft. Die vorhandene laufende Dashboard-Installation meldet inzwischen 2026.11.0; sie wurde nicht verändert und nicht zum Bauen/Validieren dieser Basis verwendet. In der geprüften nativen ESPHome-Installation ist keine offizielle WakeNet-Komponente vorhanden.

## Generationenvergleich

| Kriterium | WakeNet9-Familie | WakeNet9s | WakeNet10 |
|---|---|---|---|
| ESP32-S3 | offiziell unterstützt | primär Kostenvariante für C3/C5/C6 ohne SIMD/PSRAM; konkrete S3-Alexa-API nicht verifiziert | offiziell unterstützt |
| Offizielles Alexa-Modell | ja, aktueller Ordner wn9_alexa beschreibt laut Metadaten **9l** | Ordner wn9s_alexa vorhanden, Zielkompatibilität separat nachweisen | wn10_alexa, zwei Datenteile |
| Bibliotheksnähe zu 1.2.0 | 9er-API bereits im alten SDK enthalten, aber alte/neue APIs nicht mischen | kein sauberer Drop-in-Nachweis | neue ESP-SR-/esp-dl-Abhängigkeiten |
| Modell-Flashdaten, exakt recherchierter Stand | 290.873 Byte | 290.873 Byte | 1.564.918 Byte |
| Offizielle S3-Ressourcenbeispiele | 16 KB intern / 324 KB PSRAM / 3,0 ms bei 2 Kanälen; 20 KB / 347 KB / 4,3 ms bei 3 Kanälen | kein vergleichbares S3-Alexa-Benchmark belegt | 17 KB intern / 523 KB PSRAM / 7,1 ms, 3 Kanäle |
| CPU-Beispiel | ca. 9,4% bzw. 13,4% einer CPU aus 3,0/32 bzw. 4,3/32 abgeleitet | unbekannt für Onju | Quelle nennt 22,6% einer CPU, DET_MODE_3CH_90 |
| AFE/AEC | direkte detect()-API ohne AFE möglich; AEC optional vorgelagert | entsprechend nur mit verifiziertem Ziel/API | direkte detect()-API vorhanden; AFE nicht zwingend |
| VAD | kein zusätzlicher VAD zwingend nötig für direkte WakeNet-Inferenz | ebenso keine Pflicht aus dem Wrapper abgeleitet | ebenso; vorhandenen MWW-VAD nicht als vorgeschalteten Pflichtpfad übernehmen |
| Modellqualität | Onju nicht gemessen; 9l nicht mit 9-Benchmark gleichsetzen | keine Onju-Messung | neuere Generation und andere Modellstruktur belegen keinen Onju-Vorteil |
| Integration/Stabilität | geringerer erster Ressourcenansatz; Modellversorgung fehlt trotzdem | kein Vorteil belegt, daher nicht erste Wahl | größere Modellversorgung und neuer SDK-Unterbau |
| Lizenz | Espressif-MIT, Espressif-Hardware-Bindung, einzelne Drittanbieterhinweise beachten | gleiches Repository | gleiches Repository plus weitere Abhängigkeiten |

Quelle der Herstellerwerte: [S3-Benchmark](https://docs.espressif.com/projects/esp-sr/en/latest/esp32s3/benchmark/README.html), zusätzlich lokal auf dem untersuchten ESP-SR-Commit. Das sind keine Onju-Messungen und kein direkt fairer 9-vs-10-Qualitätstest: Kanäle/Modellstände sind verschieden. Benchmark-Frame: 32 ms; die allgemeine WakeNet-Dokumentation nennt 30-ms-MFCC-Fenster. Später immer get_samp_chunksize(), get_channel_num() und get_samp_rate() der tatsächlich erzeugten Instanz auswerten, nicht einen Wert fest verdrahten. Eingabe für direkte Verwendung ist 16-kHz signed-16-bit PCM, nicht das rohe 32-bit-I²S-Format.

**Erste Wahl:** 9er-Familie als kleinerer Integrations-/Speicher-Versuch, nachdem Modellversorgung geklärt ist. Für ein konkretes Alexa-Binary zusätzlich die 9l-Metadaten berücksichtigen; keine 9er-Leistungszahlen als Messung dieser Datei übernehmen. WakeNet10 bleibt sinnvoller zweiter Kandidat, falls ein konsistenter aktueller SDK-Unterbau ohne ADF-Regression und der größere Modell-/PSRAM-Bedarf nachgewiesen werden. Keine Behauptung, 9 erkenne besser oder 10 sei auf S3 ungeeignet.

## Offizielle Modelle und Lizenz

| Modellordner | Originaldateien gesamt, Byte | Modellmetadaten |
|---|---:|---|
| wn9_alexa | 290.873 | wakenet9l_v4h8_Alexa_3_0.640_0.650 |
| wn9s_alexa | 290.873 | wakenet9s_v4h8_Alexa_3_0.640_0.650 |
| wn10_alexa | 1.564.918 | wakenet10_tts4h12q16p1_alexa_3_0.6_0.609; wakenet10_tts4h12q16p2_alexa_3_0.6009_0.6096 |
| wn9_jarvis_tts | 291.008 | wakenet9l_tts1h8_Jarvis_3_0.627_0.632 |
| wn9_mycroft_tts | 290.877 | wakenet9l_tts1h8_Mycroft_3_0.625_0.629 |

Alle Dateien einzeln mit Größe und SHA256 erfasst in diagnostics/wakenet-20261124/feasibility.json. Das ist die Summe der Modelldateien einschließlich Metadaten/Index, nicht die Größe eines fertigen Pack-Images oder einer Firmware. wn9_alexa und wn9s_alexa haben in diesem Commit denselben wn9_data-SHA256; ihre Metadaten sind verschieden. Nicht als zwei unabhängig gemessene Modelle behandeln. Der alte, vorhandene wn9_alexa-Datensatz beschreibt wakenet9l_v3h24_alexa; aktuelle Datei beschreibt v4h8. Ein Versionsvergleich muss deshalb Modellhash UND SDK festhalten.

Alexa, Jarvis und Mycroft sind englische Wakewords; Jarvis/Mycroft stammen laut Modellnamen aus der TTS-Modellfamilie. **Jarvis** ist nicht automatisch die bestehende MWW-Phrase **Hey Jarvis**, und Mycroft nicht automatisch Hey Mycroft. Keine Ersetzung derselben Wörter vortäuschen. Nabu und Hey Home Assistant stehen nicht im vollständigen offiziellen Modellverzeichnis dieses Commits. Keine Community-Modelle übernommen.

[ESP-SR-Lizenz](https://github.com/espressif/esp-sr/blob/bb552f1a559396a17681299cb3e199a0f1a4520a/LICENSE): Espressif-MIT erlaubt Nutzung/Weitergabe auf Espressif-Produkten mit Erhalt des Copyright-/Lizenzhinweises. Das ist keine unbeschränkte Standard-MIT-Freigabe für beliebige Hardware. Header/Abhängigkeiten können eigene Apache-/Drittanbieterhinweise tragen. Keine gesonderte LICENSE-Datei in den untersuchten einzelnen Modellordnern gefunden. Die [offizielle README](https://github.com/espressif/esp-sr/blob/bb552f1a559396a17681299cb3e199a0f1a4520a/README.md) weist zusätzlich auf fremde Wakeword-Marken und nötige Berechtigung bei kommerzieller Nutzung hin. Technische Binärweitergabe auf ESP32-S3 ist nach den Repository-Bedingungen grundsätzlich vorgesehen; keine pauschale Freigabe beliebiger kommerzieller Alexa-Produkte abgeleitet. In diesem Auftrag werden keine Modelle/Binaries öffentlich verteilt.

## Konkrete Integrationshürden

1. **Kollisionen bei paralleler SDK-Einbindung:** Altes ESP-SR-CMake und aktuelles ESP-SR definieren dieselben Targets esp_audio_front_end, esp_audio_processor, hufzip, multinet, wakenet. Die untersuchte externe Komponente zusätzlich zur bestehenden ADF-Liste einzutragen ist kein kompatibler Buildweg. Darüber hinaus besitzen die Bibliotheken gleichnamige globale WakeNet-Symbole. Bloßes Umbenennen der CMake-Targets gewährleistet keine ABI-Trennung.
2. **ABI-Abweichung:** Alter esp_wn_iface_t hat 14 Funktionspointerfelder, neuer 17; reset_det_threshold wird vor get_det_threshold eingefügt, weitere MFCC-Felder kommen hinzu. Alter Header plus neue Bibliothek oder umgekehrt wäre gefährlich. Auch srmodel_list_t hat unterschiedliche Felder. Beide Generationen dürfen nicht gegeneinander aufgelöst werden.
3. **Modellversorgung:** Das bestehende alte SDK lädt S3-Modelle über SPIFFS/SD-Pfade und bietet nicht das neue srmodel_load(const void*) zum Laden eines eingebetteten Blob-Images. Die externe Komponente ruft esp_srmodel_init("model") auf. Ein bloßer Alexa-Modellname genügt nicht.
4. **Partitionstabelle:** 1.2.0 hat otadata 0x9000, phy_init 0xB000, app0 0x10000 mit 0x7C0000 Byte, app1 0x7D0000 mit 0x7C0000 Byte, nvs 0xF90000 mit 0x70000 Byte. Ende exakt **0x1000000**. Keine model-Partition, kein freier Anhängeplatz. Die Bibliothekskonfiguration enthält zwar USE_AFE/USE_WAKENET und einen Standard-Hilexin-Eintrag, aber kein erzeugter/geladener Modell-Datenbereich und keine aktive WakeNet-Instanz im Onju-Laufzeitcode. Kconfig ist kein Laufzeitnachweis.
5. **Updateweg:** Eine neue Modellpartition würde Verkleinerung/Umlagerung und eine separat geprüfte Partition-/Modellmigration erfordern. Das vorhandene generische Application-OTA transportiert eine solche zusätzliche Partition nicht automatisch. Eine solche Änderung wurde nicht vorgenommen. Modell plus Code im selben App-Image ist die bevorzugte Richtung; das neue SDK besitzt die relevante Blob-API, muss dafür jedoch als **einzige konsistente** SR-Generation mit dem alten ADF-Unterbau kompatibel gemacht und gebaut werden. Dieser Übergang ist noch nicht nachgewiesen.
6. **Native HA-Slots:** get_configuration()/on_set_configuration() in der lokalen VoiceAssistant-Komponente binden Katalog und Auswahl unmittelbar an microWakeWord-Modelle. Ein zusätzlicher Template-Select würde weder den Katalog filtern noch Slot-/Pipeline-Zuordnung lösen. Es fehlt ein enginebewusster Adapter, der für MWW exakt den alten Pfad behält. Ein ausgewähltes WakeNet ohne funktionierende Modell-/Routing-Anbindung wäre irreführend; deshalb kein Select veröffentlicht/implementiert.

Diese Befunde verhindern eine saubere direkte Übernahme. Sie ersetzen keinen generellen Unmöglichkeitsnachweis und keine Arbeit an einem späteren Embedded-Model-/SDK-Prototyp. Ein blindes ADF-/SR-Upgrade nur um den Select bauen zu können würde den geforderten Schutz der 1.2.0-Referenz unterlaufen.

## Audiobesitz und spätere Umschaltarchitektur

Der tatsächliche Pfad ist I²S mono LEFT 16 kHz/32 bit → bestehender ADF-PCMSink → Integer-DC-Korrektur → Laufzeit-Gain/Clamping → 16-bit-Mono-Bytevector → MicrophoneSource gain_factor 1 → MWW-Featurebildung und MWW/VAD. MicrophoneSource führt keine Sample-Rate-Konvertierung aus. ADFMicrophone bedient höchstens vier begrenzte Chunks je Loop. MWW nutzt einen 120-ms-Ringpuffer und besitzt Start/Stop seines MicrophoneSource. Der MWW-Task beendet sich vor Freigabe; Modelle/VAD, Puffer und Task-Ressourcen werden beim Stop abgebaut.

**Kein aktives AEC, NS, AGC für den Mikrofonpfad und kein ESP-SR-AFE.** Duplex-I²S/gleichzeitige Hardware-RX/TX-Fähigkeit ist nicht gleich AEC oder garantierte Barge-in-Qualität. Ausgangs-ALC ist keine Mikrofon-AGC. Kein Echo-Referenzkanal wird in die MWW-Eingabe gemischt. Neue AFE/AEC/VAD-Stufen wären eine eigene Audioänderung und sind für direkte WakeNet-Inferenz nicht nötig.

Ein späterer WakeNet-Consumer soll denselben bereits korrigierten PCM-Callback verwenden; kein zweiter I²S-Reader/ADC, kein zweiter aktiver Audio-Frontend-Pfad. Ein begrenzter eigener Inferenzpuffer/Task ist dabei möglich, aber ausschließlich für die ausgewählte Engine. Callback übernimmt nur begrenztes Kopieren in den Puffer, keine blockierende Inferenz. Überlaufzähler statt stiller Frameverluste. Kanalzahl/Samplezahl prüfen und bei Abweichung geschlossen fehlschlagen, keine erfundenen Echo-/Mehrkanalsamples.

Runtime-Wechsel sind grundsätzlich über start/stop/destroy/create möglich, aber die Onju-Teardown-/ADF-/VA-Interaktion ist dafür nicht verifiziert. **Erster robuster Entwurf: Auswahl persistent speichern und kontrollierten Neustart ausdrücklich auslösen/erfordern**, statt während VA/TTS einen zweiten Consumer zu starten. Nicht implementiert und kein Reboot ausgeführt. Für spätere Runtime-Wechsel: Start der neuen Engine erst nach Task-Ende, Callback-Entkopplung, Modellfreigabe und tatsächlichem Mikrofon-STOPPED; Generations-ID verwirft verspätete Treffer. Keine gegenseitigen Auto-Restarts.

Default bleibt MWW; neue versionierte Preference für Engine, bestehende Sensitivity-/Modell-IDs unverändert. Eindeutige Default-/Restore-Reihenfolge nach Komponenten-Setup und lokale begrenzte Erfolgsprüfung müssen Audiozähler UND Inferenz belegen. Mute/Use Wake Word sperren beide Start- und Detection-Callbacks; Unmute startet nur die gewählte Engine. Bei VA/TTS bleiben der vorhandene VA-IDLE-Barrier, Bestätigungston und Assist-Delay unverändert.

Erster WakeNet-Katalog sollte nur Alexa mit stabiler Zuordnung zur vorhandenen Alexa-Slot-ID anbieten, keine fünf MWW-Wörter vortäuschen. Slot 1 hat bei identischer Auswahl weiter Priorität. Die Behandlung nicht-Alexa-Slots bei Enginewechsel und der Erhalt der bisherigen MWW-Auswahl benötigen einen expliziten, getesteten Katalog-/Preferences-Entwurf; keine stillen HA-Auswahländerungen in diesem Auftrag. Keine zweite VA-Implementierung und keine separaten Conversation-IDs.

## Ressourcen und Performance

| Messgröße | 1.2.0 | Dual-Engine |
|---|---:|---|
| Linker-Flashverbrauch | 1.823.307 Byte | nicht gebaut, unbekannt |
| Static RAM | 130.095 Byte | nicht gebaut, unbekannt |
| OTA-Dateigröße | 1.823.424 Byte | kein Artefakt |
| Flash-/RAM-Delta | Referenz | nicht ermittelbar |
| Codebasen/Modelle gleichzeitig im Flash | fünf MWW-Modelle/VAD | grundsätzlich plausibel; kein Linknachweis |
| interner Heap / größter Block | keine neue Messung | keine Messung |
| PSRAM / Boot-/Engine-/VA-/TTS-Peaks | keine neue Messung | keine Messung |
| Onju-Inferenzzeit / CPU / Drops / Loop-Warnings | keine vergleichbare Messreihe | keine Messung |

Die Flash-/RAM-Zahlen stammen aus dem finalen 1.2.0-Clean-Build, nicht aus einer Schätzung. Die Summengröße allein des neuen Alexa-Modells beträgt ca. 0,29 MB (9er) bzw. 1,56 MB (10er); zusätzlich kommen Code, Modellpacker-Strukturen, Alignment und Laufzeitpuffer hinzu. Daraus keine finale Firmwaregröße ableiten. Die statische RAM-Auslastung allein belegt keinen freien/zusammenhängenden Runtime-Heap.

Vorhandene **historische RC2-Messungen**, nicht neue 1.2.0-/Dual-Engine-Messungen: nach Managed-OTA Boot-Intervall internal_min 150.252 Byte, internal_now 214.848 Byte, largest_internal_now 120.832 Byte, psram_min 8.322.812 Byte. Manifestcheck in RC1: internal_min 149.236 Byte. Diese Intervalle wurden damals mit einer bestimmten Konfiguration/einem aktiven Modell gemessen, nicht als zwei-Modelle-plus-WakeNet-/VA-/TTS-Worst-Case. Sie sind weder eine konkrete freie Reserve für das neue SDK noch ein Nachweis kritischen RAMs. Keine aktuelle Heap-Abfrage, kein neuer Geräteclient und keine neuen Runtime-Aktionen ausgeführt.

CPU-/Inferenzmessung und Engine-Start-Peaks sind ohne Ausführung auf ESP32-S3 nicht durch Hosttests ersetzbar. Keine x86-Laufzeiten oder Hersteller-Korvo-Werte als Onju-Messung ausgegeben. Es ist weder ein kritischer Heap nachgewiesen noch genügend Reserve zugesichert. Deshalb **Safe to hardware-test: NO**.

## Validierung und Schutz

- Pinned ESPHome 2026.10.2: **Config PASS, Codegen PASS für unveränderte 1.2.0-Basis**. 843 SDK-Dateien gegen die ursprünglichen SHA256/Größen geprüft. Eigene isolierte Build-/Cachepfade im experimentellen Worktree; produktiver Dashboard-Container unangetastet.
- **14 Host-Machbarkeitstests PASS**: Baseline/Runtime-Diff, CMake-Target-Kollisionen, Interface-ABI, Blob-Loader alt/neu, echte erzeugte Partitionstabelle, offizielle Modelle, keine Nabu-/HA-Modelle, Audiofrontend, VA-Katalogbindung und Lizenzbedingung. PASS bedeutet, dass die geprüften Befunde reproduziert sind, nicht dass WakeNet inferiert.
- Dual-Engine **Config/Codegen/Clean Build: NICHT DURCHGEFÜHRT / BLOCKIERT**, weil keine funktionsfähige Dual-Engine-Implementierung angelegt wurde. Der historische finale 1.2.0-Clean-Build bleibt PASS; es wurde kein neuer vollständiger Firmwarebuild und kein Factory-/OTA-Artefakt erzeugt. Keine neuen Engine-Regressionstests als bestanden behauptet.
- Tools: tools/test_wakenet_feasibility.py. Ausgabe lokal: diagnostics/wakenet-20261124/feasibility.json. Der Prüfer erwartet zuvor Codegen mit ESPHOME_BUILD_PATH=.esphome/wakenet-feasibility und zwei explizite, unveränderte ESP-SR/SDK-Quellpfade.

## Abschlussfelder

ESP-SR version investigated: 2.6.2 master bb552f1a559396a17681299cb3e199a0f1a4520a; altes SDK 0c1eecaac259af95f76723b61d4e16cef5904fc7; externe Komponente 2.4.4
WakeNet9 supported: YES, S3; konkreter aktueller Alexa-Ordner enthält 9l
WakeNet9s supported: S3-Alexa nicht abschließend verifiziert; Modellordner vorhanden
WakeNet10 supported: YES, S3
Recommended WakeNet generation: 9er-Familie für ersten kleinen Versuch, 10 als Folgekandidat
Reason: kleinerer Modell-/Hersteller-Ressourcenansatz; keine Qualitätsbehauptung
Alexa model: wn9_alexa / wn10_alexa offiziell verfügbar
Jarvis model: wn9_jarvis_tts verfügbar
Mycroft model: wn9_mycroft_tts verfügbar
Okay Nabu model available: NO
Hey Home Assistant model available: NO
WakeNet license: Espressif MIT / Drittanbieterhinweise
Model redistribution allowed: unter Espressif-Hardware-/Notice-Bedingungen; Markenrechte gesondert
ESPHome integration approach: External Component über vorhandenen PCM-Consumer, nach SDK-/Modellversorgungsgate
External component required: YES
Official component available: NO in ESPHome 2026.10.2
Existing ADF compatible: PCM-seitig plausibel; aktuelles ESP-SR nicht als Drop-in nachgewiesen
Existing AEC compatible: kein aktives AEC in 1.2.0 vorhanden
Existing microphone path reusable: YES, als Architekturpfad; nicht mit WakeNet getestet
Second audio pipeline required: NO, keine zweite Hardwarepipeline vorgesehen
Dual-engine firmware technically possible: grundsätzlich plausibel, noch nicht sauber nachgewiesen
Runtime engine switching possible: API-seitig plausibel, Onju-Lifecycle ungeprüft
Reboot required for engine change: noch nicht entschieden/implementiert; erster Entwurf bevorzugt kontrollierten Neustart
HA Wakeword Engine select implemented: NO
Persistent engine selection implemented: NO
microWakeWord regression: keine Runtime-Änderung vorgenommen
MWW functionality byte/functionally protected: Runtime-Source identisch zu 1.2.0; kein neuer Binary-/Hardwarevergleich
Flash 1.2.0: 1.823.307 Byte
Flash dual-engine: N/A
Flash delta: N/A
Static RAM 1.2.0: 130.095 Byte
Static RAM dual-engine: N/A
Delta: N/A
Internal heap: keine neue Messung
PSRAM: keine neue Messung
Worst measured allocation: keine Dual-Engine-Messung
WakeNet inference time: Onju nicht gemessen
MWW inference time: keine vergleichbare Messreihe
Mute compatible: vorgesehen, nicht integriert/getestet
Use Wake Word compatible: vorgesehen, nicht integriert/getestet
Two pipeline slots compatible: vorhandener VA-Katalog braucht enginebewussten Adapter
Config: PASS (nur unveränderte Basis)
Codegen: PASS (nur unveränderte Basis)
Clean Build: kein neuer Dual-Engine-Build
Host tests: 14/14 Machbarkeitsprüfungen PASS
Recommended next step: atomare In-App-Modellversorgung plus eine konsistente SR-Generation isoliert gegen den ADF-/IDF-Linker bauen; erst danach Engine-Arbitrierung und Select
Safe to hardware-test: NO

Wohnzimmer changed: NO
Küche changed: NO
main changed: NO
Release 1.2.0 changed: NO
releases/latest changed: NO

STOPP. Keine Geräteaktion oder Veröffentlichung freigegeben. A/B-Matrix und Messverfahren liegen im Notebook artefact:a_5550c3c21a1d; kein realer A/B-Test ausgeführt.
