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

Manager 1.2.0-preview.1 development adds persistent EN/FR choice, checked queue,
card-to-Load navigation and complete per-tag readback. 67 Python/Qt tests passed
before the final packaging/localization edits; final EXE validation is pending.
New outputs use dist/preview and artifacts/manager-preview, preserving 1.1.1.

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
