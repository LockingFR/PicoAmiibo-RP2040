# PicoAmiibo Manager 1.2.0-preview.1 — Windows guide

## Languages and checked playlists

Choose **Diagnostics → Preferences and local data → Language → English/Français**.
The window changes immediately and remembers the setting. This changes displayed
text, not private files or protocol bytes.

Click an amiibo card body to go straight to **Load** with that tag selected.
Click its checkbox to queue it without changing pages. **Select all shown** checks
the current filtered results; **Clear checked** empties the queue. The Load page
lists the queue in checking order, up to 64 tags; nothing is silently truncated.
Click **Load checked tags**, confirm the Pico, then **Load checked playlist**.
Every tag is read back and compared. Cancelling after flash commit can leave the
new list stored but not verified; reconnect and inspect it before retrying.

Multiple tags require firmware **0.2.0**. Older firmware supports a single tag
and the app blocks a multi-tag transfer. The app never flashes firmware.
The separate 0.2.0 preview requires physical qualification; see
[the physical test plan](docs/PLAYLIST_V2.md).

On 0.2.0: short tap presents/removes; double tap sends A. Hold BOOTSEL for about
five seconds to advance **once**, release, then allow about one second for the
removal interval/USB drain and two confirmation LED pulses. Short-tap to present
the new tag. Repeat to wrap to the first. Boot always selects the first, ejected.
To enter PC configuration, release after two seconds but **before five**.

To restore one tag, click its card or choose **Single amiibo (replace playlist)**,
then load and verify it. That operation replaces the whole new-firmware list.

## Open the portable application

Extract the entire Windows x64 ZIP from GitHub Releases. Run
`PicoAmiibo-Manager.exe` and keep `_internal` beside it. No system Python is needed.
The prototype executable is unsigned. The Manager never installs firmware.

The first launch has an empty library. Files, preferences, history, and optional
public-image cache are stored in `%LOCALAPPDATA%/PicoAmiiboManager`. Updating or
moving the application folder does not overwrite that private profile.

## First physical test

1. Keep the working firmware already installed on the Pico. The Manager does not
   require changing 0.1.1 to 0.1.2.
2. Connect a USB data cable to the PC. After normal startup, hold BOOTSEL for two
   seconds and release. This opens CDC configuration. Holding BOOTSEL before
   connecting power instead opens the RPI-RP2 recovery drive.
3. Choose **Library → Import** and select your raw 540/572-byte amiibo files.
   Duplicates are skipped. An unidentified file can still be loaded.
4. Click a card to open **Load** directly, and confirm the correct COM port.
   Multiple Pico devices require an explicit selection.
5. Click **Load and verify**. Wait for **Saved and verified on the Pico**.
   The loader confirms commit, reads back every byte, compares it, and checks
   the final status. A transmit progress bar alone is not this confirmation.
6. Open the Switch 2 guide, disconnect from the PC, and connect the Pico to the
   console/dock using the setup that has worked with your controller.
7. Start the in-game amiibo scan. Briefly tap BOOTSEL to present the stored tag;
   another short tap removes it. On 0.1.1/0.1.2, two quick taps send A. A regular
   Pro Controller 2 can also confirm A. The normal guide does not require L+R.
8. Return to the PC to report whether the game recognized the scan. This is your
   observation, not automatic console telemetry.

Record the displayed firmware version, COM port, size/CRC and readback result,
then the exact in-game result or error. Do not send the tag dump.
To check persistence, reconnect to the PC, enter configuration again, and use
**Diagnostics → Test communication** to read the stored record.

## TOTK rewards

Cards show a **possible reward** summary. **Selected amiibo rewards** opens the
matching reference. **Explore all TOTK rewards** works even with an empty library.
Search ignores case/accents and includes item names, for example Epona or Dusk Bow.

**Diagnostics → Preferences and local data → Show TOTK rewards** is enabled by
default. Disable it to hide reward summaries/buttons and remove rewards from
library search. The preference survives closing the app.

The offline catalog contains 36 profiles: 33 specific figures, two internal
generic Link/Zelda tables, and one fallback for other amiibo. All 33 specific
figure IDs are mapped, including Mineru using a pinned public TagMo identifier.
Unknown IDs are not assigned an exclusive reward.

Epona is associated with the relevant Link Twilight Princess and Super Smash
Bros. figures. Other reward entries include fabric, armor, equipment, and material
pools. Progression and game-version conditions are shown in the detailed list.
Numbers are relative weights within a selected table, not guaranteed per-scan
probabilities. Previously obtained items can affect the pool.

For the Dusk Bow, use Zelda Super Smash Bros. and satisfy the Depths progression
condition. Receiving different loot does not by itself mean the USB transfer
failed. The Manager cannot choose loot or read your save.

## Optional images and offline use

Zelda names and reward references are bundled as public metadata. Artwork is not.
Enable online metadata in Diagnostics and click **Refresh metadata** if desired.
Only a public catalog and public images are fetched. Up to 20 library images are
cached per refresh; other cards use the original NFC fallback icon. No private
tag data is uploaded. Disabling network metadata keeps the existing cache usable.

## Troubleshooting

- **Pico not detected:** try a data-capable cable, wait for normal startup, then
  hold BOOTSEL for two seconds. Close other tools holding the same COM port.
- **Controller mode, unidentified:** the VID/PID can also belong to a retail
  Pro Controller 2. Enter CDC on your Pico to establish its identity.
- **BOOTSEL/RPI-RP2:** this is the firmware bootloader, not a place to copy amiibo files.
- **Interrupted load or corrupt readback:** the operation is not verified.
  Reconnect and read the stored record before retrying. A commit could have
  completed before the interruption; the app cannot promise the previous record.
- **Saved but controller return not confirmed:** verified stored data remains
  valid; disconnect/reconnect before using the console.
- **Format verified but game rejects the tag:** size/BCC/CRC do not establish
  cryptographic authenticity. Check the original file and version-specific guide.

Recovery is manual: disconnect, hold BOOTSEL while connecting to the PC, confirm
the correct RPI-RP2 drive, then copy the chosen empty UF2. A firmware UF2 update
does not necessarily erase the separately reserved tag banks.

## Development and verification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_manager.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/test_manager.ps1 -Frozen
powershell -NoProfile -ExecutionPolicy Bypass -File tools/test.ps1
```

The Manager build uses a private virtual environment, pinned dependencies, a
clean Git revision, and a required smoke result bound to the exact EXE SHA256.
The smoke test uses an isolated artificial profile with USB disabled and renders
14 EN/FR views, including checked playlists. Archive timestamps mean byte-for-byte
ZIP reproducibility is not promised. Preview outputs are separate from stable builds.

The source archive supports review and `python -m manager` with the pinned
requirements. A fresh source checkout can build the application without local
recovery UF2 backups; download the separately labeled recovery images from Releases
if needed. No application build step flashes a board.

Sources and licenses: `MANAGER_ARCHITECTURE.md`, `MANAGER_REVIEW_CHATGPT.md`,
`THIRD_PARTY_NOTICES.md`, and the packaged `licenses` directory.
Qt/PySide6 libraries are dynamically loaded and replaceable; application source
is supplied under Apache-2.0.
