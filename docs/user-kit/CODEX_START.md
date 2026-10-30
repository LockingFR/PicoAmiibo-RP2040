# Engineering mission — PicoAmiibo USB for the original RP2040 Pico

Original brief: 30 October 2026. At the time of the initial kit, feasibility on
the non-wireless Pico had not been demonstrated. This document is the English
translation of that scope; `STATUS.md` records subsequent results.

## Goal

Use an original Raspberry Pi Pico RP2040 B2 without Bluetooth or Wi-Fi, connected
by a USB data cable to an official, unmodified Nintendo Switch 2. Emulate the USB
controller protocol needed to present a stored amiibo in Tears of the Kingdom,
initially to obtain Epona. Do not modify the console, cartridge, game, or save files.

The board has no NFC antenna. All NFC interaction is emulated through USB Pro
Controller 2 commands. Its single native USB port connects to PC and console
sequentially, never to both hosts at once.

## Required work

1. Inspect and pin [PicoSwitch2 v2.5.0](https://github.com/notsosaelin/PicoSwitch2/tree/v2.5.0),
   not whichever implementation happens to be on main.
2. Trace HID Pro Controller 2, vendor USB NFC commands, and Virtual Amiibo.
   Identify portable code, its licenses, and Pico W dependencies.
3. Create an independent real `PICO_BOARD=pico` target without CYW43, BTstack,
   BLE, Bluepad32, or a radio-management second core.
4. Replace wireless inputs with neutral inputs and controlled BOOTSEL gestures.
   Preserve the USB service loop, descriptors, and NFC state machine.
5. Provide offline Windows loading of one user-supplied amiibo, validate size,
   structure, and integrity, persist it transactionally, and read it back.
6. Start with no tag presented. Support deliberate presentation/removal and a
   separate PC configuration personality.
7. Produce actual builds, reproducible tests, commits, and a physical test plan.
   Compiling is not proof of console compatibility.
8. Maintain `STATUS.md` and `HANDOFF.md` with evidence and remaining unknowns.

## References

- PicoSwitch2 `v2.5.0` sources, release notes, CMake, USB/NFC modules, and tests.
- [Switch 2 controller research](https://github.com/ndeadly/switch2_controller_research):
  commands, descriptors, and HID reports.
- [Raspberry Pi microcontroller documentation](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html):
  original Pico, 264 KiB SRAM, 2 MiB flash, native USB 1.1.
- [switch2-pico](https://github.com/joshbirnholz/switch2-pico) as a warning that a
  Switch 1 Pro Controller personality does not by itself establish a working NFC path.

Upstream wireless-board hardware claims are not proof for this non-wireless port.
Prefer reusable, licensed code over speculative protocol rewrites.

## Milestones

- M0: targeted audit, exact versions, license/provenance and uncertainty matrix.
- M1: real Pico UF2, no radio linkage, passing host tests and memory checks.
- M2: actual Switch 2 controller recognition, with the observed identity recorded.
- M3: actual NFC dialogue, measured rather than inferred from a PC build.
- M4: actual TOTK scan and game result reported by the user.
- M5: quality-of-life work after M4; multiple hardware slots and NFC writes remain
  separate work. A Windows library was authorized after the Epona result.

## Minimum tests

Validate descriptors/endpoints, initialization, packet bounds, timeouts,
fragmentation, NFC state transitions, removal/re-presentation, CRC, malformed
inputs, no-tag behavior, SRAM/flash budgets, and transactional storage interruption.
Use artificial fixtures for host tests. Their authentication is not valid hardware
evidence. Preserve all previous firmware deliveries.

## Boundaries

No automatic device flashing, console modification, save editing, unrelated
project changes, tag dump/key distribution, or premature multi-slot firmware.
Keep private inputs outside Git and release packages. Ask for the user only when
a physical test or an explicitly manual installation is required.

Expected deliverables are source commits, UF2 files when buildable, manifests and
hashes, `USER_TEST.md`, `STATUS.md`, `HANDOFF.md`, and an honest distinction between
build, simulation, PC hardware, and console evidence.

The later Manager mission is in `MANAGER_MISSION_V1.md`. The current publication
request changes the maintained application and documentation language to English.
