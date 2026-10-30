# Development handoff — PicoAmiibo-RP2040

Current desktop release: **Manager 1.1.0**, English. Current firmware source:
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
