#include "pa_cycle.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* Artificial records only. Flash-bank validation is covered in test_playlist. */
static uint8_t bank[PA_PLAYLIST_BANK_SIZE];
static void put32(uint8_t *p,uint32_t value) {
    for(unsigned i=0;i<4;++i)p[i]=(uint8_t)(value>>(8*i));
}
static void slot(unsigned index) {
    uint8_t *p=bank+PA_PLAYLIST_DATA_OFFSET+index*PA_SLOT_SIZE;
    memcpy(p,PA_SLOT_MAGIC,16);put32(p+16,572);
    for(unsigned i=0;i<572;++i)p[32+i]=(uint8_t)(i+index*19);
    p[35]=0x88^p[32]^p[33]^p[34];p[40]=p[36]^p[37]^p[38]^p[39];
    put32(p+20,virtual_amiibo_crc32(p+32,572));
}
int main(void) {
    slot(0);slot(1);slot(2);
    pa_playlist_t p={.bank={bank,NULL},.active=0,.count=3,.generation=7};
    pa_device_t d;pa_device_init(&d);pa_cycle_t c={0};
    assert(pa_slot_load(&d,pa_playlist_slot(&p,0),PA_SLOT_SIZE));
    pa_device_present(&d,true);d.counter=91;d.commands=20;d.nfc_commands=12;
    assert(pa_cycle_request(&c,&p,&d,100));
    assert(!d.presented && c.pending && p.index==0);
    assert(!pa_cycle_request(&c,&p,&d,500)); /* held input cannot queue another */
    assert(!pa_cycle_tick(&c,&p,&d,1099,false,false));
    assert(!pa_cycle_tick(&c,&p,&d,1100,true,false));
    assert(!pa_cycle_tick(&c,&p,&d,1100,false,true));
    assert(c.pending && p.index==0);
    assert(pa_cycle_tick(&c,&p,&d,1100,false,false));
    assert(p.index==1 && !c.pending && d.loaded && !d.presented);
    assert(!memcmp(d.raw,pa_playlist_slot(&p,1)+32,540));
    assert(!memcmp(d.signature,pa_playlist_slot(&p,1)+572,32));
    assert(d.counter==91 && d.commands==20 && d.nfc_commands==12 && p.generation==7);
    assert(!pa_cycle_tick(&c,&p,&d,9000,false,false));
    /* Subsequent holds wrap, including across the uint32_t clock rollover. */
    assert(pa_cycle_request(&c,&p,&d,0xfffffff0u));
    assert(!pa_cycle_tick(&c,&p,&d,500,false,false));
    assert(pa_cycle_tick(&c,&p,&d,984,false,false));assert(p.index==2);
    assert(pa_cycle_request(&c,&p,&d,2000));
    assert(pa_cycle_tick(&c,&p,&d,3000,false,false));assert(p.index==0);
    p.count=1;assert(!pa_cycle_request(&c,&p,&d,4000));
    p.count=0;assert(!pa_cycle_request(&c,&p,&d,4000));
    p.count=3;assert(pa_cycle_request(&c,&p,&d,4000));
    bank[PA_PLAYLIST_DATA_OFFSET+PA_SLOT_SIZE+20]^=1;
    assert(!pa_cycle_tick(&c,&p,&d,5000,false,false));
    assert(p.index==0 && !d.presented && !d.loaded && !c.pending);
    puts("PASS: cycle removal, USB drain, wrap, signature, no auto-present or flash writes; host model only");
    return 0;
}
