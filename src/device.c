#include "pa_device.h"
#include "pa_identity.h"
#include <string.h>

static uint32_t read32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1]<<8) | ((uint32_t)p[2]<<16) | ((uint32_t)p[3]<<24);
}

void pa_device_init(pa_device_t *d) {
    memset(d, 0, sizeof(*d));
    ns2_virtual_nfc_runtime_init(&d->nfc);
    pa_identity_init();
}

void pa_device_present(pa_device_t *d, bool present) {
    d->presented=present && d->loaded;
    ns2_virtual_nfc_runtime_init(&d->nfc);
}

bool pa_slot_load(pa_device_t *d, const uint8_t *slot, size_t size) {
    d->loaded = false;
    d->presented = false;
    ns2_virtual_nfc_runtime_init(&d->nfc);
    if (!slot || size != PA_SLOT_SIZE || memcmp(slot, PA_SLOT_MAGIC, 16)) return false;
    uint32_t n = read32(slot+16);
    if ((n != 540 && n != 572) || read32(slot+20) != virtual_amiibo_crc32(slot+32, n) ||
        virtual_amiibo_validate_raw(slot+32, 540) != VIRTUAL_AMIIBO_OK) return false;
    memcpy(d->raw, slot+32, 540);
    memset(d->signature, 0, 32);
    if (n == 572) memcpy(d->signature, slot+572, 32);
    d->loaded = true;
    return true;
}

size_t pa_device_command(pa_device_t *d, uint32_t now_ms,
                         const uint8_t *c, size_t n, uint8_t r[128]) {
    if (!c || n < 8 || n != 8u + ((size_t)c[4]<<8) + c[5] || c[1] != 0x91 || c[2] != 0) {
        ++d->rejected;
        return 0;
    }
    ++d->commands;
    if (c[0] != 1) return pa_identity_command(c, n, r);
    ++d->nfc_commands;
    ns2_virtual_nfc_response_t response;
    // P0 is read-only. Do not acknowledge a write that is not durable.
    // Preserve the upstream error event/status instead of silently losing writes.
    if (c[3] == 0x14 || c[3] == 0x08) {
        ns2_virtual_nfc_runtime_write_apply_failed(&d->nfc, now_ms);
        memset(&response, 0, sizeof(response));
        response.response_direction = 4;
        ++d->rejected;
    } else if (!ns2_virtual_nfc_runtime_dispatch(&d->nfc, now_ms, c[3], c+8, n-8,
                 d->presented, d->presented ? d->raw : NULL, d->signature, &response)) {
        return pa_identity_command(c, n, r);
    }
    memset(r, 0, 128);
    r[0] = 1; r[1] = response.response_direction; r[2] = c[2]; r[3] = c[3]; r[5] = 0xf8;
    memcpy(r+8, response.payload, response.payload_size);
    return 8u + response.payload_size;
}

void pa_device_report(pa_device_t *d, uint32_t now_ms, const uint8_t buttons[3], uint8_t r[63]) {
    ns2_virtual_nfc_runtime_tick(&d->nfc, now_ms);
    memset(r, 0, 63);
    r[0] = d->counter++;
    r[1] = 0x25; // Upstream unknown-source fallback: external power, full.
    memcpy(r+2, buttons, 3);
    const uint8_t center[3] = {0, 8, 0x80}; // both 12-bit axes = 2048
    memcpy(r+5, center, 3); memcpy(r+8, center, 3);
    r[11] = 0x30;
    r[12] = ns2_virtual_nfc_runtime_report_state(&d->nfc);
    // No motion or headset is advertised.
}
