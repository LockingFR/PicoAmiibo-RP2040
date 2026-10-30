/* Adapted from PicoSwitch2 v2.5.0, Apache-2.0. See docs/PROVENANCE.md.
 * No radio dependencies. Descriptors and bootstrap replies retain upstream bytes.
 */
#include <string.h>
#include "pa_identity.h"
#include "ns2_pairing_crypto.h"
#include "ns2_firmware_profile.h"
static uint8_t ns2_report_id = 0x09;
static bool ns2_streaming;
static bool ns2_imu_enabled;
static const uint8_t ns2_device_desc[] = {
    0x12,        // bLength
    0x01,        // bDescriptorType (Device)
    0x00, 0x02,  // bcdUSB 2.00
    0xEF,        // bDeviceClass (Misc, IAD composite)
    0x02,        // bDeviceSubClass
    0x01,        // bDeviceProtocol
    0x40,        // bMaxPacketSize0 64
    0x7E, 0x05,  // idVendor 0x057E (Nintendo)
    0x69, 0x20,  // idProduct 0x2069 (Switch 2 Pro Controller)
    0x10, 0x02,  // bcdDevice 2.10 â€” deliberately NOT the real 2.00. Hardware A/B settled it:
                 // diag3 (2.10) and diag4 (2.00) BOTH stall the console at the same point, so the
                 // console does NOT gate on bcdDevice. On PC, though, 2.00 collides with the user's
                 // retail PC2 (also 2.00) in Windows' WinUSB cache (key = VID+PID+bcdDevice) â†’ WinUSB
                 // won't bind â†’ no Steam debug loop. 2.10 is a distinct key: console-neutral AND it
                 // preserves the PC/WinUSB proxy we use to exercise the vendor protocol.
    0x01,        // iManufacturer
    0x02,        // iProduct
    0x03,        // iSerialNumber
    0x01,        // bNumConfigurations
};

static const char *ns2_strings[] = {
    (const char[]){0x09, 0x04},   // 0: language id (en-US)
    "Nintendo",                    // 1: manufacturer
    "Switch 2 Pro Controller",     // 2: product
    "00",                          // 3: serial number
};

// HID report descriptor (97 bytes) â€” exact from the real PC2.
static const uint8_t ns2_report_desc[] = {
    0x05, 0x01,        // Usage Page (Generic Desktop Ctrls)
    0x09, 0x05,        // Usage (Game Pad)
    0xA1, 0x01,        // Collection (Application)
    0x85, 0x05,        //   Report ID (5)
    0x05, 0xFF,        //   Usage Page (Vendor 0xFF)
    0x09, 0x01,        //   Usage (0x01)
    0x15, 0x00,        //   Logical Minimum (0)
    0x26, 0xFF, 0x00,  //   Logical Maximum (255)
    0x95, 0x3F,        //   Report Count (63)
    0x75, 0x08,        //   Report Size (8)
    0x81, 0x02,        //   Input (Data,Var,Abs)
    0x85, 0x09,        //   Report ID (9)
    0x09, 0x01,        //   Usage (0x01)
    0x95, 0x02,        //   Report Count (2)
    0x81, 0x02,        //   Input (Data,Var,Abs)
    0x05, 0x09,        //   Usage Page (Button)
    0x19, 0x01,        //   Usage Minimum (0x01)
    0x29, 0x15,        //   Usage Maximum (0x15)  -> 21 buttons
    0x25, 0x01,        //   Logical Maximum (1)
    0x95, 0x15,        //   Report Count (21)
    0x75, 0x01,        //   Report Size (1)
    0x81, 0x02,        //   Input (Data,Var,Abs)
    0x95, 0x01,        //   Report Count (1)
    0x75, 0x03,        //   Report Size (3)
    0x81, 0x03,        //   Input (Const) -> 3-bit pad
    0x05, 0x01,        //   Usage Page (Generic Desktop Ctrls)
    0x09, 0x01,        //   Usage (Pointer)
    0xA1, 0x00,        //   Collection (Physical)
    0x09, 0x30,        //     Usage (X)
    0x09, 0x31,        //     Usage (Y)
    0x09, 0x33,        //     Usage (Rx)
    0x09, 0x35,        //     Usage (Rz)
    0x26, 0xFF, 0x0F,  //     Logical Maximum (4095)
    0x95, 0x04,        //     Report Count (4)
    0x75, 0x0C,        //     Report Size (12)
    0x81, 0x02,        //     Input (Data,Var,Abs)
    0xC0,              //   End Collection
    0x05, 0xFF,        //   Usage Page (Vendor 0xFF)
    0x09, 0x02,        //   Usage (0x02)
    0x26, 0xFF, 0x00,  //   Logical Maximum (255)
    0x95, 0x34,        //   Report Count (52)
    0x75, 0x08,        //   Report Size (8)
    0x81, 0x02,        //   Input (Data,Var,Abs)
    0x85, 0x02,        //   Report ID (2)
    0x09, 0x01,        //   Usage (0x01)
    0x95, 0x3F,        //   Report Count (63)
    0x91, 0x02,        //   Output (Data,Var,Abs)
    0xC0,              // End Collection
};
_Static_assert(sizeof(ns2_report_desc) == 97, "PC2 HID report descriptor must be 97 bytes");

