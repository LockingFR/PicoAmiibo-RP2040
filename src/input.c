#include "pa_input.h"
#include <string.h>

void pa_input_init(pa_input_t *s) { memset(s, 0, sizeof(*s)); }

void pa_input_step(pa_input_t *s, uint32_t now, bool raw, bool config,
                      pa_input_actions_t *out) {
    memset(out, 0, sizeof(*out));
    if (config != s->config_mode) {
        s->config_mode = config;
        s->tap_pending = false;
        s->second_tap = false;
        s->a_active = false;
        if (s->pressed) s->hold_handled = true;
    }
    if (s->a_active && (int32_t)(now - s->a_until) >= 0) s->a_active = false;

    if (raw != s->raw_pressed) {
        s->raw_pressed = raw;
        s->raw_since = now;
    }
    // Do not emit the first single tap while a potential second press is
    // being debounced. Its physical start time decides the double-tap window.
    if (s->tap_pending && !raw && !s->pressed &&
        (uint32_t)(now - s->tap_released) >= PA_INPUT_DOUBLE_TAP_MS) {
        out->toggle_tag = !config;
        s->tap_pending = false;
    }
    if (raw != s->pressed &&
        (uint32_t)(now - s->raw_since) >= PA_INPUT_DEBOUNCE_MS) {
        s->pressed = raw;
        if (raw) {
            s->second_tap = s->tap_pending &&
                (uint32_t)(s->raw_since - s->tap_released) <= PA_INPUT_DOUBLE_TAP_MS;
            if (s->tap_pending && !s->second_tap) out->toggle_tag = !config;
            s->tap_pending = false;
            s->pressed_since = now;
            s->hold_handled = false;
        } else if (!s->hold_handled) {
            uint32_t held = now - s->pressed_since;
            if (held >= PA_INPUT_CONFIG_HOLD_MS) {
                out->toggle_config = true;
            } else if (held < PA_INPUT_TAP_MAX_MS) {
                if (s->second_tap) {
                    if (!config) {
                        s->a_active = true;
                        s->a_until = now + PA_INPUT_A_PULSE_MS;
                    }
                } else if (!config) {
                    s->tap_pending = true;
                    s->tap_released = now;
                }
            }
            s->second_tap = false;
        }
    }
    if (s->pressed && !s->hold_handled &&
        (uint32_t)(now - s->pressed_since) >= PA_INPUT_CONFIG_HOLD_MS) {
        s->hold_handled = true;
        out->toggle_config = true;
    }
    if (out->toggle_config) {
        s->tap_pending = false;
        s->second_tap = false;
        s->a_active = false;
        out->toggle_tag = false;
    }
    if (!config) {
        if (s->a_active) out->buttons[0] |= 0x02; // report 0x09 A
    }
}
