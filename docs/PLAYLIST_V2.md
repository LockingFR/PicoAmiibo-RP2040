# Experimental bilingual Manager and multi-tag firmware

The user explicitly authorized this extension after the working single-tag
prototype: choose French/English, check multiple tags, load the checked set,
advance through it with a five-second hold, replace it with one tag later,
and open the Load page by clicking the card body.

Development branch: feature/bilingual-playlist. Stable main, 0.1.1/0.1.2 UF2s,
the current application and private profile remain preserved. No automatic flash.

## Gesture contract for the new firmware

- Short tap: present/remove, as before.
- Double tap: A, as before.
- In controller mode, release a hold between two and five seconds: configuration.
- Hold for five seconds: advance once, wrap after the last tag; release before
  advancing again. A five-second hold must never first enter CDC at two seconds.
- In CDC, a two-second hold exits configuration; an already handled press cannot
  also advance a tag after switching USB personality.
- Changing tags first removes the old tag. The next tag stays ejected until a
  deliberate short tap. The LED confirms change, not the tag name.

## Storage and protocol

Up to 64 NTAG215 images fit a bounded playlist. Two new 64 KiB banks are reserved
immediately before the existing two 4 KiB single-tag banks. Old single-tag banks
are read as a fallback and never erased by playlist saves.

The inactive bank receives header and data pages before its final commit marker.
CRC, count, generation, and every embedded slot are validated. A failed/cancelled
upload before commit must not replace the previous committed list. Cancellation
after commit can leave the new list stored but unverified; reconnect and inspect.
Active index starts at zero
after boot and advances in RAM without writing flash on each button press.

Legacy INFO/LOAD/READ/EXIT remain usable. CAPS explicitly advertises playlist
support. BATCH uploads a bounded sequence of existing 608-byte slot records;
READ index supports per-tag byte-for-byte destination verification. Single LOAD
replaces the whole playlist with one tag on the new firmware.

Older firmware must never receive a simulated multi-upload success. The Manager
requires the capability response before enabling/sending a playlist.

## Qualification

Host storage/input/protocol tests, interruption simulation, ARM build/memory audit,
Python transport tests and GUI tests are required. Actual Pico/Switch 2 use of
this new firmware remains UNTESTED until a user-operated physical test.

## Reproducible physical test (user-operated)

Keep the working 0.1.1 UF2 and its original tag available for rollback. Close the
old Manager before opening the preview against the same private library.

1. Manually install the separate empty 0.2.0 UF2 on the correct Pico RPI-RP2
   drive. The old single-tag sectors are preserved; confirm the old tag is still
   readable in CDC before writing a playlist. No console/saves modification.
2. In Diagnostics, choose English or Français. Restart the app and verify the
   preference. In Library, click a card body: it opens Load directly. Return and
   click just its checkbox: it queues the tag without leaving Library.
3. Check two or three distinct owned files, click Load checked tags, confirm
   displayed order/COM port, then Load checked playlist. Require a verified
   readback of every tag. Record version, count, CRC/result, without sharing data.
4. On Switch 2, the first tag starts ejected. Open the game scan and short-tap
   BOOTSEL to present. Remove it after the result. Hold BOOTSEL about five seconds
   and release; allow about one more second for removal/draining, then the LED
   pulses twice. Open the next scan and short-tap to present the next tag. Repeat
   through the last to confirm wrap. An extended hold advances only once.
5. Unplug/replug: the first tag is active again, ejected. Return to PC, release
   BOOTSEL after two seconds but before five to enter CDC, and confirm count.
6. Click a single card, use Single amiibo (replace playlist), load/verify it,
   reconnect and confirm count=1. Long holds must no longer change the tag.
7. Report exact success/error at each stage. USB/readback success is separate
   from game recognition. Game rewards remain random and subject to game rules.

If needed, deliberately reinstall the preserved 0.1.1 UF2. It reads the unchanged
legacy single-tag banks, not the new list. Reinstalling 0.2.0 later restores its
last committed playlist. Neither installation alone erases these data regions.
