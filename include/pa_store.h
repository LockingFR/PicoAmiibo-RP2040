#pragma once
#include "pa_device.h"
#define PA_BANK_SIZE 4096u
#define PA_PAGE_SIZE 256u
#define PA_FLASH_BANK0 (2u*1024u*1024u - 2u*PA_BANK_SIZE)
typedef struct {
    const uint8_t *bank[2];
    int active;
    uint32_t generation;
} pa_store_t;
typedef bool (*pa_erase_fn)(void *ctx, unsigned bank);
typedef bool (*pa_program_fn)(void *ctx, unsigned bank, size_t offset, const uint8_t page[256]);
void pa_store_init(pa_store_t *store, const uint8_t *bank0, const uint8_t *bank1);
const uint8_t *pa_store_slot(const pa_store_t *store);
bool pa_store_save(pa_store_t *store, const uint8_t *data, size_t size,
                    pa_erase_fn erase, pa_program_fn program, void *ctx);
