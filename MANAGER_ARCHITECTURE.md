# PicoAmiibo Manager — implementation architecture

The desktop application reuses the existing single-tag firmware and wire protocol.
The English 1.1.1 release changes presentation/catalog data, not the C firmware.

## Preserved foundation

Original 0.1.1/P1 and 0.1.2/P2 deliveries were copied to ignored local backup
directories and reread with SHA256 checks before Manager work. P1 preceded the
reported Epona result; P2 removes L+R and remains a separately qualified build.
The shipped empty firmware images contain no private tag.

## Layout

- `manager/core`: SQLite library, private file copies, validation, settings,
  history, optional public metadata cache, and offline TOTK reference.
- `manager/transport`: Windows SetupAPI/pyserial discovery and CDC adapter.
- `manager/app`: PySide6 Widgets, five pages, reward dialog, and worker threads.
- `manager/assets`: original NFC icon and a public factual reward JSON catalog.
- `manager/tests`: artificial protocol model, core tests, and real Qt interactions.
- `tools/load_amiibo.py`: common CLI/GUI loader with optional progress callbacks.
- `tools/uf2.py`: structural validation and firmware UF2 tooling.
- `tools/build_manager.ps1`: build, smoke test, and portable package.

USB operations are serialized. Device scans and probes use workers, as do optional
metadata downloads, to keep the UI responsive. Cancellation is checked at I/O
boundaries. Closing during a transfer asks the user to finish/cancel; other workers
are allowed to terminate before the window is destroyed.

## Exact CDC flow

Configuration USB VID/PID is CAFE:4013. Port baud rate is 115200.

1. `INFO\n` → `PA1 loaded=... size=... crc=... generation=... presented=...`,
   with additional command/NFC/rejection counters.
2. `LOAD n crc_hex\n` → `READY`, followed by exactly n bytes.
3. `OK` is returned after the firmware validates and commits the stored record.
4. `READ\n` → `DATA n crc_hex\n`, followed by all stored bytes.
5. The existing loader compares source and readback byte for byte and verifies
   final INFO consistency.
6. `EXIT\n` → `BYE`, followed by controller-mode USB re-enumeration.

Only **Load and verify** sends LOAD. Automatic configuration probes use INFO and
READ only. Progress reports actual bytes accepted by the serial port/read back;
commit and comparison are distinct stages. An EXIT failure after successful
readback does not invalidate the measured save.

Firmware accepts 540/572 bytes and expires incomplete loading after five seconds.
Two flash banks, data/record CRC, generation and final commit protect transactional
updates. A disconnect after commit but before readback leaves an unverified state,
not a guarantee that the old record remains active.

## Observability and identity

Version is inferred from the USB serial when its PicoAmiibo format is recognized;
PA1 does not provide a firmware version. This is not full-image attestation.
READ can identify a tag by SHA256 and its public ID at bytes 0x54–0x5b.
Format/BCC/CRC do not authenticate amiibo data.

2E8A:0003 indicates the ROM bootloader. Normal 057E:2069 can also identify a retail
controller, so it remains only a controller candidate. Multiple CDC candidates
require a deliberate port selection.

When the Pico is attached to the console, the PC has no connection. The Manager
does not know the running game, scan state, save progress, or actual reward.
Game recognition is saved as a separate user-reported observation.

## Data and network

Default profile: `%LOCALAPPDATA%/PicoAmiiboManager`. SQLite stores settings,
history, and tag metadata; private binaries use SHA256 filenames. Import validates
before copying, duplicates are keyed by SHA256, and each load revalidates the local
copy. The profile is never included in Git or package inputs.

Optional GET requests download a public catalog and public artwork into a local
cache. They do not upload tag contents. English offline Zelda identities remain
available without network access. Original tag names/history remain private user
data rather than being rewritten by a language update.

## TOTK references

36 profiles cover 33 specific figures and three generic/internal cases. Figure
IDs, conditions, table quantities and relative weights are source-attributed.
Mineru uses its pinned public TagMo ID. No generic file is promised exclusive loot.
The persistent `show_totk_rewards` preference controls summaries, reward search,
and access buttons. Reward data never changes the transfer or game outcome.

## Validation boundaries

The suite has 54 Manager/loader Python tests, including Qt interactions. The
firmware suite rebuilds 11 C executables and runs its 13 historical Python tests.
EXE smoke testing is real Windows execution with synthetic data and USB disabled.
These are not console tests. See STATUS.md for actual hardware observations.
