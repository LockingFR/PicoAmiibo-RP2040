#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "pa_device.h"
#include "pa_identity.h"
#include "ns2_vendor_rx.h"

static void write32(uint8_t *p,uint32_t v) { for(unsigned i=0;i<4;++i) p[i]=(uint8_t)(v>>(8*i)); }
static void slot_make(uint8_t s[PA_SLOT_SIZE]) {
    memset(s,0,PA_SLOT_SIZE); memcpy(s,PA_SLOT_MAGIC,16); write32(s+16,572);
    for(size_t i=0;i<572;++i) s[32+i]=(uint8_t)(i*29+7);
    s[35]=0x88^s[32]^s[33]^s[34]; s[40]=s[36]^s[37]^s[38]^s[39];
    write32(s+20,virtual_amiibo_crc32(s+32,572));
}
static size_t send(pa_device_t *d,uint32_t time,uint8_t id,uint8_t sub,const uint8_t *p,size_t n,uint8_t r[128]) {
    uint8_t c[128]={id,0x91,0,sub,0,(uint8_t)n,0,0};
    assert(n<=120); if(n) memcpy(c+8,p,n);
    return pa_device_command(d,time,c,n+8,r);
}
static void descriptors(void) {
    const uint8_t *c=ns2_config_descriptor();
    assert(c[2]==80 && c[3]==0 && c[4]==2);
    unsigned interfaces=0,eps=0; uint8_t seen=0;
    for(size_t i=0;i<80;) {
        assert(c[i]>=2 && i+c[i]<=80);
        if(c[i+1]==4) ++interfaces;
        if(c[i+1]==5) { ++eps; if(c[i+2]==0x81)seen|=1; if(c[i+2]==1)seen|=2; if(c[i+2]==0x82)seen|=4; if(c[i+2]==2)seen|=8; }
        i+=c[i];
    }
    assert(interfaces==2 && eps==4 && seen==15);
    const uint8_t *dev=ns2_device_descriptor(); assert(dev[8]==0x7e && dev[10]==0x69 && dev[11]==0x20);
}
int main(void) {
    descriptors();
    pa_device_t d; pa_device_init(&d);
    uint8_t slot[PA_SLOT_SIZE],r[128]; slot_make(slot);
    assert(!pa_slot_load(&d,slot,PA_SLOT_SIZE-1));
    assert(send(&d,0,1,5,NULL,0,r)==69 && r[8]==7);
    assert(pa_slot_load(&d,slot,sizeof(slot)) && d.loaded);
    assert(!d.presented);
    assert(send(&d,0,1,5,NULL,0,r)==69 && r[8]==7);
    pa_device_present(&d,true);
    assert(send(&d,0,3,0x0a,NULL,0,r)==0); // short init must not read past end
    uint8_t select=9;
    assert(send(&d,0,3,0x0a,&select,1,r)==8 && pa_identity_streaming());
    assert(send(&d,0,1,3,NULL,0,r)==8 && r[1]==4);
    uint8_t report[63],buttons[3]={0}; pa_device_report(&d,41,buttons,report);
    assert(report[12]==2 && report[5]==0 && report[6]==8 && report[7]==0x80 && report[14]==0);
    assert(send(&d,42,1,5,NULL,0,r)==69 && r[8]==9 && r[16]==7);
    const uint8_t begin[19]={0xd0,7,0,0,0,0,0,0,0,1,3,0,0x3b,0x3c,0x77,0x78,0x86,0,0};
    assert(send(&d,43,1,6,begin,sizeof(begin),r)==8);
    uint8_t expected[600],received[600];
    assert(ns2_virtual_nfc_build_read_buffer(slot+32,slot+572,begin+10,expected)==NS2_VIRTUAL_NFC_OK);
    size_t count=0;
    for(unsigned offset=0;offset<600;offset+=70) {
        uint8_t p[2]={(uint8_t)offset,(uint8_t)(offset>>8)};
        size_t n=send(&d,85,1,0x15,p,2,r);
        assert(n>=11 && n<=81 && r[1]==1);
        size_t bytes=(size_t)r[9]+((size_t)r[10]<<8);
        assert(n==11+bytes && count+bytes<=600);
        memcpy(received+count,r+11,bytes); count+=bytes;
        assert(r[8]==(count==600));
    }
    assert(count==600 && !memcmp(expected,received,600));
    pa_device_present(&d,false);
    assert(send(&d,86,1,5,NULL,0,r)==69 && r[8]==7);
    pa_device_present(&d,true);
    assert(send(&d,87,1,3,NULL,0,r)==8);
    pa_device_report(&d,128,buttons,report); assert(report[12]==2);
    uint8_t before[540]; memcpy(before,d.raw,540);
    assert(send(&d,90,1,0x08,NULL,0,r)==8);
    assert(!memcmp(before,d.raw,540));
    assert(send(&d,92,1,5,NULL,0,r)==69 && r[8]==7 && r[9]==0x41);
    slot[100]^=1; assert(!pa_slot_load(&d,slot,sizeof(slot)) && !d.loaded);
    // Deterministic malformed packet campaign under ASan/UBSan.
    uint32_t random=42;
    for(unsigned k=0;k<20000;++k) {
        uint8_t c[128];
        for(unsigned j=0;j<128;++j) { random=random*1664525u+1013904223u; c[j]=(uint8_t)(random>>24); }
        size_t n=k%129; if(n>=8) {c[1]=0x91;c[2]=0;c[4]=0;c[5]=(uint8_t)(n-8);}
        assert(pa_device_command(&d,k,c,n,r)<=128);
    }
    puts("PASS device integration: descriptors, empty/load/CRC, handshake bounds, scan/read 600 bytes, write refusal, 20000 malformed packets");
    return 0;
}
