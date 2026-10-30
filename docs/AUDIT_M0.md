# M0 audit — 30 October 2026

This is the English record of the initial audit. Read STATUS.md for later
hardware evidence; unknowns here describe the initial engineering stage.
The main reference was the supplied brief in CODEX_START.md. The original
starter archive provided engineering instructions and tests, not working firmware.

## Exact versions inspected

- PicoSwitch2 v2.5.0 annotated tag object:
  3a19cf15c460a3f932f34153cf37394f5b5f4c86.
  Source commit: cdb5bf6f85cef9998c11da280073a0c7642b712c.
- Main at audit time: 4f90703b4d7236fb858ad3acba1bd3b419fe5f90.
  A targeted comparison showed main lacked src/nfc and src/switch_pro2.
  The requested tag was therefore essential.
- Switch 2 controller research: a3306b473acff0d6844fb1e288883a3940df0baf.
  commands.md, descriptors.md, and hid_reports.md were inspected.
- The switch2-pico counterexample used a first-generation Pro Controller
  personality, 057E:2009. It did not demonstrate this selected NFC path.
  This project instead preserves Pro Controller 2 identity 057E:2069.

## Reusable USB/NFC path

Upstream main starts Bluetooth on core1 and USB on core0. TinyUSB dispatches
through usb.c/usb_descriptors.c to switch_pro2.c.
HID endpoint 0x81 sends report 0x09 with its NFC event counter. NFC command 0x01
arrives on bulk OUT 0x02 and replies through IN 0x82.

ns2_vendor_rx reassembles fragments; ns2_vendor_tx queues replies under
backpressure. ns2_virtual_nfc_runtime handles scan state, begin-read, and 70-byte
blocks. ns2_virtual_nfc builds the 600-byte NFC buffer. virtual_amiibo checks
format, UID/BCC, and CRC.

Seven portable modules and their upstream tests were imported unchanged.
docs/upstream-files.json records their SHA256 values. identity.c derives the
descriptors and bootstrap responses from the same tag, adding bounds checks.
USB pairing math remains necessary for wired operation and does not load a
Bluetooth stack. The public wired pairing B1 constant is not an amiibo master key.

## Removed dependencies and adaptations

Upstream links pico_cyw43_arch_none, pico_btstack_classic, pico_btstack_ble,
pico_btstack_cyw43 and Bluetooth HID handling. Its CMake resolves BTstack early;
changing only PICO_BOARD is insufficient.

The independent target explicitly selects sources and links no CYW43, BTstack,
BLE, Bluepad32, Opus audio codec, or companion application. Bluepad32 had already
been replaced by joypad-os upstream. Inputs are neutral plus BOOTSEL and optional
GPIO buttons. Core1 is not started; core0 services USB and NFC.

Upstream persistence depends on btstack flash-bank helpers and its flash layout.
The port instead reserves two 4096-byte sectors at the end of flash. Records have
data CRC, record CRC, generation, and a final commit marker.
PC configuration uses a CDC personality mutually exclusive with controller mode.

The minimal Pro2 configuration has two HID/vendor interfaces, 80 configuration
bytes, a 97-byte HID descriptor, 64-byte packets, 1 ms polling and bcdDevice 0x0210,
matching the upstream no-audio option. It does not expose the full retail audio
configuration. Initial Switch 2 acceptance was unknown.

## Licenses and evidence boundaries

PicoSwitch2 Apache-2.0 was checked at the tag and its license retained.
Pico SDK 2.2.0 is BSD-3-Clause with component-specific third-party terms.
TinyUSB is MIT. See THIRD_PARTY_NOTICES.md.
No amiibo dump, amiibo authentication key, Nintendo artwork, game, or save was imported.

Wireless-board hardware claims upstream did not establish behavior on an original
Pico B2, this no-audio personality, or the new CDC/flash transport. Builds and host
tests alone did not establish physical USB timing, flash behavior, controller
routing, or the Epona result.

Console NFC writes are rejected without modifying the stored tag. Persistent
console writes remain separate M5 work. If a game requires a write, that path
must be measured rather than assumed to work.

## Reproduce the source comparison

In a reference clone without changing its checkout:

```text
git rev-parse v2.5.0^{commit}
git fetch --depth 1 origin main
git diff --stat v2.5.0 FETCH_HEAD -- CMakeLists.txt src/nfc src/switch_pro2 README.md
git ls-tree --name-only FETCH_HEAD src/
```

Reference repositories are read; their source files are not modified.
