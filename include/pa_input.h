#pragma once
#include <stdbool.h>
#include <stdint.h>

#define PA_INPUT_DEBOUNCE_MS 15u
#define PA_INPUT_DOUBLE_TAP_MS 400u
#define PA_INPUT_TAP_MAX_MS 600u
#define PA_INPUT_CONFIG_HOLD_MS 2000u
#define PA_INPUT_A_PULSE_MS 180u

typedef struct {
    uint32_t raw_since, pressed_since, tap_released, a_until;
    bool raw_pressed, pressed, hold_handled, second_tap, tap_pending;
    bool a_active, config_mode;
} pa_input_t;

typedef struct {
    uint8_t buttons[3];
    bool toggle_tag;
    bool toggle_config;
} pa_input_actions_t;

void pa_input_init(pa_input_t *input);
// Nonblocking, caller supplies the QSPI sample and monotonic uint32 ms clock.
// Single tap: delayed tag toggle. Double tap: A, without changing tag presence.
// Medium hold: no action. Long hold: configuration, once per physical press.
void pa_input_step(pa_input_t *input, uint32_t now_ms, bool raw_pressed,
                      bool config_mode, pa_input_actions_t *actions);
