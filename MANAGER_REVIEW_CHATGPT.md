# Standalone technical review — PicoAmiibo Manager

This document describes the maintained implementation and evidence as of
30 October 2026. Current experimental desktop: 1.2.0-preview.1 (English/French).

The new feature branch adds 64 transactional slots in two new 64 KiB banks,
preserves the old two 4 KiB tag sectors, and negotiates CAPS/BATCH/indexed READ.
Single LOAD replaces the new playlist. BOOTSEL holds of at least five seconds
advance once with wrap; release a two-to-less-than-five-second hold for CDC.
New-tag activation first removes the previous tag, waits a second and drains old
USB messages. The next tag stays ejected. Runtime index resets to zero on boot.

The bilingual Manager persists checked order and language, opens Load on card
click, and verifies all selected tags byte for byte. Host tests simulate flash
interruptions and USB transport; these are not console qualification. No real
device writes or physical 0.2.0 Switch 2 test have been performed for this branch.
See docs/PLAYLIST_V2.md for the concrete user-operated test and rollback plan.
The baseline description below describes stable 1.1.1 and earlier firmware.

## Existing firmware

The original RP2040 Pico emulates a USB Pro Controller 2 using code derived from
PicoSwitch2 v2.5.0, commit cdb5bf6f85cef9998c11da280073a0c7642b712c.
It has no Bluetooth, Wi-Fi, or NFC radio. HID carries report 0x09 and NFC state;
vendor bulk handles NFC commands. Seven portable upstream C modules and tests
retain recorded source hashes. The USB identity/handshake adapter is explicitly
derived, with added payload bounds checks.

PC loading uses a separate CDC USB personality. A single raw 540/572-byte NTAG215
record is stored in two reserved flash sectors using CRC, generation, and final
commit. No amiibo data or authentication keys are built into firmware. NFC writes
from the console are rejected. The English Manager does not change C firmware,
flash layout, or commands.

The user reported obtaining Epona in TOTK on an official Switch 2 after 0.1.1.
A later Windows observation identified the installed USB serial as 0.1.1 with
the matching source prefix. That serial is not a full firmware image hash.
0.1.2 removes L+R but is not yet independently qualified on console.

Preserved empty UF2 SHA256:

- 0.1.1: bc71827d0893e1dd9090493484c70d258fb8d0132c6bf440111269d1b4902329
- 0.1.2: f518a2744dbb83ebb29e23b275aa91e9cacd36a656ce112ebb7b4896f77b07c9

## Desktop implementation

Python 3.13.3 x64, PySide6 6.12.0, pyserial 3.5, PyInstaller 6.22.3.
It is a local Qt Widgets application, without a server or embedded browser.
See MANAGER_ARCHITECTURE.md for the module map.

The loader shared by CLI and GUI is `tools/load_amiibo.py`. Manager work added
optional callbacks and package imports without changing the wire protocol.
Tasks run in QThread workers and signal the UI. Series/favorite/name/reward
filters act on the local library. SHA256 handles duplicates. Private originals
are never included in distribution inputs.

## Protocol and measured success

INFO identifies PA1; LOAD n crc receives READY; n bytes are sent; OK confirms
commit; READ returns DATA n crc and bytes; the source and readback are compared;
the final INFO must match; EXIT/BYE requests controller mode.

Write progress measures serial bytes, not a completed flash save. Only successful
full comparison and final state produce **Saved and verified**. If EXIT fails
after that, the app keeps the successful readback and asks for reconnection.
Cancellation is cooperative. After a disconnect between commit and readback,
the saved record must be reread; the previous bank is not assumed active.

Automatic probes only issue INFO/READ. No probing operation writes a tag.
Loading requires the user to click the actual load control.

## What the application can observe

Windows exposes COM, USB serial, and VID/PID. Configuration PA1 gives load state,
size, CRC, generation, presented state, and counters. Full READ gives SHA256 and
public figure ID. USB serial supplies a version hint, not cryptographic attestation.

VID/PID 057E:2069 also belongs to retail controllers, so it is not a unique Pico
identity. ROM 2E8A:0003 is distinct from CAFE:4013 CDC. Multiple CDC devices require
manual selection.

The single USB cable is moved from PC to console. The app cannot then observe
the game, scan, save, or loot. User feedback is stored separately from PC verification.
Gesture instructions distinguish 0.1.0, 0.1.1, 0.1.2, and unknown versions.

## Reward data and optional network

The offline reference has 36 profiles, including 33 specific figure IDs. It
contains factual item names, quantities, relative weights, conditions, and original
summaries. It does not contain tag dumps or extracted game assets. Epona is
assigned only to the two relevant Link figures; Wolf Link does not promise a
BOTW-style companion. Dusk Bow is conditional random loot, not a guaranteed scan.

Sources are pinned in `manager/assets/rewards_totk.json`:

- JordanBTucker drop-table revision 4dd8cd25ce09ed1fdf9403614ea7c68ab812e81e.
- Zelda Wiki revision 1386889 for additional figure/reference facts.
- Pinned TagMo public figure metadata for the Mineru identifier.
- Nintendo support for general amiibo use and random rewards.

The optional AmiiboAPI catalog and public artwork are GET downloads with bounded
sizes and a local cache. No private tag data is sent. Artwork is not bundled.
The earlier network test fetched 932 entries and three images into a test profile.

## Evidence levels

- Host: 54 Manager/loader Python tests, including actual Qt interactions.
- Firmware host: 11 rebuilt C executables under ASan/UBSan, 13 Python tests,
  5,120 simulated flash interruptions and 20,000 malformed packets.
- Windows EXE: six rendered views from an isolated, explicitly artificial library
  with USB disabled. Packaging requires a smoke result bound to its exact SHA256.
- Real Windows: 0.1.1 CDC identity and stored-record readback were observed. A
  Manager 1.0.1 transfer was logged as verified and the user marked it recognized.
- Real console: the user explicitly reported Epona after 0.1.1. No saved-game
  inspection, bus trace, or comprehensive compatibility campaign was performed.

The English 1.1.1 UI and firmware 0.1.2 still need their own physical qualification.
Private library imports do not prove console acceptance for all imported figures.
The repo and release contain no user library, dump, key, or save.

## Publication

Public source and a private mirror are published only at the user request.
The English publication starts from a checked, sanitized source snapshot; the
earlier local engineering history is retained locally. Build manifests identify
the publication revision. No runtime profiles or workstation paths are exported.
