# Initial test matrix — every physical case starts UNTESTED

- T01: PICO_BOARD=pico compiles; a UF2 is produced and its SHA256 recorded.
- T02: no CYW43, BLE, or BTstack dependency/linkage in the non-W build.
- T03: Windows USB descriptors/configuration can be inspected without errors.
- T04: a synthetic fixture transfers to Pico and readback/CRC matches.
- T05: interrupted flash update preserves a complete committed record.
- T06: BOOTSEL/tag selection does not block USB service.
- T07: real Switch 2 recognizes the expected controller.
- T08: real TOTK initiates NFC requests to the Pico.
- T09: Pico answers a tag presentation without timeout/protocol error.
- T10: TOTK accepts legitimate user-supplied amiibo data.
- T11: deliberate removal/re-presentation works without permanent false presence.
- T12: reconnect/recovery is safe and firmware remains manually recoverable.

## Initial physical protocol

1. Preserve previous firmware when available and record the candidate UF2 hash.
2. Hold BOOTSEL while connecting to the PC, identify the correct RPI-RP2 volume,
   and manually copy the chosen test UF2.
3. Disconnect from PC and connect to the Switch 2 dock with a USB data cable.
4. Open TOTK amiibo scanning at a suitable location and trigger presentation.
5. Record time, game, messages, Pico LED and any actual traces. Do not mark
   T08–T11 PASS without a real test.
6. If blocked, disconnect and manually recover through PC BOOTSEL mode.

Do not call a simulated response physical validation. Do not include third-party
dumps, authentication keys, or saves in a public test report.
