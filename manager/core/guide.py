def instructions(version):
    base=["Your amiibo was saved on the Pico and read back byte for byte.",
          "Disconnect the Pico from the PC. It cannot be connected to two USB hosts.",
          "Connect it to your Switch 2 dock using a USB data cable.",
          "Open your game, enable its amiibo feature, and start scanning."]
    if version=="0.2.0":
        base += ["If the console asks for A, quickly tap BOOTSEL twice.",
                 "While the game waits for a scan, briefly tap BOOTSEL once and wait about half a second.",
                 "Hold BOOTSEL for five seconds to select the next tag, wrapping to the first. The new tag stays ejected.",
                 "The LED confirms a change, not a tag name.",
                 "Release a 2-to-5-second hold to enter configuration."]
    elif version in ("0.1.1","0.1.2"):
        base += ["If the console asks for A, quickly tap BOOTSEL twice.",
                 "While the game waits for a scan, briefly tap BOOTSEL once and wait about half a second.",
                 "Another short tap removes the tag. A two-second hold opens PC configuration."]
        if version=="0.1.1":base.append("On 0.1.1 only, holding for about one second sends L+R. This gesture is absent from 0.1.2.")
    elif version=="0.1.0":
        base += ["Version 0.1.0: a short tap presents or removes the tag; a one-second hold sends L+R.",
                 "BOOTSEL cannot send A on this version. Use your regular controller to confirm."]
    else:
        base += ["Unknown firmware version: do not assume 0.1.1 or 0.1.2 gestures. Return to PC configuration to identify the USB version."]
    base.append("The Manager cannot observe the Switch 2. Confirm the scan result yourself below.")
    return base
