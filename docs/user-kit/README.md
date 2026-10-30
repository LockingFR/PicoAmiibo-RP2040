# PicoAmiibo USB — original starter kit, English translation

Target: original Raspberry Pi Pico RP2040 B2, non-W, official Switch 2, and TOTK.
The original archive supplied a development mission, constraints, and tests,
not working firmware. Its initial non-W feasibility was unknown.

## Original workflow

1. Read the complete CODEX_START.md in a separate working project.
2. Inspect the tagged upstream sources, create a real pico target, and attempt
   compilation with licensed reusable code.
3. Once an experimental UF2 exists, the user chooses the correct board and
   performs physical tests from docs/TEST_MATRIX.md.
4. Never equate compilation with operation on Switch 2.

The non-wireless Pico has no Bluetooth or NFC radio, but can emulate a USB
controller protocol. Its only native USB port is used sequentially for PC
configuration and console operation. Initial priority was one stored amiibo and
one accepted TOTK scan, before a sophisticated library application.

These files are translated copies of the initial instructions. The SHA256 in
archive-sha256.txt identifies the original archive, not the translated file bytes.
Current evidence is recorded in the repository-root STATUS.md.
