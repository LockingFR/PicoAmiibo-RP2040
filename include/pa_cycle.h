#pragma once
#include "pa_playlist.h"

#define PA_CYCLE_REMOVAL_MS 1000u
typedef struct {
    bool pending;
    unsigned target;
    uint32_t requested_at;
} pa_cycle_t;

/* No USB reset or flash write. New tags always start ejected. */
bool pa_cycle_request(pa_cycle_t *cycle, pa_playlist_t *list, pa_device_t *device, uint32_t now);
bool pa_cycle_tick(pa_cycle_t *cycle, pa_playlist_t *list, pa_device_t *device,
                   uint32_t now, bool tx_busy, bool rx_partial);
