cmake_minimum_required(VERSION 3.20)
set(PICO_BOARD pico CACHE STRING "Only original Pico is supported")
if(NOT PICO_BOARD STREQUAL "pico")
    message(FATAL_ERROR "PicoAmiibo-RP2040 requires PICO_BOARD=pico")
endif()
set(PICO_NO_PICOTOOL 1)
include(pico_sdk_import.cmake)
project(PicoAmiiboRP2040 VERSION 0.1.2 LANGUAGES C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()
add_executable(picoamiibo
    src/main.c src/device.c src/identity.c src/store.c src/config.c src/input.c
    src/vendor/virtual_amiibo.c src/vendor/ns2_virtual_nfc.c
    src/vendor/ns2_virtual_nfc_runtime.c src/vendor/ns2_vendor_rx.c
    src/vendor/ns2_vendor_tx.c src/vendor/ns2_pairing_crypto.c
    src/vendor/ns2_firmware_profile.c)
target_include_directories(picoamiibo PRIVATE include)
target_link_libraries(picoamiibo pico_stdlib tinyusb_device tinyusb_board hardware_sync hardware_flash)
target_compile_options(picoamiibo PRIVATE -Wall -Wextra -Werror)
pico_enable_stdio_usb(picoamiibo 0)
pico_enable_stdio_uart(picoamiibo 0)
find_package(Git QUIET)
set(PA_BUILD_ID unknown)
if(GIT_FOUND)
    execute_process(COMMAND ${GIT_EXECUTABLE} rev-parse --short=12 HEAD
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} OUTPUT_VARIABLE PA_BUILD_ID OUTPUT_STRIP_TRAILING_WHITESPACE)
    execute_process(COMMAND ${GIT_EXECUTABLE} status --porcelain --untracked-files=normal
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} OUTPUT_VARIABLE PA_DIRTY OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(PA_DIRTY)
        string(APPEND PA_BUILD_ID "+dirty")
    endif()
endif()
target_compile_definitions(picoamiibo PRIVATE PA_BUILD_ID="${PA_BUILD_ID}" PA_VERSION="${PROJECT_VERSION}" PICO_NO_BI_PROGRAM_BUILD_DATE=1)
pico_set_program_version(picoamiibo "${PROJECT_VERSION}-${PA_BUILD_ID}")
pico_add_extra_outputs(picoamiibo)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
add_custom_command(TARGET picoamiibo POST_BUILD
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/tools/uf2.py pack
        ${CMAKE_CURRENT_BINARY_DIR}/picoamiibo.bin ${CMAKE_CURRENT_BINARY_DIR}/PicoAmiibo-RP2040-pico-empty.uf2 --replace-build-output
    VERBATIM)
