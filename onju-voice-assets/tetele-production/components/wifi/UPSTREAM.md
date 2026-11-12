# ESPHome Wi-Fi source provenance

Vendored byte-for-byte from ESPHome 2026.10.2 except for one guarded hook in
wifi_component.cpp: set_sta copies the AP, applies the MAC-bound Onju network
profile, and passes that copy to the unchanged native connection logic.
No API, native Wi-Fi preference key, TLS or audio algorithm is replaced.
Original copyright/license is preserved in UPSTREAM_LICENSE.txt.

The external component is required because the native saved-station loader
creates a fresh AP without compiled static IP parameters. Post-connect changes
would be too late to preserve the first connection's network configuration.
