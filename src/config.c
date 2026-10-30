#include "pa_config.h"
#include <stdio.h>
#include <string.h>

static void reply(pa_config_t *c,const char *message) {
    c->output_offset=0; c->output_size=strlen(message);
    memcpy(c->output,message,c->output_size);
}
static uint32_t read32(const uint8_t *p) {
    return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
static bool parse_load(const char *line,unsigned *size,unsigned *crc) {
    if(strncmp(line,"LOAD ",5))return false;
    const char *p=line+5;
    unsigned n=0,digits=0,value=0;
    while(*p>='0' && *p<='9') {
        if(++digits>3)return false;
        n=n*10+(unsigned)(*p++-'0');
    }
    if(!digits || *p++!=' ' || (n!=540 && n!=572))return false;
    digits=0;
    while(*p) {
        unsigned nibble;
        if(*p>='0' && *p<='9')nibble=(unsigned)(*p-'0');
        else if(*p>='a' && *p<='f')nibble=(unsigned)(*p-'a'+10);
        else if(*p>='A' && *p<='F')nibble=(unsigned)(*p-'A'+10);
        else return false;
        if(++digits>8)return false;
        value=(value<<4)|nibble;++p;
    }
    if(!digits)return false;
    *size=n;*crc=value;return true;
}
void pa_config_init(pa_config_t *c,pa_device_t *d,pa_store_t *s,pa_config_save_fn save,void *ctx) {
    memset(c,0,sizeof(*c)); c->device=d; c->store=s; c->save=save; c->context=ctx;
}
void pa_config_set_playlist(pa_config_t *c,pa_playlist_t *list,pa_config_save_list_fn save_list) {
    c->playlist=list;c->save_list=save_list;
}
static unsigned slot_count(const pa_config_t *c) {
    return c->playlist && c->playlist->count ? c->playlist->count : (pa_store_slot(c->store) ? 1u : 0u);
}
static const uint8_t *get_slot(const pa_config_t *c,unsigned index) {
    if(c->playlist && c->playlist->count)return pa_playlist_slot(c->playlist,index);
    return index==0 ? pa_store_slot(c->store) : NULL;
}
static unsigned current_index(const pa_config_t *c) {
    return c->playlist && c->playlist->count ? c->playlist->index : 0;
}
static bool parse_index(const char *p,unsigned *value) {
    unsigned n=0,digits=0;
    while(*p>='0' && *p<='9') {
        if(++digits>2)return false;
        n=n*10+(unsigned)(*p++-'0');
    }
    if(!digits || *p || n>=PA_PLAYLIST_MAX_SLOTS)return false;
    *value=n;return true;
}
static bool parse_batch(const char *line,unsigned *count,unsigned *bytes,unsigned *crc) {
    if(strncmp(line,"BATCH ",6))return false;
    const char *p=line+6;unsigned n=0,size=0,value=0,digits=0;
    while(*p>='0' && *p<='9') {
        if(++digits>2)return false;
        n=n*10+(unsigned)(*p++-'0');
    }
    if(!digits || *p++!=' ' || !n || n>PA_PLAYLIST_MAX_SLOTS)return false;
    digits=0;
    while(*p>='0' && *p<='9') {
        if(++digits>5)return false;
        size=size*10+(unsigned)(*p++-'0');
    }
    if(!digits || *p++!=' ' || size!=n*PA_SLOT_SIZE)return false;
    for(unsigned i=0;i<8;++i) {
        unsigned nibble;
        if(*p>='0' && *p<='9')nibble=(unsigned)(*p-'0');
        else if(*p>='a' && *p<='f')nibble=(unsigned)(*p-'a'+10);
        else if(*p>='A' && *p<='F')nibble=(unsigned)(*p-'A'+10);
        else return false;
        value=(value<<4)|nibble;++p;
    }
    if(*p)return false;
    *count=n;*bytes=size;*crc=value;return true;
}
static void line_command(pa_config_t *c) {
    if(!strcmp(c->line,"INFO")) {
        const uint8_t *slot=get_slot(c,current_index(c));
        c->output_size=(size_t)snprintf((char *)c->output,sizeof(c->output),
            "PA1 loaded=%u size=%lu crc=%08lx generation=%lu presented=%u commands=%lu nfc=%lu rejected=%lu\n",
            c->device->loaded,(unsigned long)(slot?read32(slot+16):0),
            (unsigned long)(slot?read32(slot+20):0),(unsigned long)(c->playlist && c->playlist->count ? c->playlist->generation : c->store->generation),
            c->device->presented,(unsigned long)c->device->commands,
            (unsigned long)c->device->nfc_commands,(unsigned long)c->device->rejected);
        c->output_offset=0;
        if(c->playlist) {
            /* Keep the PA1 fields compatible with the original loader. */
            --c->output_size;
            c->output_size+=(size_t)snprintf((char *)c->output+c->output_size,sizeof(c->output)-c->output_size,
                " protocol=2 max_slots=%u slots=%u index=%u\n",PA_PLAYLIST_MAX_SLOTS,slot_count(c),current_index(c));
        }
    } else if(!strcmp(c->line,"CAPS") && c->playlist) {
        c->output_size=(size_t)snprintf((char *)c->output,sizeof(c->output),
            "PA2 protocol=2 max_slots=%u slot_size=%u count=%u index=%u\n",
            PA_PLAYLIST_MAX_SLOTS,PA_SLOT_SIZE,slot_count(c),current_index(c));
        c->output_offset=0;
    } else if(!strcmp(c->line,"READ") || (c->playlist && !strncmp(c->line,"READ ",5))) {
        unsigned index=current_index(c);
        if(c->line[4] && !parse_index(c->line+5,&index)) {reply(c,"ERR index\n");return;}
        if(c->line[4] && index>=slot_count(c)) {reply(c,"ERR index\n");return;}
        const uint8_t *slot=get_slot(c,index);
        if(!slot) {reply(c,"ERR empty\n");return;}
        size_t size=read32(slot+16);
        size_t header=(size_t)snprintf((char *)c->output,sizeof(c->output),"DATA %u %08lx\n",
            (unsigned)size,(unsigned long)read32(slot+20));
        memcpy(c->output+header,slot+32,size);
        c->output_size=header+size; c->output_offset=0;
    } else if(!strcmp(c->line,"EXIT")) {
        reply(c,"BYE\n"); c->exit_requested=true;
    } else {
        unsigned size,crc;
        unsigned count=0;
        if(c->playlist && c->save_list && parse_batch(c->line,&count,&size,&crc)) {
            c->upload_count=count;
        } else if(parse_load(c->line,&size,&crc))c->upload_count=0;
        else {reply(c,"ERR command\n");return;}
        c->expected=size; c->received=0; c->crc=crc;
        reply(c,"READY\n");
    }
}
void pa_config_feed(pa_config_t *c,uint32_t now,uint8_t byte) {
    c->last_activity=now;
    if(c->expected) {
        c->upload[c->received++]=byte;
        if(c->received==c->expected) {
            size_t n=c->expected; c->expected=0; c->received=0;
            if(virtual_amiibo_crc32(c->upload,n)!=c->crc) reply(c,"ERR crc\n");
            else if(c->upload_count ?
                !c->save_list(c->context,c->upload,c->upload_count) :
                !c->save(c->context,c->upload,n)) reply(c,"ERR store\n");
            else {
                const uint8_t *slot=get_slot(c,current_index(c));
                if(!slot || !pa_slot_load(c->device,slot,PA_SLOT_SIZE)) reply(c,"ERR readback\n");
                else reply(c,"OK\n");
            }
        }
        return;
    }
    if(byte=='\r') return;
    if(byte=='\n') {
        if(c->discard_line) reply(c,"ERR line\n");
        else {c->line[c->line_size]='\0';line_command(c);}
        c->line_size=0;c->discard_line=false;return;
    }
    if(c->discard_line) return;
    if(byte<32 || byte>126 || c->line_size>=sizeof(c->line)-1) {c->discard_line=true;return;}
    c->line[c->line_size++]=(char)byte;
}
void pa_config_tick(pa_config_t *c,uint32_t now) {
    if((c->expected || c->line_size || c->discard_line) &&
        (uint32_t)(now-c->last_activity)>=5000u) {
        c->expected=0;c->received=0;c->line_size=0;c->discard_line=false;
        c->upload_count=0;
        reply(c,"ERR timeout\n");
    }
}
