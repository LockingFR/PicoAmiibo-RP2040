#include "pa_playlist.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static uint8_t banks[2][PA_PLAYLIST_BANK_SIZE],saved[2][PA_PLAYLIST_BANK_SIZE];
static uint8_t slots[PA_PLAYLIST_MAX_BYTES];
static size_t cut,done;
static void write32(uint8_t *p,uint32_t v) { for(unsigned i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i)); }
static bool erase(void *ctx,unsigned bank) {
    (void)ctx;assert(bank<2);
    /* Erase interruption is checked separately at every sector boundary. */
    if(done>=cut)return false;
    memset(banks[bank],0xff,PA_PLAYLIST_BANK_SIZE);++done;return true;
}
static bool program(void *ctx,unsigned bank,size_t offset,const uint8_t page[256]) {
    (void)ctx;assert(bank<2 && offset%256==0 && offset+256<=PA_PLAYLIST_BANK_SIZE);
    for(size_t i=0;i<256;++i) {
        if(done++>=cut)return false;
        assert((banks[bank][offset+i]&page[i])==page[i]);
        banks[bank][offset+i]&=page[i];
    }
    return true;
}
static void make_slot(unsigned index,unsigned seed,size_t n) {
    uint8_t *p=slots+(size_t)index*PA_SLOT_SIZE;memset(p,0,PA_SLOT_SIZE);
    memcpy(p,PA_SLOT_MAGIC,16);write32(p+16,(uint32_t)n);
    for(size_t i=0;i<n;++i)p[32+i]=(uint8_t)(i*29+seed);
    p[35]=0x88^p[32]^p[33]^p[34];p[40]=p[36]^p[37]^p[38]^p[39];
    write32(p+20,virtual_amiibo_crc32(p+32,n));
}
int main(void) {
    memset(banks,0xff,sizeof(banks));pa_playlist_t p;
    pa_playlist_init(&p,banks[0],banks[1]);assert(p.active==-1 && p.count==0);
    for(unsigned i=0;i<64;++i)make_slot(i,i+1,i%2 ? 572 : 540);
    assert(pa_playlist_validate_slots(slots,64,sizeof(slots)));
    assert(!pa_playlist_validate_slots(slots,65,sizeof(slots)));
    assert(!pa_playlist_validate_slots(slots,0,0));
    assert(!pa_playlist_validate_slots(slots,2,1));
    cut=SIZE_MAX;done=0;assert(pa_playlist_save(&p,slots,64,erase,program,NULL));
    assert(p.count==64 && p.index==0 && p.generation==1);
    for(unsigned i=0;i<64;++i)assert(!memcmp(pa_playlist_slot(&p,i),slots+i*PA_SLOT_SIZE,PA_SLOT_SIZE));
    assert(!pa_playlist_slot(&p,64));p.index=63;
    pa_playlist_init(&p,banks[0],banks[1]);assert(p.index==0 && p.count==64);

    /* A whole list is atomically replaced by one tag. */
    done=0;assert(pa_playlist_save_single(&p,slots+32,540,erase,program,NULL));
    assert(p.count==1 && p.index==0 && p.generation==2);
    memcpy(saved,banks,sizeof(banks));
    unsigned interruptions=0;
    make_slot(0,101,540);make_slot(1,102,572);
    /* Every byte of header/data/commit programming, including partial commit. */
    for(cut=0;cut<1+256+5*256+256+2;++cut) {
        memcpy(banks,saved,sizeof(banks));pa_playlist_init(&p,banks[0],banks[1]);done=0;
        (void)pa_playlist_save(&p,slots,2,erase,program,NULL);
        pa_playlist_init(&p,banks[0],banks[1]);
        assert(p.active>=0 && (p.count==1 || p.count==2));
        if(p.count==2)assert(!memcmp(pa_playlist_slot(&p,1),slots+PA_SLOT_SIZE,PA_SLOT_SIZE));
        else assert(!memcmp(pa_playlist_slot(&p,0),saved[1]+PA_PLAYLIST_DATA_OFFSET,PA_SLOT_SIZE));
        ++interruptions;
    }
    /* A partially erased inactive bank cannot destroy the last committed list. */
    for(size_t erased=0;erased<=PA_PLAYLIST_BANK_SIZE;erased+=4096) {
        memcpy(banks,saved,sizeof(banks));memset(banks[0],0xff,erased);
        pa_playlist_init(&p,banks[0],banks[1]);assert(p.count==1 && p.generation==2);
    }
    memcpy(banks,saved,sizeof(banks));pa_playlist_init(&p,banks[0],banks[1]);
    slots[35]^=1;cut=SIZE_MAX;done=0;
    assert(!pa_playlist_save(&p,slots,2,erase,program,NULL));assert(done==0);
    slots[35]^=1;
    memset(banks[0],0xff,sizeof(banks[0]));
    write32(banks[1]+20,UINT32_MAX);
    uint8_t *commit=banks[1]+PA_PLAYLIST_BANK_SIZE-PA_PAGE_SIZE;
    write32(commit+20,UINT32_MAX);write32(commit+28,virtual_amiibo_crc32(banks[1],256));
    pa_playlist_init(&p,banks[0],banks[1]);assert(p.generation==UINT32_MAX);
    done=0;assert(pa_playlist_save(&p,slots,2,erase,program,NULL));
    pa_playlist_init(&p,banks[0],banks[1]);assert(p.generation==0 && p.count==2);
    printf("PASS playlist: 64 slots, single replacement, bounds, CRC/BCC, reboot, %u programming cuts and sector erase cuts\n",interruptions);
    return 0;
}
