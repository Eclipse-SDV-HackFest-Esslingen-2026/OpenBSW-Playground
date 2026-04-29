# =====================================================================
# SOVD Demo — CMake Overlay for OpenBSW
#
# This project wraps the upstream openbsw/ build and adds a demo executable
# (app.sovdDemo.elf) that includes DTC simulation and SOVD-compatible UDS
# services — all without modifying openbsw/.
#
# Usage:
#   cmake --preset posix-freertos-sovd                # OpenBSW demo ECU
#   cmake --preset posix-freertos-sovd -DUSE_FLXC1000_ECU=ON  # FLXC1000 ECU
#   cmake --build build/posix-freertos-sovd
# ==========================================================================
cmake_minimum_required(VERSION 3.28 FATAL_ERROR)

# --- ECU Configuration Option (early, before project()) -------------------
option(USE_FLXC1000_ECU "Build with FLXC1000 ECU simulation" OFF)

# --- Locate OpenBSW ---------------------------------------------------------
set(OPENBSW_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/../openbsw"
    CACHE PATH "Path to the OpenBSW source tree")

if (NOT EXISTS "${OPENBSW_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "OpenBSW not found at ${OPENBSW_DIR}")
endif ()

# --- Load platform options BEFORE project() so compile definitions are set ---
set(BUILD_EXECUTABLE
    "referenceApp"
    CACHE STRING "Which build to enable" FORCE)
set(BUILD_TARGET_PLATFORM
    "POSIX"
    CACHE STRING "Target Platform" FORCE)
set(BUILD_TARGET_RTOS
    "FREERTOS"
    CACHE STRING "Target RTOS" FORCE)

project(
    sovdDemo
    VERSION 0.1.0
    DESCRIPTION "SOVD Demo overlay for OpenBSW"
    LANGUAGES C CXX ASM)

# --- Build the full OpenBSW tree (libraries + referenceApp) ------------------
add_subdirectory("${OPENBSW_DIR}" "${CMAKE_BINARY_DIR}/openbsw")

# --- Overlay: TransportConfiguration for FLXC1000/SOVD ----------------------
# Must be done BEFORE any target links to transportConfiguration
# This allows all requests (tester address 0x0000 from OpenSOVD CDA)
target_include_directories(
    transportConfiguration
    BEFORE INTERFACE
    "${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/transportConfiguration/include")

# --- Overlay: DoIP interop fix -----------------------------------------------
get_target_property(_doip_srcs doip SOURCES)
get_target_property(_doip_srcdir doip SOURCE_DIR)
list(FILTER _doip_srcs EXCLUDE REGEX "DoIpServerConnectionHandler\\.cpp$")
list(TRANSFORM _doip_srcs PREPEND "${_doip_srcdir}/")
set_target_properties(doip PROPERTIES SOURCES "")
target_sources(
    doip
    PRIVATE
        ${_doip_srcs}
        "${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/libs/doip/src/doip/server/DoIpServerConnectionHandler.cpp")

# --- Overlay: DTC/UDS library additions --------------------------------------
add_library(
    uds_dtc_overlay STATIC
    openbsw-overlay/libs/uds/src/services/readdtcinformation/ReadDTCInformation.cpp
    openbsw-overlay/libs/uds/src/services/cleardiagnosticinformation/ClearDiagnosticInformation.cpp)

target_include_directories(
    uds_dtc_overlay
    PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/libs/uds/include")

target_link_libraries(uds_dtc_overlay PUBLIC uds)

# --- Overlay: Demo executable ------------------------------------------------
set(REFAPP_SRC "${OPENBSW_DIR}/executables/referenceApp/application/src")
set(REFAPP_INC "${OPENBSW_DIR}/executables/referenceApp/application/include")

add_executable(
    app.sovdDemo
    ${REFAPP_SRC}/app/app.cpp
    ${REFAPP_SRC}/console/console.cpp
    ${REFAPP_SRC}/logger/logger.cpp
    ${REFAPP_SRC}/systems/DemoSystem.cpp
    ${REFAPP_SRC}/systems/RuntimeSystem.cpp
    ${REFAPP_SRC}/systems/SysAdminSystem.cpp
    ${REFAPP_SRC}/systems/SafetySystem.cpp
    ${REFAPP_SRC}/main.cpp)

# --- Conditional sources (match referenceApp pattern) ------------------------
if (PLATFORM_SUPPORT_TRANSPORT)
    target_sources(
        app.sovdDemo
        PRIVATE ${REFAPP_SRC}/systems/TransportSystem.cpp)

    if (PLATFORM_SUPPORT_UDS)
        # Shared UDS overlay sources (used by both OpenBSW demo and FLXC1000)
        target_sources(
            app.sovdDemo
            PRIVATE
                ${REFAPP_SRC}/uds/ReadIdentifierPot.cpp
                ${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/src/uds/ReadIdentifierSimulated.cpp)

        # ECU-specific sources
        if (USE_FLXC1000_ECU)
            message(STATUS "*** Building FLXC1000 ECU simulation ***")
            target_sources(
                app.sovdDemo
                PRIVATE
                    ${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/src/systems/Flxc1000UdsSystem.cpp
                    ${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/src/uds/Flxc1000Simulator.cpp)
            target_compile_definitions(app.sovdDemo PRIVATE USE_FLXC1000_ECU=1)
        else ()
            message(STATUS "*** Building OpenBSW demo ECU simulation ***")
            target_sources(
                app.sovdDemo
                PRIVATE
                    ${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/src/systems/UdsSystem.cpp
                    ${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/src/uds/DtcSimulator.cpp)
        endif ()
    endif ()
endif ()

if (PLATFORM_SUPPORT_ETHERNET)
    target_sources(app.sovdDemo PRIVATE ${REFAPP_SRC}/systems/EthernetSystem.cpp)
    if (PLATFORM_SUPPORT_TRANSPORT)
        target_sources(app.sovdDemo PRIVATE ${REFAPP_SRC}/systems/DoIpServerSystem.cpp)
    endif ()
endif ()

if (PLATFORM_SUPPORT_CAN)
    target_sources(app.sovdDemo PRIVATE ${REFAPP_SRC}/app/CanDemoListener.cpp)
    if (PLATFORM_SUPPORT_TRANSPORT)
        target_sources(app.sovdDemo PRIVATE ${REFAPP_SRC}/systems/DoCanSystem.cpp)
    endif ()
endif ()

if (PLATFORM_SUPPORT_STORAGE)
    target_sources(app.sovdDemo PRIVATE ${REFAPP_SRC}/systems/StorageSystem.cpp)
endif ()

set_target_properties(app.sovdDemo PROPERTIES SUFFIX ".elf")

# --- Compile definitions -----------------------------------------------------
target_compile_definitions(app.sovdDemo PRIVATE SUPPORT_FREERTOS)
get_cmake_property(_all_vars VARIABLES)
foreach (var ${_all_vars})
    if (var MATCHES "^PLATFORM_SUPPORT_")
        if (${var})
            target_compile_definitions(app.sovdDemo PRIVATE ${var}=1)
        endif ()
    endif ()
endforeach ()

# --- Include directories -----------------------------------------------------
# Overlay FIRST so our headers take precedence over upstream
target_include_directories(
    app.sovdDemo
    PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/include"
        "${REFAPP_INC}")

# For FLXC1000, also override appConfig.h (ECU logical address) and TransportConfiguration
if (USE_FLXC1000_ECU)
    target_include_directories(
        app.sovdDemo
        BEFORE PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/configuration/include"
        "${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/transportConfiguration/include")
endif ()

# --- Link libraries ----------------------------------------------------------
target_link_libraries(
    app.sovdDemo
    PRIVATE uds_dtc_overlay
            asyncBinding
            asyncConsole
            bspMcu
            configuration
            etl
            etlImpl
            lifecycle
            consoleCommands
            logger
            printf
            loggerIntegration
            main
            stdioConsoleInput
            osRtos
            asyncRtosImpl
            util
            runtime
            safeLifecycle
            safeUtils
            safeWatchdog
            bspUart
            socBsp)

if (PLATFORM_SUPPORT_TRANSPORT)
    target_link_libraries(app.sovdDemo PRIVATE transport transportRouterSimple)
    if (PLATFORM_SUPPORT_UDS)
        target_link_libraries(app.sovdDemo PRIVATE uds udsConfigurationImpl)
    endif ()
endif ()

if (PLATFORM_SUPPORT_CAN)
    target_link_libraries(app.sovdDemo PRIVATE cpp2can)
    if (PLATFORM_SUPPORT_TRANSPORT)
        target_link_libraries(app.sovdDemo PRIVATE docan)
    endif ()
endif ()

if (PLATFORM_SUPPORT_ETHERNET)
    target_link_libraries(
        app.sovdDemo PRIVATE cpp2ethernet lwipSocket lwipcore ethConfiguration)
    if (PLATFORM_SUPPORT_TRANSPORT)
        target_link_libraries(app.sovdDemo PRIVATE doip)
    endif ()
endif ()

if (PLATFORM_SUPPORT_STORAGE)
    target_link_libraries(app.sovdDemo PRIVATE storage)
endif ()

if (PLATFORM_SUPPORT_ROM_CHECK)
    target_link_libraries(app.sovdDemo PRIVATE safeMemory)
endif ()

if (TARGET startUp)
    get_target_property(LINKER_SCRIPT startUp PROP_LINKER_SCRIPT)
    if (DEFINED LINKER_SCRIPT)
        target_link_options(app.sovdDemo PRIVATE -T ${LINKER_SCRIPT})
    endif ()
endif ()