// Configuration descriptor. Two build variants selected by NS2_AUDIO:
//   Option B (default off): IF0 HID + IF1 vendor bulk only (80 B, 2 interfaces).
//   Option A (NS2_AUDIO):   adds the real PC2's 3 audio interfaces (268 B, 5 IF),
//                           serviced by the PC2-specific UAC1 driver below.
// iConfiguration / iInterface are 0 (the retail strings 4/5/6 are unknown).
#define NS2_CONFIG_LEN 80
static const uint8_t ns2_config_desc[] = {
    0x09, 0x02, (NS2_CONFIG_LEN & 0xFF), (NS2_CONFIG_LEN >> 8), 0x02, 0x01, 0x00, 0xC0, 0xFA,
    // IAD + Interface 0: HID
    0x08, 0x0B, 0x00, 0x01, 0x03, 0x00, 0x00, 0x00,
    0x09, 0x04, 0x00, 0x00, 0x02, 0x03, 0x00, 0x00, 0x00,
    0x09, 0x21, 0x11, 0x01, 0x00, 0x01, 0x22, 0x61, 0x00,  // HID desc, report len 97
    0x07, 0x05, 0x81, 0x03, 0x40, 0x00, 0x01,  // EP 0x81 interrupt IN, bInterval 1 = 1000Hz FS max
    0x07, 0x05, 0x01, 0x03, 0x40, 0x00, 0x01,  // EP 0x01 interrupt OUT, bInterval 1
    // IAD + Interface 1: vendor bulk
    0x08, 0x0B, 0x01, 0x01, 0xFF, 0x00, 0x00, 0x00,
    0x09, 0x04, 0x01, 0x00, 0x02, 0xFF, 0x00, 0x00, 0x00,
    0x07, 0x05, 0x02, 0x02, 0x40, 0x00, 0x00,  // EP 0x02 bulk OUT
    0x07, 0x05, 0x82, 0x02, 0x40, 0x00, 0x00,  // EP 0x82 bulk IN
};

_Static_assert(sizeof(ns2_config_desc) == NS2_CONFIG_LEN, "config descriptor size mismatch");

const uint8_t *ns2_device_descriptor(void) { return ns2_device_desc; }
const uint8_t *ns2_config_descriptor(void) { return ns2_config_desc; }
const uint8_t *ns2_hid_report_descriptor(void) { return ns2_report_desc; }
const char **ns2_string_table(size_t *count) {
    *count = sizeof(ns2_strings) / sizeof(ns2_strings[0]);
    return ns2_strings;
}

#define FACTORY_BASE 0x13000u
#define FACTORY_SIZE 0x160u
static uint8_t factory[FACTORY_SIZE];

