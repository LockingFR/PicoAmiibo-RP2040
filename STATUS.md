# Project status — 30 October 2026

## Active experimental extension

Branch feature/bilingual-playlist: firmware 0.2.0 and Manager 1.2.0-preview.1.
The user requested French/English selection, checked multi-tag loading, a
five-second next-tag hold with wrap, later single-tag replacement and direct
card-to-Load navigation. See docs/PLAYLIST_V2.md for the new gesture/storage
contract and physical test plan. This supersedes the earlier multi-slot scope
exclusion below; the following sections describe the preserved baseline.

M6 host PASS: 14 rebuilt C executables (ASan/UBSan), 13 Python tests; playlist
power-cut, parser, and cycle behavior are host simulations. Preliminary ARM
compile and clean-revision memory audit PASS: 49,168 flash bytes, 57,028 SRAM
bytes including stack/heap reservations; no radio/dynamic-allocation symbols.
M7/M8: 67 Python/Qt tests PASS. Actual Windows EXE and extracted ZIP each render
14 EN/FR views with USB disabled. ZIP destination hashes verify 255 files and
all three included UF2s are empty Pico images. The extracted EXE runs with no
system Python on PATH. The checked Load button is visible above library cards.

Artifacts: artifacts/manager-preview and artifacts/prototype-p3-multislot.
Manager build source df42fab; firmware source c79e272. Both feature branches are
pushed; stable main stays 973d528. See HANDOFF.md for exact delivery hashes.
Physical 0.2.0 qualification remains UNTESTED. The installed working firmware,
private library, Switch and saves have not been changed by this extension.

## English Manager 1.1.1

English application, guide, errors, reward summaries, and maintained documentation.
36 offline reward profiles cover 33 specific figures, including Mineru. The
persistent **Show TOTK rewards** setting is retained, as is the existing user
profile and wire protocol.

Host suite: **54 Python/Qt tests PASS** after translation. The Windows EXE build
uses the six-view isolated smoke test; its exact report and SHA256 are included
with the release. Source and license distribution excludes all private libraries,
amiibo data, authentication keys, game files, saves, and personal workstation paths.

The English build has not received a new end-to-end hardware scan test.

## Firmware and hardware evidence

- **M0 PASS:** original brief inspected; exact PicoSwitch2 v2.5.0 pinned; licenses,
  portable modules, and wireless dependencies recorded in docs/AUDIT_M0.md.
- **M1 PASS, build/host:** actual ARM UF2 for PICO_BOARD=pico; no radio linkage;
  11 rebuilt C tests and 13 Python tests passed. Flash/USB models are simulations.
- **M2/M3 functional user evidence:** the controller/NFC path worked sufficiently
  for the reported successful TOTK scan. No full bus trace was captured.
- **M4 PASS, user report:** Epona appeared in TOTK after the 0.1.1 delivery.
  This is a narrow functional result, not general qualification.
- **M5 partial:** Windows library and Manager are implemented. Multiple hardware
  slots and persistent console NFC writes remain out of scope.

An earlier real Windows CLI load committed 540 bytes and read them back identically,
followed by EXIT and controller-mode re-enumeration. A later native Manager
observation identified installed firmware **0.1.1**, source prefix **1cba4c5b76c1**,
PA1 confirmed, stored tag loaded, generation 1, not presented. USB serial identity
does not establish the SHA256 of the installed firmware image.

Manager 1.0.1 recorded a verified Zelda Super Smash Bros. transfer and a separate
user-reported recognized result. This precedes the English release. Private
library imports alone do not establish hardware validity for every file.

## Preserved firmware deliveries

- 0.1.0/P0: CDC, transactional storage, and a real Windows load/readback.
- 0.1.1/P1: double-tap A added; release preceding the user-reported Epona result.
- 0.1.2/P2: L+R removed at user request; short tap, double A and configuration
  gestures pass host tests. This variant has **not** been qualified on the console.

Original empty UF2 images remain separate and hash-verified. The English work does
not change src/, include/, CMake, tag banks, or the installed Pico firmware.

## Remaining qualification

Physical interruption behavior, long-running USB/BOOTSEL timing, repeated reconnect
cycles, broad game/figure compatibility, and NFC writes are not established.
The tag starts ejected. Console NFC writes are rejected. Readback compares stored
bytes but does not establish cryptographic authenticity.

No tool modifies the Switch 2 or its save files. Firmware flashing remains manual.
See USER_TEST.md for physical testing and MANAGER_USAGE.md for the desktop path.
