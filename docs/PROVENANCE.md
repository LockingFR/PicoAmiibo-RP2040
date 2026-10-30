# PicoAmiibo-RP2040 foundation

Independent Apache-2.0 project for the original RP2040 Pico (`PICO_BOARD=pico`).
Upstream: https://github.com/notsosaelin/PicoSwitch2/tree/v2.5.0
Annotated tag object: 3a19cf15c460a3f932f34153cf37394f5b5f4c86.
Source commit: cdb5bf6f85cef9998c11da280073a0c7642b712c.

The seven pure C modules and their upstream tests are imported verbatim by
tools/import_upstream.py. docs/upstream-files.json records their hashes.
The new USB protocol adapter derives descriptors, factory calibration, USB pairing
math and handshake responses from src/switch_pro2/switch_pro2.c at that revision.
The USB pairing challenge is required even for a wired controller; it does not
require a Bluetooth radio, stack, driver, connection or bond database.

Research reference (read, not redistributed):
https://github.com/ndeadly/switch2_controller_research/tree/a3306b473acff0d6844fb1e288883a3940df0baf
Specifically commands.md, descriptors.md and hid_reports.md.
The current research document still labels much NFC behavior unknown. The more
complete NFC lifecycle comes from PicoSwitch2's implementation and its tests.
Upstream's hardware claims apply to its Pico W/Pico 2 W firmware, not this port.

No upstream dumps/, firmware image, amiibo data, amiibo authentication keys,
Bluetooth code, companion application or audio codec is imported.

The original engineering kit was preserved outside publication inputs.
English translations are included under docs/user-kit/. CODEX_START.md governs
scope; STATUS.md records later evidence. The archive fingerprint refers to the
original archive, not the translated documents.
Archive SHA256: ec125a4765f35f0c95024ee7c4eae0d7262c51b939cc3bca46cf113770fdfd78.