// Identity + info blocks the console fetches over EP0 vendor control BEFORE it will
// touch the bulk command channel (verified from ndeadly's USB capture, PC2 = device 7;
// see tud_vendor_control_xfer_cb). ns2_ctrl_identity is the first 64 B of factory memory
// (0x13000: 01 00, serial, VID, PID, 01 06 01, colours) with a 0xFF tail; built in
// ns2_factory_init once `factory` is populated. ns2_ctrl_info is the fixed 16-B reply to
// vendor request 0x02 (firmware/version + a per-unit id). The opaque middle and
// per-unit bytes remain verbatim from our capture; only the documented leading
// firmware triplet advances to the updated retail version.
static uint8_t ns2_ctrl_identity[64];
static uint8_t ns2_ctrl_info[16];

// Command 0x10/0x01 response payload:
// firmware[3], controller type, Bluetooth patch[3], pad, DSP[3], pad.
static uint8_t ns2_firmware_info[12];

static void fac(uint32_t addr, const uint8_t *d, size_t n) {
    uint32_t o = addr - FACTORY_BASE;
    if (o + n <= FACTORY_SIZE) memcpy(&factory[o], d, n);
}

static void ns2_factory_init(void) {
    static const uint8_t unit_id[6] = {0x9E, 0x2B, 0xAB, 0xAB, 0xA9, 0x3C};
    static const uint8_t blk[40] = {
        0x01, 0xAD, 0xD9, 0x9A, 0x55, 0x56, 0x65, 0xA0, 0x00, 0x0A, 0xA0, 0x00, 0x0A, 0xE2,
        0x20, 0x0E, 0xE2, 0x20, 0x0E, 0x9A, 0xAD, 0xD9, 0x9A, 0xAD, 0xD9, 0x0A, 0xA5, 0x50,
        0x0A, 0xA5, 0x50, 0x2F, 0xF6, 0x62, 0x2F, 0xF6, 0x62, 0x0A, 0xFF, 0xFF};
    memset(factory, 0, sizeof(factory));
    ns2_firmware_build_ep0_info(ns2_ctrl_info, unit_id);
    ns2_firmware_build_command_info(0x02, ns2_firmware_info);  // 0x02 = Pro Controller
    fac(0x13000, (const uint8_t[]){0x01, 0x00}, 2);
    fac(0x13002, (const uint8_t[]){0x48, 0x45, 0x4A, 0x37, 0x31, 0x30, 0x30, 0x31, 0x31, 0x32,
                                   0x31, 0x32, 0x34, 0x37, 0x00, 0x00}, 16);  // serial
    fac(0x13012, (const uint8_t[]){0x7E, 0x05}, 2);  // VID
    fac(0x13014, (const uint8_t[]){0x69, 0x20}, 2);  // PID
    fac(0x13016, (const uint8_t[]){0x01, 0x06, 0x01}, 3);
    uint8_t body_color[3];
    memcpy(body_color, (const uint8_t[]){0x70, 0x70, 0x70}, 3);
    fac(0x13019, body_color, sizeof(body_color));          // configured body colour
    fac(0x1301C, (const uint8_t[]){0xA0, 0xA0, 0xA0}, 3);  // button colour
    fac(0x1301F, (const uint8_t[]){0xE6, 0xE6, 0xE6}, 3);  // highlight
    fac(0x13022, (const uint8_t[]){0x32, 0x32, 0x32}, 3);  // grip
    fac(0x13040, (const uint8_t[]){0x3B, 0xE0, 0xD3, 0x41, 0xC6, 0x60, 0x6A, 0xBC, 0x4D, 0xD7,
                                   0xA2, 0xBB, 0x71, 0x1E, 0xDD, 0x37}, 16);
    // 0x13060..0x1307F (32 B) reads back erased/unprogrammed (0xFF) on a real unit, not the
    // previously-hardcoded `4C 09 00 00` (source unknown/unannotated). Confirmed by TWO
    // independent real-capture sources (2026-07-12): ndeadly's raw USB capture (a 32-byte read
    // at this address, all 0xFF) and Dycool/NS-PC-Control's own factory-table comment ("reads
    // back erased (0xFF) on the real unit â€” Captured read: addr=0x13060 len=0x20"). The
    // factory[] array default-zero-fills anything not explicitly populated (see the memset
    // above), so this region must be set to 0xFF explicitly, not just left unpopulated.
    fac(0x13060, (const uint8_t[]){0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                                   0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                                   0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                                   0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF}, 32);
    fac(0x13080, blk, 40);
    fac(0x130A8, (const uint8_t[]){0xB3, 0x67, 0x83, 0x2E, 0x66, 0x5E, 0x3A, 0x06, 0x5F}, 9);  // L stick cal
    fac(0x130C0, blk, 40);
    fac(0x130E8, (const uint8_t[]){0x2C, 0x08, 0x84, 0xD1, 0x65, 0x63, 0x2A, 0x26, 0x62}, 9);  // R stick cal
    // Magnetometer bias (zero, unit never calibrated) + accelerometer bias, both float32 x,y,z â€”
    // decoded 2026-07-10 (docs/switch2/report-0x09-motion.md "Factory motion calibration") from
    // this repo's own SPI dump but never wired into the served memory table until 2026-07-12,
    // when a fresh independent decode of a real console-side USB capture (ndeadly's
    // rumble-procon-gccon.pcapng, a DIFFERENT physical unit) confirmed the console actually reads
    // this exact address (0x02/04, len 0x18) during init and expects non-zero data there â€” this
    // repo was previously returning zero-fill (memset default) for any read at 0x13100, a real
    // gap between documented-and-decoded vs. actually-served. Exact bytes are this repo's own
    // unit's SPI dump (`dumps/SPI/2069_spi_dump_2026-07-10_1422.bin`), for internal consistency
    // with the surrounding factory-block entries above.
    fac(0x13100, (const uint8_t[]){0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                   0x00, 0x00, 0xC1, 0xF9, 0x23, 0x3E, 0x51, 0xAC, 0x8C, 0xBD,
                                   0x21, 0x0F, 0x26, 0x41}, 24);
    fac(0x13140, (const uint8_t[]){0x00, 0xD7, 0xA3, 0xBC, 0x41, 0xD7, 0xA3, 0xBC, 0x41}, 9);

    // Identity block for the EP0 vendor 0x03 request = first 0x25 B of factory (01 00,
    // serial, VID, PID, 01 06 01, colours) then 0xFF fill to 64 (matches the capture).
    memset(ns2_ctrl_identity, 0xFF, sizeof(ns2_ctrl_identity));
    memcpy(ns2_ctrl_identity, factory, 0x25);
}

