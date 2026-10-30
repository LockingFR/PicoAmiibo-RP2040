# Firmware development review — 30 October 2026

PicoAmiibo-RP2040 is an independent USB controller/NFC emulator for the original
RP2040 Pico without a radio. The user reported obtaining Epona in TOTK on an
official Switch 2 after the 0.1.1 delivery. This is a specific user observation,
not a captured USB trace, video proof, or compatibility guarantee for every game.

## Reused foundation

PicoSwitch2 v2.5.0 is pinned to cdb5bf6f85cef9998c11da280073a0c7642b712c.
The inspected main branch lacked the requested USB/NFC path, so the tag matters.
Seven portable C modules and tests were imported verbatim: tag validation,
NFC codec/state machine, fragmented USB receive, buffered transmit, USB pairing
math, and firmware profile. The identity/handshake is adapted from the same tag.
See docs/PROVENANCE.md and docs/upstream-files.json.

The firmware targets PICO_BOARD=pico and links Pico SDK/TinyUSB without CYW43,
BTstack, BLE, Bluepad32, audio codec, or a radio-management core1 task.
The native USB personality is Pro Controller 2 057E:2069. HID report 0x09 includes
NFC state; vendor bulk handles NFC reads from the stored tag. There is no NFC radio.

## Offline storage and loading

Windows configuration is a separate CDC personality, CAFE:4013. The one USB cable
is used with PC and console in sequence. The loader accepts 540/572 bytes,
validates structure/BCC/CRC, writes two transactional flash banks, and reads all
bytes back for comparison. Records have generation and a final commit marker.
The tag starts ejected; console NFC writes are rejected.

Actual Windows CLI loading and full readback were observed before the reported
console success. User files remain private and outside Git/build inputs.
Structural PC checks do not establish cryptographic authenticity.

## Preserved milestones

- 0.1.0/P0, original local commit 8c7a757: first CDC/flash/load prototype; actual
  PC load/readback succeeded. A could not yet be sent through BOOTSEL.
- 0.1.1/P1, original local commit 1cba4c5: double-tap A added. The user subsequently
  reported Epona. A later USB observation identified installed 0.1.1/source prefix;
  no complete installed-image hash was read.
- 0.1.2/P2, original local commit 35d1d42: removed BOOTSEL L+R at user request.
  Built and host-tested, but still awaiting its own console qualification.

P2 gestures: short tap presents/removes after roughly 400 ms, double tap sends A
for 180 ms, two-second hold changes configuration mode, intermediate hold does
nothing. BOOTSEL sampling runs from SRAM with IRQs briefly disabled; core1 is not
started. Optional GPIO buttons are not required.

## Tests and limits

The firmware suite rebuilds 11 C executables with ASan/UBSan and runs 13 Python
tests. It covers 600-byte NFC reads, 20,000 malformed packets, 5,120 simulated
flash interruptions, bounds, CRC, timeouts, readback, and BOOTSEL gestures.
These models do not establish physical power-loss behavior, sustained USB timing,
all game/figure compatibility, or NFC write support.

Toolchain: Pico SDK 2.2.0, TinyUSB at the pinned SDK revision, ARM devkitARM GCC
16.1.0, CMake 3.31.6, Ninja 1.12.1, Windows Python 3.13.3, pyserial 3.5. Firmware
C tests use WSL Ubuntu-24.04. Reproduction scripts are tools/build.ps1,
tools/test.ps1, tools/load_amiibo.py and tools/verify_build.py.

The original P2 empty UF2 SHA256 is
f518a2744dbb83ebb29e23b275aa91e9cacd36a656ce112ebb7b4896f77b07c9.
Original firmware deliveries are retained separately; none is replaced merely
to update the desktop application.

The console, game, cartridge, save files, and unrelated projects are untouched.
Firmware installation remains manual. For the later English desktop application,
read MANAGER_REVIEW_CHATGPT.md and MANAGER_ARCHITECTURE.md.
