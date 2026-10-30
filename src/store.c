#include "pa_store.h"
#include <string.h>
#define COMMIT_MAGIC "PA-COMMITTED-v1"
_Static_assert(sizeof(COMMIT_MAGIC)==16, "Commit marker includes terminator");
static uint32_t read32(const uint8_t *p) {
    return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
static void write32(uint8_t *p,uint32_t v) { for(unsigned i=0;i<4;++i) p[i]=(uint8_t)(v>>(8*i)); }
static bool valid(const uint8_t *p) {
    if (!p || memcmp(p,PA_SLOT_MAGIC,16)) return false;
    const uint8_t *commit=p+PA_BANK_SIZE-PA_PAGE_SIZE;
    if(memcmp(commit,COMMIT_MAGIC,16)) return false;
    size_t n=read32(p+16);
    return (n==540 || n==572) &&
        read32(commit+16)==virtual_amiibo_crc32(p,PA_SLOT_SIZE) &&
        read32(commit+20)==read32(p+24) && read32(commit+24)==1 &&
        read32(p+20)==virtual_amiibo_crc32(p+32,n) &&
        virtual_amiibo_validate_raw(p+32,540)==VIRTUAL_AMIIBO_OK;
}
void pa_store_init(pa_store_t *s,const uint8_t *a,const uint8_t *b) {
    s->bank[0]=a; s->bank[1]=b; s->active=-1; s->generation=0;
    for(int i=0;i<2;++i) if(valid(s->bank[i])) {
        uint32_t gen=read32(s->bank[i]+24);
        if(s->active<0 || (int32_t)(gen-s->generation)>0) { s->active=i; s->generation=gen; }
    }
}
const uint8_t *pa_store_slot(const pa_store_t *s) {
    return s->active<0 || !valid(s->bank[s->active]) ? NULL : s->bank[s->active];
}
bool pa_store_save(pa_store_t *s,const uint8_t *data,size_t n,
                    pa_erase_fn erase,pa_program_fn program,void *ctx) {
    if(!s || !data || !erase || !program || (n!=540 && n!=572) ||
        virtual_amiibo_validate_raw(data,540)!=VIRTUAL_AMIIBO_OK) return false;
    uint8_t record[3*PA_PAGE_SIZE],commit[PA_PAGE_SIZE];
    memset(record,0,sizeof(record)); memset(commit,0xff,sizeof(commit));
    memcpy(record,PA_SLOT_MAGIC,16); write32(record+16,(uint32_t)n);
    write32(record+20,virtual_amiibo_crc32(data,n));
    uint32_t generation=s->generation+1;
    write32(record+24,generation); memcpy(record+32,data,n);
    memcpy(commit,COMMIT_MAGIC,16); write32(commit+16,virtual_amiibo_crc32(record,PA_SLOT_SIZE));
    write32(commit+20,generation); write32(commit+24,1);
    unsigned target=s->active==0 ? 1u : 0u;
    if(!erase(ctx,target)) return false;
    for(size_t offset=0;offset<sizeof(record);offset+=PA_PAGE_SIZE)
        if(!program(ctx,target,offset,record+offset)) return false;
    // Commit is programmed only after every data page. The previous bank is
    // never erased here. A torn marker or page fails validation at boot.
    if(!program(ctx,target,PA_BANK_SIZE-PA_PAGE_SIZE,commit)) return false;
    if(!valid(s->bank[target])) return false;
    s->active=(int)target; s->generation=generation;
    return true;
}