static void ns2_mem_read(uint8_t subcommand, uint32_t addr, uint8_t len, uint8_t *out) {
    ns2_firmware_diagnostics_record_read(subcommand, addr, len);
    for (uint8_t i = 0; i < len; i++) {
        uint32_t a = addr + i;
        if (a >= FACTORY_BASE && a < FACTORY_BASE + FACTORY_SIZE)
            out[i] = factory[a - FACTORY_BASE];
        else if (a == 0x1FA000)
            out[i] = 0x00;  // Bluetooth pairing entry count = 0 (no bonds over USB)
        else {
            // Sparse, observed post-update state supplied by the selected profile.
            if (!ns2_firmware_profile_flash_byte(a, &out[i]))
                out[i] = 0xFF;  // uninitialised flash reads as 0xFF
        }
    }
}

//--------------------------------------------------------------------+
// Bluetooth-pairing crypto (the console runs this over USB during first pairing).
// Verified against ndeadly's capture:
//   LTK        = reverse(A1) XOR reverse(B1)      (A1 from 0x15/04, B1 public)
//   B2(onwire) = AES128_ECB(LTK, reverse(A2))     (A2 from 0x15/02 challenge)
// The actual AES-128/rev16/LTK-derivation math was extracted 2026-07-13 into the shared,
// host-tested src/ns2_pairing_crypto.c (see include/ns2_pairing_crypto.h) so switch_gc.c can
// also perform real pairing crypto instead of placeholder bytes -- this file just keeps its own
// session-scoped key state and the two thin wrappers below, byte-for-byte identical behavior to
// before the extraction (verified: tools/test_ns2_pairing_crypto.c's FIPS-197 vector + this
// file's own unchanged hardware-validated pairing history).
//--------------------------------------------------------------------+

