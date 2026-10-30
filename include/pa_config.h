#pragma once
#include "pa_store.h"
#include "pa_playlist.h"
typedef bool (*pa_config_save_fn)(void *context, const uint8_t *data, size_t size);
typedef bool (*pa_config_save_list_fn)(void *context, const uint8_t *slots, unsigned count);
typedef struct {
    pa_device_t *device;
    pa_store_t *store;
    pa_config_save_fn save;
    void *context;
    pa_playlist_t *playlist;
    pa_config_save_list_fn save_list;
    unsigned upload_count;
    char line[80];
    size_t line_size;
    bool discard_line;
    uint8_t upload[PA_PLAYLIST_MAX_BYTES];
    size_t expected, received;
    uint32_t crc, last_activity;
    uint8_t output[768];
    size_t output_size, output_offset;
    bool exit_requested;
} pa_config_t;
void pa_config_init(pa_config_t *config, pa_device_t *device, pa_store_t *store,
                      pa_config_save_fn save, void *context);
void pa_config_set_playlist(pa_config_t *config,pa_playlist_t *list,pa_config_save_list_fn save_list);
// Caller drains output before feeding another input byte.
void pa_config_feed(pa_config_t *config, uint32_t now, uint8_t byte);
void pa_config_tick(pa_config_t *config, uint32_t now);
