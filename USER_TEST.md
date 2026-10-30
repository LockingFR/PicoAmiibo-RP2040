# Physical firmware test — user-operated

The user already reported Epona after 0.1.1. The 0.1.2 source removes only the
BOOTSEL L+R gesture and still needs its own console test. Updating the desktop
Manager does not require installing 0.1.2.

## Install only when deliberately testing new firmware

1. Keep your previous UF2 for recovery. The tools do not automatically read or
   back up the complete firmware currently installed on the board.
2. Verify the chosen empty UF2 against its release manifest using
   `Get-FileHash -Algorithm SHA256`.
3. Connect the correct original Pico while holding BOOTSEL. Confirm its RPI-RP2
   drive, then manually copy the UF2. No script performs this step.
4. Disconnect/reconnect normally. Separate tag banks may retain a previously
   stored record; the tag starts ejected. This is not a storage-wipe operation.

## Load a tag from Windows

1. After normal startup, hold BOOTSEL for two seconds to enter CDC configuration.
2. Use the Manager Library → Import → Load and verify, or the CLI:

   ```powershell
   python tools/list_ports.py
   python tools/load_amiibo.py --port COM7 /path/to/your-amiibo.bin
   ```

3. Select the correct port and your original 540/572-byte raw NTAG215 file.
   Loading replaces the active tag record. Wait for full byte-for-byte readback.
4. Reconnect to the PC, enter CDC again, and inspect persistence:

   ```powershell
   python tools/load_amiibo.py --port COM7 --info
   ```

5. Confirm loaded=1, expected size, and the same CRC. Do not deliberately interrupt
   physical flash programming during this first qualification.

## Console recognition and scan

1. Move the USB data cable from PC to the Switch 2 dock/compatible port.
2. Record the detected controller identity and any console message. Firmware
   controller-updating commands are not implemented.
3. If A is required, quickly tap BOOTSEL twice on 0.1.1/0.1.2, then wait. The
   180 ms A pulse does not present the tag. A regular controller can also confirm.
4. Open TOTK and its amiibo scan with your regular controller.
5. Briefly tap BOOTSEL once, then wait about half a second. The tag is presented.
   A solid LED or short activity gaps are indicators, not proof of game acceptance.
6. Briefly tap again to remove the tag. Do not assume a lack of response is a
   rejected file: controller/NFC routing can also matter.
7. Record the exact game message and reward separately. The reward depends on the
   figure, progression, and random drop rules. The app does not read or modify saves.

Console NFC writes are rejected. If a write is required and blocks the game, record
the result rather than claiming success or altering the save.

## Report and recovery

Report firmware SHA256/version, Pico model, COM state, verified transfer,
persistence readback, controller detection, LED behavior, and exact game result.
Do not send a dump, authentication key, or save.

If the board becomes unusable, disconnect it, hold BOOTSEL while reconnecting to
the PC, confirm the correct RPI-RP2 drive, and manually restore the previous UF2.
The ROM bootloader is independent of this application.
