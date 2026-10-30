# PicoAmiibo Manager changelog

## 1.2.0-preview.1 — 30 October 2026

- Persistent French/English choice with immediate in-window translation.
- Card body opens Load; checkboxes queue an ordered selection without navigating.
- Checked playlists up to 64 tags, capability negotiation and byte-for-byte
  readback of every tag. Older firmware remains compatible with single loads.
- Firmware 0.2.0 adds separate transactional playlist banks, five-second cycling,
  wrap, boot-to-first and single LOAD replacing the playlist. Old tag banks remain.
- Separate preview output, bilingual EXE smoke and reproducible physical test plan.
- Hardware qualification of the new firmware remains UNTESTED.

## 1.1.1 — 30 October 2026

- Complete English labels for the history Game column and USB configuration state.
- Refresh the portable Windows package and screenshots; no firmware/protocol changes.

## 1.1.0 — 30 October 2026

- English interface, errors, Switch 2 guide, reward summaries, and documentation.
- English README, build instructions, and sanitized publication to GitHub.
- Mineru public figure ID mapped to the existing TOTK reward reference.
- Reward summaries explicitly identify possible rewards rather than guaranteed loot.
- Existing library/preferences retained; no firmware or CDC protocol changes.

## 1.0.1 — 30 October 2026

- Persistent Show TOTK rewards setting in Diagnostics, enabled by default.
- Disabling hides summaries/reference buttons and removes reward text from search.
- Package/export version synchronized with the application version.

## 1.0.0 — 30 October 2026 — Windows prototype

- Five-page PySide6 desktop application, originally delivered in French.
- Private persistent library, 540/572-byte validation, SHA256, duplicate handling,
  favorites, optional public metadata/artwork cache.
- Windows serial/SetupAPI discovery; distinct CDC, bootloader, and controller candidate states.
- Existing CDC loader integrated with real progress, commit and full readback.
- Cancellation, errors, history, diagnostics, and separately reported game feedback.
- Version-specific Switch 2 guide, offline TOTK reference, portable EXE, sources,
  licenses, and preserved 0.1.1/0.1.2 recovery firmware.
