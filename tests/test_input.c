#include "pa_input.h"
#include "pa_device.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    pa_input_t input;
    pa_device_t device;
    uint32_t now;
    bool config;
    unsigned tag_events, config_events, a_ms;
} fixture_t;

static void init(fixture_t *f) {
    memset(f,0,sizeof(*f));
    pa_input_init(&f->input);
    pa_device_init(&f->device);
    // Presence flag only; this test never serves tag data or uses a real dump.
    f->device.loaded=true;
}
static void step(fixture_t *f,bool raw) {
    pa_input_actions_t a;
    ++f->now;
    pa_input_step(&f->input,f->now,raw,f->config,&a);
    // BOOTSEL must never synthesize L or R, for any tested gesture or mode.
    assert(!(a.buttons[0]&0x10) && !(a.buttons[1]&0x10));
    if(a.toggle_tag) {++f->tag_events;pa_device_present(&f->device,!f->device.presented);}
    if(a.toggle_config) {++f->config_events;f->config=!f->config;}
    if(a.buttons[0]&2) {
        ++f->a_ms;
        uint8_t report[63];pa_device_report(&f->device,f->now,a.buttons,report);
        assert(report[2]==2 && report[3]==0 && report[4]==0);
    }
    if(f->config) assert(a.buttons[0]==0 && a.buttons[1]==0 && a.buttons[2]==0);
}
static void run(fixture_t *f,bool raw,unsigned ms) { for(unsigned i=0;i<ms;++i) step(f,raw); }
static void double_tap(fixture_t *f) {
    run(f,true,100);run(f,false,100);run(f,true,100);run(f,false,700);
}
static void expect_double(fixture_t *f) {
    assert(f->a_ms==180 && f->tag_events==0 && f->config_events==0);
    assert(!f->input.a_active && !f->input.tap_pending);
}

int main(void) {
    fixture_t f;init(&f);run(&f,false,1000);
    assert(!f.tag_events && !f.config_events && !f.a_ms);

    init(&f);run(&f,true,100);run(&f,false,200);
    assert(f.tag_events==0 && f.a_ms==0); // first tap waits for a possible double
    run(&f,false,300);assert(f.tag_events==1 && f.device.presented);
    run(&f,true,100);run(&f,false,500);
    assert(f.tag_events==2 && !f.device.presented && !f.a_ms);

    init(&f);double_tap(&f);expect_double(&f);assert(!f.device.presented);
    init(&f);pa_device_present(&f.device,true);double_tap(&f);expect_double(&f);assert(f.device.presented);

    init(&f);run(&f,true,100);run(&f,false,600);run(&f,true,100);run(&f,false,600);
    assert(f.tag_events==2 && f.a_ms==0); // two separate single taps

    const unsigned ignored_holds[]={600,1000,1999};
    for(unsigned i=0;i<sizeof(ignored_holds)/sizeof(ignored_holds[0]);++i) {
        init(&f);run(&f,true,ignored_holds[i]);run(&f,false,600);
        assert(!f.a_ms && !f.tag_events && !f.config_events);
    }

    init(&f);run(&f,true,5000);run(&f,false,600);
    assert(f.config_events==1 && f.config && !f.a_ms && !f.tag_events);

    init(&f);f.config=true;double_tap(&f);run(&f,true,1000);run(&f,false,700);
    assert(!f.a_ms && !f.tag_events && !f.config_events);
    run(&f,true,2200);run(&f,false,700);
    assert(!f.config && f.config_events==1 && !f.a_ms && !f.tag_events);

    init(&f);
    for(unsigned i=0;i<10;++i) {run(&f,true,5);run(&f,false,5);}
    run(&f,false,600);assert(!f.a_ms && !f.tag_events && !f.config_events);

    init(&f);f.now=UINT32_MAX-250u;double_tap(&f);expect_double(&f);

    // A second physical press at the end of the window must not leak a single
    // tag toggle while it is being debounced.
    init(&f);run(&f,true,100);run(&f,false,30);
    while((uint32_t)(f.now-f.input.tap_released)<399u)step(&f,false);
    run(&f,true,100);run(&f,false,700);expect_double(&f);

    // A second tap which becomes a long hold opens config; it must not press A
    // or briefly present the tag before doing so.
    init(&f);run(&f,true,100);run(&f,false,100);run(&f,true,2500);run(&f,false,600);
    assert(f.config_events==1 && !f.a_ms && !f.tag_events);

    // An external mode transition cancels an unfinished single tap.
    init(&f);run(&f,true,100);run(&f,false,100);f.config=true;run(&f,false,700);
    f.config=false;run(&f,false,700);assert(!f.tag_events && !f.a_ms);

    puts("PASS BOOTSEL input: no synthetic L/R; double-tap A reaches HID then releases; single-tag toggle, ignored medium holds, config, bounce, deadline, mode cancellation, clock wrap");
    return 0;
}
