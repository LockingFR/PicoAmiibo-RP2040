#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
const uint8_t *ns2_device_descriptor(void);
const uint8_t *ns2_config_descriptor(void);
const uint8_t *ns2_hid_report_descriptor(void);
const char **ns2_string_table(size_t *count);
void pa_identity_init(void);
bool pa_identity_streaming(void);
uint8_t pa_identity_report_id(void);
const uint8_t *pa_identity_ep0(uint8_t request, size_t *size);
size_t pa_identity_command(const uint8_t *command, size_t size, uint8_t response[128]);
