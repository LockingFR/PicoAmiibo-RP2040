#include "pa_config.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint8_t banks[2][4096];
static unsigned saves;
static pa_store_t store;
static bool erase(void *ctx,unsigned bank) { (void)ctx;memset(banks[bank],0xff,4096);return true; }
static bool program(void *ctx,unsigned bank,size_t offset,const uint8_t page[256]) {
    (void)ctx;for(size_t i=0;i<256;++i)banks[bank][offset+i]&=page[i];return true;
}
static bool save(void *ctx,const uint8_t *data,size_t size) {
    (void)ctx;++saves;return pa_store_save(&store,data,size,erase,program,NULL);
}
static void send(pa_config_t *c,const char *line) {
    assert(!c->output_size);
    for(size_t i=0;i<strlen(line);++i)pa_config_feed(c,10,(uint8_t)line[i]);
}
static void expect(pa_config_t *c,const char *s) {
    assert(c->output_size==strlen(s) && !memcmp(c->output,s,c->output_size));c->output_size=0;c->output_offset=0;
}
int main(void) {
    memset(banks,0xff,sizeof(banks));pa_store_init(&store,banks[0],banks[1]);
    pa_device_t d;pa_device_init(&d);pa_config_t c;pa_config_init(&c,&d,&store,save,NULL);
    send(&c,"INFO\n");assert(!memcmp(c.output,"PA1 loaded=0",12));c.output_size=0;
    send(&c,"READ\n");expect(&c,"ERR empty\n");
    send(&c,"LOAD 2048 0\n");expect(&c,"ERR command\n");assert(saves==0);
    send(&c,"LOAD 540 0 junk\n");expect(&c,"ERR command\n");
    send(&c,"LOAD 540 0\n");expect(&c,"READY\n");
    pa_config_feed(&c,20,7);pa_config_tick(&c,5021);expect(&c,"ERR timeout\n");assert(saves==0);
    uint8_t raw[572];for(size_t i=0;i<572;++i)raw[i]=(uint8_t)(i*29+7);
    raw[3]=0x88^raw[0]^raw[1]^raw[2];raw[8]=raw[4]^raw[5]^raw[6]^raw[7];
    char line[80];snprintf(line,sizeof(line),"LOAD 572 %08lx\n",(unsigned long)virtual_amiibo_crc32(raw,572));
    send(&c,line);expect(&c,"READY\n");
    for(size_t i=0;i<572;++i)pa_config_feed(&c,30,raw[i]);
    expect(&c,"OK\n");assert(saves==1 && d.loaded && !d.presented);
    send(&c,"READ\n");uint8_t *start=memchr(c.output,'\n',c.output_size);assert(start);
    size_t header=(size_t)(start+1-c.output);assert(c.output_size==header+572 && !memcmp(start+1,raw,572));c.output_size=0;
    send(&c,"LOAD 540 0\n");expect(&c,"READY\n");
    for(size_t i=0;i<540;++i) {pa_config_feed(&c,40,raw[i]);}
    expect(&c,"ERR crc\n");assert(saves==1);
    assert(!memcmp(pa_store_slot(&store)+32,raw,572));
    for(unsigned i=0;i<1000;++i) {pa_config_feed(&c,50,'x');}
    pa_config_feed(&c,50,'\n');expect(&c,"ERR line\n");
    send(&c,"EXIT\n");expect(&c,"BYE\n");assert(c.exit_requested);
    puts("PASS config: INFO, raw readback, CRC, timeout, overflow, interrupted upload preservation, controlled exit");
}
