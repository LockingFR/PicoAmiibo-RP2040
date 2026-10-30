#include "pa_playlist.h"
#include <string.h>

#define LIST_MAGIC "PICOAMIIBO-LST1"
#define COMMIT_MAGIC "PA-LIST-COMMIT1"
_Static_assert(sizeof(LIST_MAGIC)==16, "Playlist magic size");
_Static_assert(sizeof(COMMIT_MAGIC)==16, "Playlist commit size");
_Static_assert(PA_PLAYLIST_DATA_OFFSET+PA_PLAYLIST_MAX_BYTES <= PA_PLAYLIST_BANK_SIZE-PA_PAGE_SIZE,
               "Playlist data overlaps commit page");
_Static_assert(PA_PLAYLIST_FLASH_BANK0 % 4096u == 0, "Flash alignment");

static uint32_t read32(const uint8_t *p) {
    return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
static void write32(uint8_t *p,uint32_t v) {
    for(unsigned i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i));
}
bool pa_playlist_validate_slots(const uint8_t *slots,unsigned count,size_t bytes) {
    if(!slots || !count || count>PA_PLAYLIST_MAX_SLOTS || bytes!=(size_t)count*PA_SLOT_SIZE)return false;
    for(unsigned i=0;i<count;++i) {
        const uint8_t *slot=slots+(size_t)i*PA_SLOT_SIZE;
        if(memcmp(slot,PA_SLOT_MAGIC,16))return false;
        size_t n=read32(slot+16);
        if((n!=540 && n!=572) || read32(slot+20)!=virtual_amiibo_crc32(slot+32,n) ||
            virtual_amiibo_validate_raw(slot+32,540)!=VIRTUAL_AMIIBO_OK)return false;
    }
    return true;
}
static bool valid_bank(const uint8_t *p) {
    if(!p || memcmp(p,LIST_MAGIC,16) || read32(p+32)!=1)return false;
    unsigned count=read32(p+16);
    if(!count || count>PA_PLAYLIST_MAX_SLOTS || read32(p+28)!=count*PA_SLOT_SIZE)return false;
    const uint8_t *commit=p+PA_PLAYLIST_BANK_SIZE-PA_PAGE_SIZE;
    uint32_t crc=read32(p+24);
    return !memcmp(commit,COMMIT_MAGIC,16) && read32(commit+16)==crc &&
        read32(commit+20)==read32(p+20) && read32(commit+24)==count &&
        read32(commit+28)==virtual_amiibo_crc32(p,PA_PAGE_SIZE) &&
        crc==virtual_amiibo_crc32(p+PA_PLAYLIST_DATA_OFFSET,(size_t)count*PA_SLOT_SIZE) &&
        pa_playlist_validate_slots(p+PA_PLAYLIST_DATA_OFFSET,count,(size_t)count*PA_SLOT_SIZE);
}
void pa_playlist_init(pa_playlist_t *s,const uint8_t *a,const uint8_t *b) {
    memset(s,0,sizeof(*s));s->bank[0]=a;s->bank[1]=b;s->active=-1;
    for(int i=0;i<2;++i)if(valid_bank(s->bank[i])) {
        uint32_t generation=read32(s->bank[i]+20);
        if(s->active<0 || (int32_t)(generation-s->generation)>0) {
            s->active=i;s->generation=generation;s->count=read32(s->bank[i]+16);
        }
    }
}
const uint8_t *pa_playlist_slot(const pa_playlist_t *s,unsigned index) {
    if(!s || s->active<0 || index>=s->count)return NULL;
    /* Full bank CRC is checked at boot and commit. Banks are immutable in game mode. */
    return s->bank[s->active]+PA_PLAYLIST_DATA_OFFSET+(size_t)index*PA_SLOT_SIZE;
}
bool pa_playlist_save(pa_playlist_t *s,const uint8_t *slots,unsigned count,
                      pa_erase_fn erase,pa_program_fn program,void *ctx) {
    if(!s || !erase || !program ||
        !pa_playlist_validate_slots(slots,count,(size_t)count*PA_SLOT_SIZE))return false;
    uint8_t header[PA_PAGE_SIZE],page[PA_PAGE_SIZE],commit[PA_PAGE_SIZE];
    size_t bytes=(size_t)count*PA_SLOT_SIZE;
    uint32_t generation=s->generation+1,crc=virtual_amiibo_crc32(slots,bytes);
    memset(header,0,sizeof(header));memset(commit,0xff,sizeof(commit));
    memcpy(header,LIST_MAGIC,16);write32(header+16,count);write32(header+20,generation);
    write32(header+24,crc);write32(header+28,(uint32_t)bytes);write32(header+32,1);
    memcpy(commit,COMMIT_MAGIC,16);write32(commit+16,crc);write32(commit+20,generation);
    write32(commit+24,count);write32(commit+28,virtual_amiibo_crc32(header,sizeof(header)));
    unsigned target=s->active==0 ? 1u : 0u;
    if(!erase(ctx,target) || !program(ctx,target,0,header))return false;
    for(size_t offset=0;offset<bytes;offset+=PA_PAGE_SIZE) {
        memset(page,0,sizeof(page));
        size_t n=bytes-offset;if(n>sizeof(page))n=sizeof(page);
        memcpy(page,slots+offset,n);
        if(!program(ctx,target,PA_PLAYLIST_DATA_OFFSET+offset,page))return false;
    }
    if(!program(ctx,target,PA_PLAYLIST_BANK_SIZE-PA_PAGE_SIZE,commit) ||
        !valid_bank(s->bank[target]))return false;
    s->active=(int)target;s->generation=generation;s->count=count;s->index=0;
    return true;
}
bool pa_playlist_save_single(pa_playlist_t *s,const uint8_t *raw,size_t n,
                             pa_erase_fn erase,pa_program_fn program,void *ctx) {
    if(!raw || (n!=540 && n!=572) || virtual_amiibo_validate_raw(raw,540)!=VIRTUAL_AMIIBO_OK)return false;
    uint8_t slot[PA_SLOT_SIZE];memset(slot,0,sizeof(slot));
    memcpy(slot,PA_SLOT_MAGIC,16);write32(slot+16,(uint32_t)n);
    write32(slot+20,virtual_amiibo_crc32(raw,n));memcpy(slot+32,raw,n);
    return pa_playlist_save(s,slot,1,erase,program,ctx);
}
