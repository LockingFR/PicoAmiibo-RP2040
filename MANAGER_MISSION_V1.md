# PicoAmiibo Manager V1 — development brief

This is the English edition of the user-supplied Manager brief. It builds on the
existing Pico firmware rather than restarting firmware research.

## Existing foundation

The independent firmware targets an original RP2040 Pico without Bluetooth or
Wi-Fi and emulates USB Pro Controller 2 NFC reads. Windows CDC loading supports
540/572-byte images, CRC, two flash banks, transactional commit, and full readback.
The user reported Epona in TOTK after 0.1.1. Firmware 0.1.2 removes L+R and remains
separate until its console test succeeds.

## Goal

Create a modern portable Windows x64 application that lets a beginner connect
the Pico, inspect its state, choose a local amiibo, load it, verify it, and follow
a version-correct Switch 2 guide without a terminal.

Use the existing Python loader and wire protocol. PySide6 is the preferred GUI
framework. The original brief requested French; the latest user instruction
explicitly requests English throughout.

## Required pages

1. **Home:** actual connection/mode, COM port, firmware version when identifiable,
   current tag when readable, last verification, library and diagnostic shortcuts.
2. **Library:** visual cards, import 540/572-byte files, names/characters/series,
   optional cached artwork, text search, series filters, favorites, duplicates,
   selection, and persistence. Unknown files remain usable with clear validation.
3. **Load:** identify CDC peer, validate input, transmit with real progress, wait
   for commit, read all bytes back, compare, and show actionable errors.
4. **Switch 2 guide:** move from PC to console, start the in-game scan, use gestures
   for the detected firmware, and record the user-reported result separately.
5. **Diagnostics/settings:** USB identity, bootloader/CDC modes, protocol, version,
   communication probe, history, CRC, exportable logs without dumps, and recovery.

The same USB port cannot remain connected to PC and console. Never show a live
game result that the PC cannot observe.

## Quality and privacy

Preserve 0.1.1 backups and keep 0.1.2 separate. Do not change firmware/protocol
without demonstrated need. Do not implement multiple simultaneous hardware tags.
Never distribute private dumps or send their contents to a metadata service.
Network metadata/artwork must be optional, with an offline cache.
No dummy buttons or unmarked simulated device states.

Test absence, multiple devices, wrong peers, invalid size/format, disconnects,
write refusal, corrupted readback, duplicates, preferences, historical firmware
compatibility, and NFC non-regression. Protect the existing flash-bank design.

## Delivery phases

- A: inspect loader/firmware/tests, preserve backups, write architecture.
- B: real GUI for detection, file selection, loading, readback, and Switch guide.
- C: cards, metadata, search, favorites, history, diagnostics, and visual polish.
- D: portable EXE, dependency licenses, English usage, changelog, tests, screenshots.
- E: user-run physical Pico/Switch 2 tests; no unsupported hardware claims.

Commit each milestone and update the handoff. Prepare a standalone architecture
review covering exact CDC commands, observable state, detection limits, private
storage, code organization, and the real EXE status.

The user additionally requested TOTK reward references per amiibo. Display possible
rewards and conditions, not guaranteed loot. Include a persistent **Show TOTK
rewards** setting, and keep reward references separate from console telemetry.
