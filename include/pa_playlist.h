#pragma once
#include "pa_store.h"

#define PA_PLAYLIST_MAX_SLOTS 64u
#define PA_PLAYLIST_BANK_SIZE 65536u
#define PA_PLAYLIST_DATA_OFFSET PA_PAGE_SIZE
#define PA_PLAYLIST_MAX_BYTES (PA_PLAYLIST_MAX_SLOTS * PA_SLOT_SIZE)
/* Keep both original single-tag sectors untouched for rollback. */
#define PA_PLAYLIST_FLASH_BANK0 (PA_FLASH_BANK0 - 2u * PA_PLAYLIST_BANK_SIZE)

typedef struct {
    const uint8_t *bank[2];
    int active;
    uint32_t generation;
    unsigned count;
    unsigned index;
} pa_playlist_t;

void pa_playlist_init(pa_playlist_t *list, const uint8_t *a, const uint8_t *b);
bool pa_playlist_validate_slots(const uint8_t *slots, unsigned count, size_t bytes);
const uint8_t *pa_playlist_slot(const pa_playlist_t *list, unsigned index);
bool pa_playlist_save(pa_playlist_t *list, const uint8_t *slots, unsigned count,
                      pa_erase_fn erase, pa_program_fn program, void *context);
bool pa_playlist_save_single(pa_playlist_t *list, const uint8_t *raw, size_t size,
                             pa_erase_fn erase, pa_program_fn program, void *context);
