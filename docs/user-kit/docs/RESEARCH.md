# Initial sources and hypotheses — 30 October 2026

This translated historical note records the initial unknowns, not current status.

- **Original Pico:** RP2040, USB 1.1 host/device, 264 KiB SRAM, 2 MiB flash, no
  Bluetooth. A working Switch 2 controller/NFC implementation still had to be shown.
- **PicoSwitch2 v2.5.0:** published Pico W/Pico 2 W code with Pro Controller 2 and
  Virtual Amiibo release claims. Porting and success without wireless hardware
  had not been established.
- **Switch 2 USB:** partially documented public descriptors and commands.
  Recognition and NFC acceptance of the new non-W fork were unknown.
- **Amiibo storage:** local-library behavior existed for W hardware. A non-Bluetooth
  configuration channel, safe persistence, and actual TOTK scan still needed work.

## References

- https://github.com/notsosaelin/PicoSwitch2/releases/tag/v2.5.0
- https://github.com/notsosaelin/PicoSwitch2/releases
- https://raw.githubusercontent.com/notsosaelin/PicoSwitch2/v2.5.0/README.md
- https://raw.githubusercontent.com/notsosaelin/PicoSwitch2/v2.5.0/AGENTS.md
- https://raw.githubusercontent.com/notsosaelin/PicoSwitch2/v2.5.0/STATUS.md
- https://raw.githubusercontent.com/notsosaelin/PicoSwitch2/v2.5.0/CMakeLists.txt
- https://github.com/ndeadly/switch2_controller_research/blob/master/commands.md
- https://github.com/ndeadly/switch2_controller_research/blob/master/descriptors.md
- https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html
- https://github.com/joshbirnholz/switch2-pico

Use the specified tag as the porting reference; main and older README claims can
differ. Release 2.0.0 wireless-board hardware reports are not non-W evidence.
Check dependencies and licenses at the copied version.

The minimal architecture is Windows configuration over the Pico USB port, then
unplug/replug to Switch 2 with one stored tag. Radio NFC writing is neither
necessary nor possible on the bare Pico.

The key uncertainty was whether the Pro Controller 2 personality and NFC exchanges
required behavior absent from the available port. Measure real compatibility;
do not announce hardware success from simulation.
