#include <string.h>
#include "pico/stdlib.h"
#include "hardware/sync.h"
#include "hardware/structs/ioqspi.h"
#include "hardware/structs/sio.h"
#include "hardware/flash.h"
#include "tusb.h"
#include "pa_device.h"
#include "pa_identity.h"
#include "pa_config.h"
#include "pa_input.h"
#include "ns2_vendor_rx.h"
#include "ns2_vendor_tx.h"

// Public template is empty. tools/uf2.py replaces this complete, unique slot.
// No flash writes or automatic input on boot. Core 1 is never launched.
const uint8_t pa_preload[PA_SLOT_SIZE] __attribute__((used, aligned(16))) = PA_SLOT_MAGIC;
static const char pa_build_id[] __attribute__((used)) = "PicoAmiibo " PA_VERSION " " PA_BUILD_ID;
static pa_device_t device;
static ns2_vendor_rx_t rx;
static ns2_vendor_tx_t tx;
static bool mounted;
static uint32_t last_report_ms;
static pa_store_t store;
static pa_config_t config;
static bool config_mode;
static pa_input_t input;

static const tusb_desc_device_t config_device={
    .bLength=18,.bDescriptorType=TUSB_DESC_DEVICE,.bcdUSB=0x0200,
    .bDeviceClass=0xef,.bDeviceSubClass=2,.bDeviceProtocol=1,.bMaxPacketSize0=64,
    .idVendor=0xcafe,.idProduct=0x4013,.bcdDevice=0x0100,
    .iManufacturer=1,.iProduct=2,.iSerialNumber=3,.bNumConfigurations=1,
};
static const uint8_t config_descriptor[]={
    TUD_CONFIG_DESCRIPTOR(1,2,0,TUD_CONFIG_DESC_LEN+TUD_CDC_DESC_LEN,0,100),
    TUD_CDC_DESCRIPTOR(0,0,0x81,8,0x02,0x82,64),
};

static bool erase_bank(void *context,unsigned bank) {
    (void)context;
    if(bank>1) return false;
    uint32_t flags=save_and_disable_interrupts();
    flash_range_erase(PA_FLASH_BANK0+bank*PA_BANK_SIZE,PA_BANK_SIZE);
    restore_interrupts(flags);
    return true;
}
static bool program_page(void *context,unsigned bank,size_t offset,const uint8_t page[256]) {
    (void)context;
    if(bank>1 || offset%256 || offset+256>PA_BANK_SIZE) return false;
    uint32_t flags=save_and_disable_interrupts();
    flash_range_program(PA_FLASH_BANK0+bank*PA_BANK_SIZE+(uint32_t)offset,page,256);
    restore_interrupts(flags);
    return true;
}
static bool save_tag(void *context,const uint8_t *data,size_t size) {
    (void)context;
    return pa_store_save(&store,data,size,erase_bank,program_page,NULL);
}
static void set_config_mode(bool next) {
    tud_disconnect();
    sleep_ms(100);
    config_mode=next;
    mounted=false;
    pa_device_present(&device,false);
    pa_identity_init(); ns2_vendor_rx_init(&rx); ns2_vendor_tx_init(&tx);
    pa_config_init(&config,&device,&store,save_tag,NULL);
    tud_connect();
}

// Pico SDK BOOTSEL technique: sample flash CS from SRAM with IRQs disabled.
// No second core, DMA flash reads, or radio are active in this firmware.
static bool __no_inline_not_in_flash_func(bootsel_raw)(void) {
    uint32_t flags = save_and_disable_interrupts();
    hw_write_masked(&ioqspi_hw->io[1].ctrl,
        GPIO_OVERRIDE_LOW << IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_LSB,
        IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_BITS);
    for (volatile int i = 0; i < 1000; ++i) {}
    bool pressed = !(sio_hw->gpio_hi_in & (1u << 1));
    hw_write_masked(&ioqspi_hw->io[1].ctrl,
        GPIO_OVERRIDE_NORMAL << IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_LSB,
        IO_QSPI_GPIO_QSPI_SS_CTRL_OEOVER_BITS);
    restore_interrupts(flags);
    return pressed;
}

