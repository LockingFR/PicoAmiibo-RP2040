# Firmware qualification matrix — P0/P1/P2

The initial all-UNTESTED matrix is retained in the translated starter kit.
Host PASS is never a substitute for the corresponding physical test.

- **T01, Pico UF2/hash:** PASS ARM build with delivery logs and manifests.
- **T02, no radio linkage:** PASS explicit CMake source/link selection and ELF symbol audit.
- **T03, Windows USB:** limited physical observation of CDC and controller
  HID/composite enumeration. The vendor MI_01 interface showed Error under
  Windows; its cause and Windows bulk behavior were not qualified. Pro2 descriptor
  sizes/interfaces/endpoints pass host tests.
- **T04, load/readback:** limited hardware PASS for a real 540-byte CLI load,
  flash commit, complete identical readback and coherent state. Later Manager
  0.1.1 identification/readback was observed. These are not tests of every input.
- **T05, flash interruption:** physical power-loss qualification pending.
  The in-memory model passes 5,120 erase/program interruptions with old/new
  committed-record recovery and CRC checks.
- **T06, BOOTSEL/USB:** CDC entry and EXIT return to Pro2 were observed. Sustained
  traffic timing remains unqualified. BOOTSEL uses SRAM/QSPI access with IRQs
  briefly disabled and no active core1.
- **T07, controller recognition:** functional user evidence from the successful
  post-P1 TOTK scan; no complete console descriptor/bus capture.
- **T08, real NFC commands:** functional inference from the reported successful
  scan, without a captured command stream establishing every byte.
- **T09, scan timing:** a successful scan was reported, without a timeout/stress
  campaign. Host coverage includes the 600-byte read path, state sequences,
  errors, and 20,000 malformed packets.
- **T10, game result:** the user explicitly reported Epona after P1. No save
  inspection, video capture, or general compatibility campaign.
- **T11, remove/re-present:** host transitions pass. Repeated real-world cycles
  are not comprehensively qualified.
- **T12, reconnect/recovery:** session reset on mount/unmount and mode changes
  is implemented and host-tested; broad physical recovery testing remains pending.

## Reproduction and model limits

tools/test.ps1 rebuilds 11 C executables using -Wall -Wextra -Werror and ASan/UBSan
under WSL Ubuntu-24.04, then runs 13 Python tests. The Python tests also run on
Windows. Firmware builds use the pinned Pico SDK and an explicit ARM toolchain.
No test/build script writes the console or flashes a board.

The flash model erases to 0xff and programs only 1-to-0 transitions. An interruption
after significant commit bytes may leave a new record already valid; either
complete old or new record is acceptable after restart. It does not simulate
chip physics, brownouts, or USB timing.

Synthetic fixtures have no valid amiibo authentication. Never flash one and call
it a real Epona/authentication test. Console writes and 2048-byte tags are unsupported.

## 0.1.1/P1 — A correction

Host input tests verify double tap, an A bit in HID for 180 ms, return to neutral,
and unchanged tag presence. They also cover delayed single tap, configuration,
debounce, double-tap boundary, mode switches, and uint32 clock behavior.
The user reported Epona after this delivery. Later Windows USB serial evidence
identifies installed 0.1.1, but does not attest a full image hash.

## 0.1.2/P2 — remove L+R

Host tests check that BOOTSEL never synthesizes L/R, including 600, 1000, and
1999 ms holds. Single tap, double A, A release, and configuration remain covered.
Pico build and 11 C/13 Python host tests pass. Real-console qualification of
this variant is still pending; P0/P1 deliveries are preserved.
