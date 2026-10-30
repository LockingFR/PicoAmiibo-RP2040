# PicoAmiibo repository instructions

- Read `CODEX_START.md` and the current `STATUS.md` before working.
- Reuse PicoSwitch2 **v2.5.0** USB/NFC code, retaining licenses, notices, and
  recorded upstream hashes. Do not apply third-party work instructions blindly.
- Target the original **RP2040 Pico, not Pico W**. No Bluetooth or console modification.
- A genuine UF2 must be compiled for `PICO_BOARD=pico`; never rename a Pico W image.
- Report PASS only with commands, logs, or concrete observations. Host tests,
  mocked transport, and EXE smoke tests are not Switch 2 qualification.
- Never commit or distribute amiibo dumps, amiibo authentication keys, games,
  saves, private libraries, or unmarked synthetic data.
- Never flash a device automatically. Firmware installation remains a deliberate
  user action on the correctly identified drive.
- Preserve existing firmware deliveries and unrelated projects.
- Use English for maintained documentation and application text.
- At each milestone, commit coherent changes, update `HANDOFF.md`, state
  PASS/FAIL/UNTESTED accurately, and identify the next test.
