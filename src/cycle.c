#include "pa_cycle.h"

bool pa_cycle_request(pa_cycle_t *c,pa_playlist_t *p,pa_device_t *d,uint32_t now) {
    if(c->pending || p->count<2)return false;
    pa_device_present(d,false);
    c->target=(p->index+1)%p->count;c->requested_at=now;c->pending=true;
    return true;
}
bool pa_cycle_tick(pa_cycle_t *c,pa_playlist_t *p,pa_device_t *d,
                   uint32_t now,bool tx_busy,bool rx_partial) {
    if(!c->pending || (uint32_t)(now-c->requested_at)<PA_CYCLE_REMOVAL_MS || tx_busy || rx_partial)
        return false;
    c->pending=false;
    const uint8_t *slot=pa_playlist_slot(p,c->target);
    if(!slot || !pa_slot_load(d,slot,PA_SLOT_SIZE))return false;
    p->index=c->target;
    return true;
}
