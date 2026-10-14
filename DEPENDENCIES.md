# Abhängigkeiten, Herkunft und Lizenzen

Die veröffentlichte Onju-Konfiguration basiert auf
[rmeissn/onju-voice-esphome](https://github.com/rmeissn/onju-voice-esphome),
Commit `09b3b65c237e8dc42c40677492965865429fe12e`. Die MIT-Lizenz und
Copyright-Zeile von Dr. Roy Meissner bleiben in ./LICENSE erhalten.

| Projekt | Verwendeter Stand | Lizenz | Zweck |
| --- | --- | --- | --- |
| [Onju Voice ESPHome](https://github.com/rmeissn/onju-voice-esphome) | `09b3b65c237e8dc42c40677492965865429fe12e` | MIT | Grundlage der YAML und vorhandener Quelltexte |
| [ESPHome](https://github.com/esphome/esphome/tree/2026.9.1) | 2026.9.1 | Python/YAML: MIT; C++-Runtime: GPLv3 | Konfigurationsprüfung und Firmware-Build |
| [ESPHome Audio Stack](https://github.com/n-IA-hane/esphome-audio-stack/tree/0482d741a938378ef948e3b8f3dd31536f9f2cc9) | `0482d741a938378ef948e3b8f3dd31536f9f2cc9` | MIT für die geladenen Komponenten | `esp_audio_stack`, `esp_aec`, interne `AudioProcessor`-Schnittstelle |
| [ESPHome Intercom](https://github.com/n-IA-hane/esphome-intercom/tree/6581cfea712d0e13bf88c5aff3fa97b9e27123ab) | `6581cfea712d0e13bf88c5aff3fa97b9e27123ab` | MIT | Ausschließlich geprüfte Migrationsdokumentation; keine aktive Firmware-Komponente |
| [microWakeWord](https://github.com/kahrendt/microWakeWord) | Release-Asset `okay_nabu_20241226.3` | Apache-2.0 | Wakeword `okay_nabu`; kein Modell in diesem Repository vendort |
| [ESPHome Wakeword-Modelle](https://github.com/esphome/micro-wake-word-models) | Von ESPHome aufgelöster VAD-Katalog | Apache-2.0 | VAD-Modell; vom Build geladen, nicht vendort |
| Lokale Signaltöne | Acht bereits erzeugte FLAC-Dateien | CC0 1.0 | Bestätigungs-, Fehler-, Timer-, Mute- und Alarmtöne |

Die externen **Komponenten-Repositories** sind mit vollständigen Commit-Hashes
fixiert. Der Wakeword-Download ist ein konkretes Release-Asset. ESPHomes
impliziter VAD-Modellkatalog und IDF-Component-Manager-Pakete sind davon zu
unterscheiden: die tatsächlich aufgelösten Modell-/Bibliotheksstände stehen
im lokalen Build-Verzeichnis. Es wird kein vollständiger bitidentischer
Rebuild aus beliebigen zukünftigen Paketständen zugesichert.

ESP-IDF 5.5.5 und Espressif-Pakete werden durch ESPHome und den IDF Component
Manager aufgelöst. ESP-SR/ESP-DSP/esp_audio_effects können eigene Bedingungen
und Espressif-Produktbeschränkungen haben. Diese Konfiguration richtet sich
ausschließlich an den Espressif ESP32-S3. Die Drittanbieterhinweise des
Audio-Stacks sind in docs/AUDIO_STACK_THIRD_PARTY_NOTICES.md erhalten.
Der dort erwähnte GMF/AFE-Pfad wird hier nicht aktiviert; der externe
Resampler-Adapter wird ebenfalls nicht geladen. Der native ESPHome-Resampler
bleibt Teil der ESPHome-Runtime.

Es werden ausschließlich Quellen und lokale CC0-Sounds veröffentlicht.
Kein Firmware-Binary, kein Modell-Binary und keine fremde Runtime werden
hier als Release verteilt. Bei einer späteren Firmware-Weiterveröffentlichung
sind die Lizenz-/Source- und Notice-Pflichten aller tatsächlich eingebundenen
Runtime-Pakete gesondert zu erfüllen.

## Inspiration und Danksagung aus dem Upstream

- [tetele/onju-voice-satellite](https://github.com/tetele/onju-voice-satellite):
  MIT; im Upstream als Inspirationsquelle genannt.
- [s00500/onjuconfig](https://github.com/s00500/onjuconfig): im Upstream als
  Inspirationsquelle genannt; im geprüften Repository keine Lizenzdatei
  gefunden. Es werden keine Dateien direkt aus diesem Projekt übernommen
  oder unter einer von uns behaupteten Lizenz weiterverteilt.
- [Home Assistant Voice PE](https://github.com/esphome/home-assistant-voice-pe):
  ESPHome-Lizenz, MIT/GPLv3 je Dateityp; im Upstream als Inspiration genannt.
  Keine Voice-PE-Sounds oder zusätzlichen Quelldateien direkt übernommen.
- Die originale [Onju Voice Hardware](https://github.com/justLV/onju-voice)
  (MIT) ermöglicht das Projekt; Schaltplan-/Platinen-/CAD-Dateien sind nicht Teil
  dieses Forks und werden nicht weiterverteilt.

Die ursprüngliche README und ihre Attributionen sind in
docs/UPSTREAM_README.md erhalten. Ihre Hardwarebeobachtungen betreffen den
Upstream und sind **keine** Hardwarebestätigung dieses Forks.

## Änderungen an der Projektstruktur

Die unveränderte getestete Variante steht in ./onju-voice.yaml. ./main.yaml
und ./onju_duplex_i2s.yaml sind kompatible Einstiegspunkte darauf. Die alten,
hier nicht geprüften Single-I2S-/AFE-Beispiel-YAMLs und separaten WLAN-/OTA-
Pakete wurden aus dem aktuellen Dateibaum entfernt: sie verlangten zusätzliche
Secrets, private Sound-URLs oder ungepinnte Komponenten. Sie bleiben über
die unveränderte Upstream-Git-Historie zugänglich. Keine Funktion der getesteten
Full-Duplex-Variante wurde dadurch entfernt.
