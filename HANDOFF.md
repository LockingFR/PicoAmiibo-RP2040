# Development handoff — PicoAmiibo-RP2040

## Active preview: feature/bilingual-playlist

User-authorized extension after 1.1.1. Read docs/PLAYLIST_V2.md first.
Firmware 0.2.0 adds 64 transactional slots, CAPS/BATCH/indexed READ, legacy LOAD
replacing the list with one tag, and one advance per five-second BOOTSEL hold.
Release a two-to-less-than-five-second hold to enter configuration. Cycling
removes the old tag, waits one second and drains USB before loading the next,
still ejected. Runtime index is RAM-only and resets to first on boot.

M6 host PASS: tools/test.ps1 rebuilt 14 C executables with ASan/UBSan and ran
13 Python tests. Includes power-cut simulation, strict protocol bounds, and
cycle removal/drain/wrap/signature/counter tests. Preliminary ARM build PASS
for non-wireless pico; final clean-revision build/package still pending.

M7 Manager 1.2.0-preview.1 adds persistent EN/FR choice, checked queue,
card-to-Load navigation and complete per-tag readback. 67 Python/Qt tests PASS.
Source and frozen EXE smoke render 14 EN/FR views with artificial data and USB
disabled. Final French library, playlist and rewards views visually inspected.
Final layout keeps batch Load above the cards and the French filter readable.
Test screenshots wait for Qt layout updates before capture.
New outputs use dist/preview and artifacts/manager-preview, preserving 1.1.1.

Firmware delivery at artifacts/prototype-p3-multislot is from clean c79e272:
49,168 flash bytes, 57,028 SRAM bytes including stack/heap reservations; no
radio/dynamic-allocation symbols; empty UF2 SHA256
4b2a389100a20b41d79b869c1225a30be2047e5fb7f9095d0d4d70ec478a4cb4.
Firmware and its source commit are independent of later UI/documentation polish.

## M8 delivered preview, hardware pending

- Manager build/package source: df42fab72178ee839df479fa5eee08743c5e7825.
- tools/build_manager.ps1 PASS: final EXE built; 67 tests; 14-view frozen smoke.
- Windows ZIP: artifacts/manager-preview/PicoAmiibo-Manager-1.2.0-preview.1-windows-x64.zip.
- ZIP SHA256: c691bd58922dd7b07f6ee1d3350885f0d5783ef493f4d5d7f61f071f381185d7.
- EXE SHA256: 6f51c8c69ed5d48f474ed77c08df5d73b46eae0e92c35ade8d6b7a6f12638916.
- Fresh ZIP extraction: 255 destination entries reread against manifest hashes;
  no private library/dump/key inputs; three correctly labeled empty Pico UF2s.
- Extracted EXE PASS: 14 bilingual views with USB disabled and system Python
  absent from PATH. Evidence: artifacts/manager-preview/portable-*.json.
- Firmware audit PASS: clean c79e272, pico, flash/SRAM within bounds, no radio or
  dynamic-allocation symbols. See artifacts/prototype-p3-multislot/manifest.json.
- Both GitHub feature branches contain the development commits. Stable main
  remains 973d528. This documentation-only milestone does not alter the binaries.

Next action: user manually installs the preview UF2 and performs the two-tag
physical test in docs/PLAYLIST_V2.md, including wrap/reboot/single replacement.
Do not mark 0.2.0 or playlist NFC scanning hardware-qualified until that evidence.

No automatic flashing, real device writes, Switch operation, or private profile
changes in this extension. Firmware 0.2.0 hardware qualification is UNTESTED.

## Historical baseline (1.1.1, preserved)

Current desktop release: **Manager 1.1.1**, English. Current firmware source:
**0.1.2**, real non-W Pico. The working 0.1.1 delivery remains preserved separately.

Read CODEX_START.md, STATUS.md, MANAGER_ARCHITECTURE.md and
MANAGER_REVIEW_CHATGPT.md before resuming.

## Current implementation

Five-page PySide6 app, local SQLite library, shared CDC loader, full readback,
favorites, optional public metadata cache, history, diagnostics, version-correct
Switch 2 guide, and 36 TOTK reference profiles with 33 mapped figure IDs.
The Show TOTK rewards preference persists. All maintained UI/docs are English.
Private filenames, library contents, and history are not rewritten by the update.

No C firmware/protocol changes were needed. Do not rebuild or flash firmware
merely to update the GUI. Keep 0.1.1 and 0.1.2 qualification separate.

## Evidence

54 Python/Qt tests pass after translation. Historical firmware tests rebuild
11 C executables with ASan/UBSan and run 13 Python tests.
The real Windows EXE smoke renders six views with an isolated artificial profile,
USB disabled, and a report bound to the exact EXE SHA256.

Actual 0.1.1 USB identity/PA1/readback was observed in Windows. A previous Manager
transfer was verified and the user reported recognition. Epona was reported on
the real official Switch 2 after 0.1.1. Do not infer qualification of 0.1.2 or the
English release from that history.

## Commands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_manager.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/test_manager.ps1 -Frozen
powershell -NoProfile -ExecutionPolicy Bypass -File tools/setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build.ps1 -BuildDirectory build/pico-p2
powershell -NoProfile -ExecutionPolicy Bypass -File tools/test.ps1
```

Build/package must use a clean revision. Read manifests and logs under ignored
artifacts directories. Private runtime data belongs in
%LOCALAPPDATA%/PicoAmiiboManager, never in source/package inputs.

## Publication and recovery

The user requested both a public repository and a private mirror. Both contain
the sanitized English project, without personal workstation paths or user data.
Earlier local milestone history remains local; published source begins at a
reviewed snapshot. New build provenance must refer to a reachable published commit.

Recover the Pico only by deliberate manual BOOTSEL/RPI-RP2 installation using the
correct device and empty UF2. Do not touch unrelated projects, the console, or saves.
Physical testing is the next user action; see USER_TEST.md.
