#include "pa_store.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static uint8_t banks[2][PA_BANK_SIZE];
typedef struct { int fail_call,call; size_t prefix; } fault_t;
static bool erase(void *ctx,unsigned bank) {
    fault_t *f=ctx;
    if(f->call++==f->fail_call) {memset(banks[bank],0xff,f->prefix);return false;}
    memset(banks[bank],0xff,PA_BANK_SIZE);return true;
}
static bool program(void *ctx,unsigned bank,size_t offset,const uint8_t page[256]) {
    fault_t *f=ctx; size_t n=PA_PAGE_SIZE;
    bool fail=f->call++==f->fail_call; if(fail)n=f->prefix;
    for(size_t i=0;i<n;++i) banks[bank][offset+i]&=page[i];
    return !fail;
}
static void fixture(uint8_t *data,size_t n,unsigned seed) {
    for(size_t i=0;i<n;++i)data[i]=(uint8_t)(i*29+seed);
    data[3]=0x88^data[0]^data[1]^data[2];data[8]=data[4]^data[5]^data[6]^data[7];
}
int main(void) {
    memset(banks,0xff,sizeof(banks));pa_store_t s;pa_store_init(&s,banks[0],banks[1]);assert(s.active==-1);
    uint8_t old[572],next[572],snapshot[2][PA_BANK_SIZE];fixture(old,572,7);fixture(next,572,17);
    fault_t f={-1,0,0};assert(pa_store_save(&s,old,572,erase,program,&f));assert(s.active==0 && s.generation==1);
    memcpy(snapshot,banks,sizeof(banks));
    unsigned trials=0;
    // Cut every erase/program call at every byte boundary. Only a complete
    // valid committed generation may supersede the old one after reboot.
    for(int call=0;call<5;++call) {
        size_t limit=call==0 ? PA_BANK_SIZE : PA_PAGE_SIZE;
        for(size_t cut=0;cut<limit;++cut) {
            memcpy(banks,snapshot,sizeof(banks));pa_store_init(&s,banks[0],banks[1]);
            f=(fault_t){call,0,cut};assert(!pa_store_save(&s,next,572,erase,program,&f));
            assert(!memcmp(banks[0],snapshot[0],PA_BANK_SIZE));
            pa_store_init(&s,banks[0],banks[1]);assert(s.active>=0);
            const uint8_t *slot=pa_store_slot(&s);
            // A cut after every significant commit byte is already a valid
            // commit, even if unused tail padding was not programmed.
            if(s.generation==1)assert(!memcmp(slot+32,old,572));
            else {assert(s.generation==2);assert(!memcmp(slot+32,next,572));}
            ++trials;
        }
    }
    memcpy(banks,snapshot,sizeof(banks));pa_store_init(&s,banks[0],banks[1]);f=(fault_t){-1,0,0};
    assert(pa_store_save(&s,next,540,erase,program,&f));assert(s.active==1 && s.generation==2);
    pa_store_init(&s,banks[0],banks[1]);assert(s.active==1);
    banks[1][100]^=1;pa_store_init(&s,banks[0],banks[1]);assert(s.active==0);
    f=(fault_t){-1,0,0};assert(!pa_store_save(&s,next,541,erase,program,&f) && f.call==0);
    printf("PASS dual-bank store: %u interrupted flash simulations, old bank preservation, CRC fallback, 540/572 bytes\n",trials);
}
