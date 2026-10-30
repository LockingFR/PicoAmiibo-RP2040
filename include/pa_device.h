#pragma once
#include "ns2_virtual_nfc_runtime.h"
#define PA_SLOT_SIZE 608u
#define PA_SLOT_MAGIC "PICOAMIIBO-V001!"
typedef struct {
    ns2_virtual_nfc_runtime_t nfc;
    uint8_t raw[540];
    uint8_t signature[32];
    uint8_t counter;
    bool loaded;
    bool presented;
    uint32_t commands;
    uint32_t nfc_commands;
    uint32_t rejected;
} pa_device_t;
bool pa_slot_load(pa_device_t *device, const uint8_t *slot, size_t size);
void pa_device_init(pa_device_t *device);
void pa_device_present(pa_device_t *device, bool present);
size_t pa_device_command(pa_device_t *device, uint32_t now_ms,
                         const uint8_t *command, size_t size, uint8_t response[128]);
void pa_device_report(pa_device_t *device, uint32_t now_ms,
                      const uint8_t buttons[3], uint8_t response[63]);