static bool input_buttons(uint32_t now, uint8_t buttons[3]) {
    static uint32_t last_sample;
    static bool raw_pressed;
    if ((uint32_t)(now-last_sample) >= 30) {
        last_sample = now;
        raw_pressed = bootsel_raw();
    }
    pa_input_actions_t actions;
    pa_input_step(&input,now,raw_pressed,config_mode,&actions);
    if(actions.toggle_tag) pa_device_present(&device,!device.presented);
    memcpy(buttons,actions.buttons,3);
    // Optional dry contacts to GND. Original Pico GPIOs only, internal pullups.
    if (!gpio_get(2)) buttons[0] |= 0x02; // A
    if (!gpio_get(3)) buttons[0] |= 0x01; // B
    if (!gpio_get(4)) buttons[1] |= 0x10; // L
    if (!gpio_get(5)) buttons[0] |= 0x10; // R
    return actions.toggle_config;
}

static void config_task(uint32_t now) {
    static bool exiting;
    static uint32_t exit_at;
    pa_config_tick(&config,now);
    if(config.output_size) {
        size_t count=config.output_size-config.output_offset;
        uint32_t available=tud_cdc_write_available();
        if(count>available)count=available;
        if(count) {
            config.output_offset+=tud_cdc_write(config.output+config.output_offset,(uint32_t)count);
            tud_cdc_write_flush();
        }
        if(config.output_offset==config.output_size) {config.output_size=0;config.output_offset=0;}
    }
    if(config.exit_requested && !config.output_size) {
        if(!exiting) {exiting=true;exit_at=now+100;}
        if((int32_t)(now-exit_at)>=0) {exiting=false;set_config_mode(false);}
        return;
    }
    exiting=false;
    while(!config.output_size && tud_cdc_available()) {
        uint8_t byte;
        if(tud_cdc_read(&byte,1)!=1) break;
        pa_config_feed(&config,now,byte);
    }
}

static size_t vendor_write(void *context, const uint8_t *data, size_t size) {
    (void)context;
    return tud_vendor_write(data, (uint32_t)size);
}
static void command(void *context, const uint8_t *data, size_t size) {
    (void)context;
    uint8_t reply[128];
    size_t n = pa_device_command(&device, to_ms_since_boot(get_absolute_time()), data, size, reply);
    if (n) ns2_vendor_tx_queue(&tx, reply, n);
}

uint8_t const *tud_descriptor_device_cb(void) {
    return config_mode ? (const uint8_t *)&config_device : ns2_device_descriptor();
}
uint8_t const *tud_descriptor_configuration_cb(uint8_t index) {
    (void)index; return config_mode ? config_descriptor : ns2_config_descriptor();
}
uint8_t const *tud_hid_descriptor_report_cb(uint8_t instance) {
    (void)instance; return ns2_hid_report_descriptor();
}
uint16_t const *tud_descriptor_string_cb(uint8_t index, uint16_t language) {
    (void)language;
    static uint16_t result[64];
    if (index == 0) { result[0]=0x0304; result[1]=0x0409; return result; }
    size_t count;
    const char **strings = ns2_string_table(&count);
    const char *config_strings[]={NULL,"PicoAmiibo","PicoAmiibo Config",pa_build_id};
    if(config_mode) {strings=config_strings;count=4;}
    if (index >= count) return NULL;
    size_t n = strlen(strings[index]);
    if (n > 63) n = 63;
    result[0] = (uint16_t)(0x0300 | (2*n+2));
    for (size_t i=0; i<n; ++i) result[i+1]=(uint8_t)strings[index][i];
    return result;
}
bool tud_vendor_control_xfer_cb(uint8_t port, uint8_t stage, tusb_control_request_t const *req) {
    if (stage != CONTROL_STAGE_SETUP) return true;
    if(config_mode) return false;
    // Nintendo identity requests. Windows auto-WinUSB descriptors are omitted;
    // normal HID enumeration works without binding a vendor driver.
    if (req->bmRequestType_bit.type != TUSB_REQ_TYPE_VENDOR) return false;
    if (req->bmRequestType_bit.direction == TUSB_DIR_IN) {
        size_t size;
        const uint8_t *data=pa_identity_ep0(req->bRequest, &size);
        return data && tud_control_xfer(port, req, (void *)data,
            (uint16_t)(req->wLength < size ? req->wLength : size));
    }
    if (req->bRequest == 4 && !req->wLength) return tud_control_status(port, req);
    return false;
}
uint16_t tud_hid_get_report_cb(uint8_t instance, uint8_t id, hid_report_type_t type,
                               uint8_t *buffer, uint16_t length) {
    (void)instance; (void)id; (void)type; (void)buffer; (void)length; return 0;
}
void tud_hid_set_report_cb(uint8_t instance, uint8_t id, hid_report_type_t type,
                           uint8_t const *buffer, uint16_t length) {
    (void)instance; (void)id; (void)type; (void)buffer; (void)length;
    // No rumble hardware attached.
}
void tud_mount_cb(void) {
    pa_identity_init();
    ns2_virtual_nfc_runtime_init(&device.nfc);
    ns2_vendor_rx_init(&rx); ns2_vendor_tx_init(&tx);
    mounted=true;
}
void tud_umount_cb(void) {
    mounted=false;
    pa_identity_init();
    ns2_virtual_nfc_runtime_init(&device.nfc);
    ns2_vendor_rx_init(&rx); ns2_vendor_tx_init(&tx);
}