// Public device key B1 (constant), used to derive the LTK with the console's A1.
static const uint8_t ns2_device_key_b1[16] = {
    0x5C, 0xF6, 0xEE, 0x79, 0x2C, 0xDF, 0x05, 0xE1,
    0xBA, 0x2B, 0x63, 0x25, 0xC4, 0x1A, 0x5F, 0x10};
static uint8_t ns2_ltk[16];

// 0x15/04: LTK = reverse(A1) XOR reverse(B1).
static void ns2_pair_set_ltk(const uint8_t *a1_wire) {
    ns2_pairing_derive_ltk(a1_wire, ns2_device_key_b1, ns2_ltk);
}

// 0x15/02: B2(wire) = AES128_ECB(LTK, reverse(A2)).
static void ns2_pair_challenge(const uint8_t *a2_wire, uint8_t *b2_wire) {
    ns2_pairing_challenge(ns2_ltk, a2_wire, b2_wire);
}


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
    switch (id) {
        case 0x03:  // Initialisation
            if (sub == 0x0D) { d[0] = 0x01; dl = 4; }        // Init USB
            else if (sub == 0x03) { d[0] = 0x01; dl = 4; }   // Enable USB HID reports
            else if (sub == 0x0A) {  // Select input report (0x05 or 0x09) -> begin streaming
                if (c[8] == 0x05 || c[8] == 0x09) ns2_report_id = c[8];
                ns2_streaming = true;
                dl = 0;
            }
            else dl = 0;
            break;
        case 0x07:  // first-init command
            d[0] = 0x00; dl = 1;
            break;
        case 0x16:  // unknown, 24 zero bytes
            dl = 24;
            break;
        case 0x15:  // Bluetooth pairing (run over USB)
            if (sub == 0x01) {  // exchange addresses -> return our controller BD_ADDR
                // Same 6 bytes as the EP0 info block tail (ns2_ctrl_info) so our advertised
                // controller address is self-consistent, like the real PC2 (capture frame 463).
                static const uint8_t a[] = {0x01, 0x04, 0x01, 0x9E, 0x2B, 0xAB, 0xAB, 0xA9, 0x3C};
                memcpy(d, a, sizeof(a));
                dl = sizeof(a);
                // The request contains the console address(es) needed by the
                // Switch 2 wake advertisement. Stage now, but persist only if
                // the console later finalises this pairing with 0x15/03.
                if (n >= 8) {
                    /* Wired-only: no wake identity or radio state. */
                }
            } else if (sub == 0x02) {  // confirm LTK: B2(wire) = AES128(LTK, rev(A2))
                d[0] = 0x01;
                ns2_pair_challenge(&c[9], &d[1]);  // A2 = c[9..24]
                dl = 17;
            } else if (sub == 0x03) {  // finalise
                d[0] = 0x01; dl = 1;
                /* USB pairing only; no radio. */
            } else if (sub == 0x04) {  // exchange keys: derive LTK from A1, return B1
                ns2_pair_set_ltk(&c[9]);  // A1 = c[9..24]
                d[0] = 0x01;
                memcpy(&d[1], ns2_device_key_b1, 16);
                dl = 17;
            }
            break;
        case 0x09:  // console-assigned player LED bitfield
            if (n > 8) (void)c[8];
            dl = 0;
            break;
        case 0x0C:  // feature select
            if (sub == 0x01) {  // get feature info
                uint8_t f = (n > 8) ? c[8] : 0;
                d[4] = (f & 0x01) ? 0x07 : 0x00;
                d[5] = (f & 0x02) ? 0x07 : 0x00;
                d[6] = (f & 0x04) ? 0x01 : 0x00;
                d[7] = (f & 0x80) ? 0x01 : 0x00;
                d[8] = (f & 0x10) ? 0x01 : 0x00;
                d[9] = (f & 0x20) ? 0x03 : 0x00;
                dl = 12;
            } else if (sub == 0x06) {  // configure features -> 40-byte reply echoing feature id
                // Real PC2 replies with 40 data bytes: zeros except data[4] = the requested
                // feature id (request data[4] = c[12]). Capture frames 9494-9687.
                memset(d, 0, 40);
                d[4] = (n > 12) ? c[12] : 0;
                dl = 40;
            } else {  // set/clear/enable/disable mask
                // 0x0C/0x04 with a non-zero feature mask (0x27) is the command that flips report-0x09
                // motion on in the capture (Experiment C) â€” use it to gate the IMU block.
                if (sub == 0x04 && n > 8) ns2_imu_enabled = (c[8] != 0);
                dl = 4;
            }
            break;
        case 0x02: {  // flash memory
            uint32_t addr = (uint32_t)c[12] | ((uint32_t)c[13] << 8) |
                            ((uint32_t)c[14] << 16) | ((uint32_t)c[15] << 24);
            if (sub == 0x04) {  // memory read
                uint8_t len = c[8];
                if (len > 0x50) len = 0x50;
                d[0] = len;
                d[4] = c[12]; d[5] = c[13]; d[6] = c[14]; d[7] = c[15];
                ns2_mem_read(sub, addr, len, &d[8]);
                dl = 8 + len;
            } else if (sub == 0x01) {  // read 0x40 block
                d[0] = 0x40;
                d[4] = c[12]; d[5] = c[13]; d[6] = c[14]; d[7] = c[15];
                ns2_mem_read(sub, addr, 0x40, &d[8]);
                dl = 8 + 0x40;
            } else if (sub == 0x05) {  // memory write -> ack (we don't persist)
                d[4] = c[12]; d[5] = c[13]; d[6] = c[14]; d[7] = c[15];
                dl = 8;
            } else {
                dl = 0;
            }
            break;
        }
        case 0x10:  // firmware info (type byte 0x02 = Pro Controller)
            ns2_firmware_diagnostics_record_command();
            memcpy(d, ns2_firmware_info, sizeof(ns2_firmware_info));
            dl = sizeof(ns2_firmware_info);
            break;
        case 0x0B:  // battery
            if (sub == 0x03) { memcpy(d, (const uint8_t[]){0xA5, 0x0E, 0x00, 0x00}, 4); dl = 4; }
            else if (sub == 0x04) { memcpy(d, (const uint8_t[]){0x34, 0x00, 0x83, 0x00}, 4); dl = 4; }
            else dl = 0;
            break;
        case 0x11:  // unknown; opaque values replayed from the USB capture (last 16 B are a
                    // constant shared across units, so replaying is safe). Frames 9152/9386.
            if (sub == 0x01) { d[0] = 0x03; dl = 4; }  // USB form (0x03; the BLE form is 0x01)
            else if (sub == 0x03) {
                static const uint8_t r11_03[29] = {
                    0x01, 0xC0, 0x03, 0x00, 0x00, 0xE7, 0xD0, 0x1C, 0x3B, 0x79, 0x22, 0xA0, 0x3A,
                    0x0A, 0xE8, 0x9C, 0x42, 0x58, 0xA0, 0x0B, 0x42, 0x0A, 0xE8, 0x9C, 0x41, 0x58,
                    0xA0, 0x0B, 0x41};
                memcpy(d, r11_03, sizeof(r11_03));
                dl = sizeof(r11_03);
            }
            else dl = 0;
            break;
        case 0x01:  // NFC
            if (sub == 0x0C) { memcpy(d, (const uint8_t[]){0x61, 0x12, 0x50, 0x10}, 4); dl = 4; }
            else {
                // Bare/no-data NFC acks use dir=0x04, not the default 0x01 â€” confirmed against
                // the genuine capture for sub 0x01 (packet #30532: `01 04 00 01 00 f8 00 00`),
                // and the same dir=0x04-on-bare-ack shape recurs on an unrelated cmd=0x08 response
                // in the same window. See docs/switch2/nfc-protocol-inventory.md Â§2.3.
                r[1] = 0x04;
                dl = 0;
            }
            break;
        case 0x18:
            if (sub == 0x01) { memcpy(d, (const uint8_t[]){0, 0, 0x40, 0xF0, 0, 0, 0x60, 0}, 8); dl = 8; }
            else if (sub == 0x03) { d[0] = (n > 8) ? c[8] : 0; dl = 1; }
            else dl = 0;
            break;
        default:  // 0x06 shutdown, 0x0A vibration, and anything else -> bare ACK
            dl = 0;
            break;
    }
    return 8u + dl;
}
