#include "pa_config.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t banks[2][PA_PLAYLIST_BANK_SIZE],legacy[2][PA_BANK_SIZE],payload[2*PA_SLOT_SIZE];
static pa_playlist_t list;
static pa_store_t store;
static bool erase(void *ctx,unsigned bank) {(void)ctx;memset(banks[bank],0xff,sizeof(banks[bank]));return true;}
static bool program(void *ctx,unsigned bank,size_t offset,const uint8_t page[256]) {
    (void)ctx;assert(bank<2 && offset+256<=sizeof(banks[bank]));
    for(unsigned i=0;i<256;++i)banks[bank][offset+i]&=page[i];
    return true;
}
static bool save_one(void *ctx,const uint8_t *raw,size_t n) {
    (void)ctx;return pa_playlist_save_single(&list,raw,n,erase,program,NULL);
}
static bool save_many(void *ctx,const uint8_t *slots,unsigned count) {
    (void)ctx;return pa_playlist_save(&list,slots,count,erase,program,NULL);
}
static void send(pa_config_t *c,const char *line) {
    assert(!c->output_size);
    for(size_t i=0;i<strlen(line);++i)pa_config_feed(c,1,(uint8_t)line[i]);
}
static void expect(pa_config_t *c,const char *text) {
    assert(c->output_size==strlen(text) && !memcmp(c->output,text,c->output_size));
    c->output_size=0;c->output_offset=0;
}
static void write32(uint8_t *p,uint32_t n) {for(unsigned i=0;i<4;++i)p[i]=(uint8_t)(n>>(i*8));}
int main(void) {
    memset(banks,0xff,sizeof(banks));memset(legacy,0xff,sizeof(legacy));
    pa_playlist_init(&list,banks[0],banks[1]);pa_store_init(&store,legacy[0],legacy[1]);
    pa_device_t device;pa_device_init(&device);
    static pa_config_t c;pa_config_init(&c,&device,&store,save_one,NULL);
    pa_config_set_playlist(&c,&list,save_many);
    send(&c,"CAPS\n");expect(&c,"PA2 protocol=2 max_slots=64 slot_size=608 count=0 index=0\n");
    const char *invalid[]={"BATCH 0 0 00000000\n","BATCH 65 39520 00000000\n",
        "BATCH 2 608 00000000\n","BATCH 2 1216 0\n","BATCH 2 1216 ffffffff trailing\n",
        "BATCH 999999999999999999999999 1 00000000\n","READ 64\n","READ 0\n"};
    for(unsigned i=0;i<sizeof(invalid)/sizeof(invalid[0]);++i) {
        send(&c,invalid[i]);assert(!memcmp(c.output,"ERR ",4));c.output_size=0;
        assert(!list.count);
    }
    for(unsigned tag=0;tag<2;++tag) {
        uint8_t *p=payload+tag*PA_SLOT_SIZE;size_t n=tag ? 572 : 540;
        memset(p,0,PA_SLOT_SIZE);memcpy(p,PA_SLOT_MAGIC,16);write32(p+16,(uint32_t)n);
        for(size_t i=0;i<n;++i)p[32+i]=(uint8_t)(i*29+tag+7);
        p[35]=0x88^p[32]^p[33]^p[34];p[40]=p[36]^p[37]^p[38]^p[39];
        write32(p+20,virtual_amiibo_crc32(p+32,n));
    }
    char line[80];snprintf(line,sizeof(line),"BATCH 2 %u %08lx\n",(unsigned)sizeof(payload),
        (unsigned long)virtual_amiibo_crc32(payload,sizeof(payload)));
    send(&c,line);expect(&c,"READY\n");
    for(size_t i=0;i<sizeof(payload);++i)pa_config_feed(&c,2,payload[i]);
    expect(&c,"OK\n");assert(device.loaded && !device.presented && list.count==2);
    send(&c,"INFO\n");c.output[c.output_size]=0;
    assert(strstr((char *)c.output,"protocol=2 max_slots=64 slots=2 index=0"));c.output_size=0;
    send(&c,"READ 1\n");uint8_t *data=memchr(c.output,'\n',c.output_size);
    assert(data && c.output_size-(size_t)(data+1-c.output)==572);
    assert(!memcmp(data+1,payload+PA_SLOT_SIZE+32,572));c.output_size=0;

    /* An interrupted batch does not commit or replace the current list. */
    send(&c,line);expect(&c,"READY\n");pa_config_feed(&c,10,payload[0]);
    pa_config_tick(&c,5010);expect(&c,"ERR timeout\n");assert(list.count==2);
    send(&c,"BATCH 2 1216 00000000\n");expect(&c,"READY\n");
    for(size_t i=0;i<sizeof(payload);++i)pa_config_feed(&c,3,payload[i]);
    expect(&c,"ERR crc\n");assert(list.count==2);

    /* Legacy LOAD explicitly replaces a list with a single record. */
    snprintf(line,sizeof(line),"LOAD 540 %08lx\n",(unsigned long)virtual_amiibo_crc32(payload+32,540));
    send(&c,line);expect(&c,"READY\n");
    for(size_t i=0;i<540;++i)pa_config_feed(&c,4,payload[32+i]);
    expect(&c,"OK\n");assert(list.count==1 && list.index==0);
    for(size_t i=0;i<sizeof(legacy);++i)assert(((const uint8_t *)legacy)[i]==0xff);
    assert(PA_PLAYLIST_FLASH_BANK0+2*PA_PLAYLIST_BANK_SIZE==PA_FLASH_BANK0);
    puts("PASS config playlist: capability, strict bounds, batch/read index, timeout/CRC preserve list, LOAD replaces list, legacy region untouched");
}
