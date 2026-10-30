"""Reproduce the adapted Pro Controller 2 identity/handshake from v2.5.0."""
from pathlib import Path
import subprocess
import sys
from import_upstream import REV, ROOT

upstream = Path(sys.argv[1]).resolve()
source = subprocess.check_output(["git", "-C", str(upstream), "show", f"{REV}:src/switch_pro2/switch_pro2.c"], text=True)
def between(a, b):
    return source[source.index(a):source.index(b)]

descriptors = between("static const uint8_t ns2_device_desc[]", "//--------------------------------------------------------------------+\n// Factory")
# Keep the minimal HID + vendor personality; no audio or other personalities.
start = descriptors.index("#else  // NS2_AUDIO")
end = descriptors.index("#endif", start)
descriptors = descriptors[:start] + descriptors[end + len("#endif"):]
descriptors = descriptors.replace("#ifndef NS2_AUDIO\n", "")
factory = between("#define FACTORY_BASE", "//--------------------------------------------------------------------+\n// Command protocol")
factory = factory.replace("config_get_body_color(body_color);", "memcpy(body_color, (const uint8_t[]){0x70, 0x70, 0x70}, 3);")
dispatch = between("    switch (id) {\n        case 0x03", "    uint16_t response_length =")
dispatch = dispatch.replace("                    ns2_wake_pairing_stage(&c[8], n - 8, 0x2069, &a[3]);", "                    /* Wired-only: no wake identity or radio state. */")
dispatch = dispatch.replace("                ns2_wake_pairing_commit();", "                /* USB pairing only; no radio. */")
dispatch = dispatch.replace("report_set_player_leds(0, c[8]);", "(void)c[8];")
header = '''/* Adapted from PicoSwitch2 v2.5.0, Apache-2.0. See docs/PROVENANCE.md.
 * No radio dependencies. Descriptors and bootstrap replies retain upstream bytes.
 */
#include <string.h>
#include "pa_identity.h"
#include "ns2_pairing_crypto.h"
#include "ns2_firmware_profile.h"
static uint8_t ns2_report_id = 0x09;
static bool ns2_streaming;
static bool ns2_imu_enabled;
'''
wrapper = '''
void pa_identity_init(void) {
    ns2_report_id = 0x09;
    ns2_streaming = false;
    ns2_imu_enabled = false;
    memset(ns2_ltk, 0, sizeof(ns2_ltk));
    ns2_factory_init();
}
bool pa_identity_streaming(void) { return ns2_streaming; }
uint8_t pa_identity_report_id(void) { return ns2_report_id; }
const uint8_t *pa_identity_ep0(uint8_t request, size_t *size) {
    if (request == 3) { *size = sizeof(ns2_ctrl_identity); return ns2_ctrl_identity; }
    if (request == 2) { *size = sizeof(ns2_ctrl_info); return ns2_ctrl_info; }
    *size = 0;
    return NULL;
}
size_t pa_identity_command(const uint8_t *c, size_t n, uint8_t r[128]) {
    if (!c || !r || n < 8 || n != 8u + ((size_t)c[4] << 8) + c[5] ||
        c[1] != 0x91 || c[2] != 0) return 0;
    const uint8_t id = c[0], transport = c[2], sub = c[3];
    if ((id == 0x02 && n < 16) ||
        (id == 0x15 && (sub == 2 || sub == 4) && n < 25) ||
        (id == 0x03 && sub == 0x0a && n < 9)) return 0;
    memset(r, 0, 128);
    r[0] = id; r[1] = 1; r[2] = transport; r[3] = sub; r[5] = 0xf8;
    uint8_t *d = r + 8;
    uint16_t dl = 0;
'''
(ROOT / "src/identity.c").write_text(header + descriptors + factory + wrapper + dispatch + "    return 8u + dl;\n}\n", encoding="utf-8")
print("Derived wired USB identity and handshake, with payload bounds checks")