int main(void) {
    (void)pa_build_id;
    gpio_init(PICO_DEFAULT_LED_PIN); gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
    for (uint pin=2; pin<=5; ++pin) {
        gpio_init(pin); gpio_set_dir(pin, GPIO_IN); gpio_pull_up(pin);
    }
    pa_device_init(&device);
    pa_input_init(&input);
    pa_store_init(&store,(const uint8_t *)(XIP_BASE+PA_FLASH_BANK0),
        (const uint8_t *)(XIP_BASE+PA_FLASH_BANK0+PA_BANK_SIZE));
    const uint8_t *slot=pa_store_slot(&store);
    pa_slot_load(&device,slot ? slot : pa_preload,PA_SLOT_SIZE);
    pa_config_init(&config,&device,&store,save_tag,NULL);
    ns2_vendor_rx_init(&rx); ns2_vendor_tx_init(&tx);
    tusb_init();
    for (;;) {
        tud_task();
        uint32_t now=to_ms_since_boot(get_absolute_time());
        uint8_t buttons[3];
        if(input_buttons(now,buttons)) set_config_mode(!config_mode);
        if(config_mode) {
            config_task(now);
            gpio_put(PICO_DEFAULT_LED_PIN,(now/100)%2);
            continue;
        }
        if (ns2_vendor_tx_pump(&tx, vendor_write, NULL)) tud_vendor_write_flush();
        // Read one byte at a time until a complete command produces a reply.
        // Stop immediately on backpressure: even coalesced commands cannot
        // overwrite a queued reply. USB OUT FIFO provides bounded backpressure.
        while (!ns2_vendor_tx_active(&tx) && tud_vendor_available()) {
            uint8_t byte;
            if (tud_vendor_read(&byte, 1) != 1) break;
            ns2_vendor_rx_feed(&rx, &byte, 1, command, NULL);
        }
        if (mounted && pa_identity_streaming() && (uint32_t)(now-last_report_ms)>=1 && tud_hid_ready()) {
            uint8_t report[63];
            // The console selects 0x09. Do not mislabel its layout as 0x05.
            if (pa_identity_report_id() == 9) {
                pa_device_report(&device, now, buttons, report);
                tud_hid_report(9, report, sizeof(report));
            }
            last_report_ms=now;
        }
        // Empty: two flashes/sec. Loaded/ejected: slow blink. Presented: solid.
        bool led = device.loaded ? ((now/700u)%2u != 0) : ((now/250u)%2u != 0);
        if (device.presented) led=true;
        // One short blackout on each real NFC command is observable without
        // adding a UART cable. It is not a substitute for console acceptance.
        static uint32_t seen_nfc,last_nfc;
        if(device.nfc_commands!=seen_nfc) {seen_nfc=device.nfc_commands;last_nfc=now;}
        if(seen_nfc && (uint32_t)(now-last_nfc)<80)led=false;
        gpio_put(PICO_DEFAULT_LED_PIN, led);
    }
}
