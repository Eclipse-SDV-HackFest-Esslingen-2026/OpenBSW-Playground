# =====================================================================
# SOVD Demo — CMake Overlay for OpenBSW
#
# This project wraps the upstream openbsw/ build and adds a demo executable
# (app.sovdDemo.elf) that includes DTC simulation and SOVD-compatible UDS
# services — all without modifying openbsw/.
#
# Usage:
#   cmake --preset posix-freertos-sovd
#   cmake --build build/posix-freertos-sovd
# ==========================================================================
cmake_minimum_required(VERSION 3.28 FATAL_ERROR)

# --- Locate OpenBSW ---------------------------------------------------------
set(OPENBSW_DIR
    "${CMAKE_CURRENT_SOURCE_DIR}/../openbsw"
    CACHE PATH "Path to the OpenBSW source tree")

if (NOT EXISTS "${OPENBSW_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "OpenBSW not found at ${OPENBSW_DIR}")
endif ()

# --- Load platform options BEFORE project() so compile definitions are set ---
# The referenceApp preset sets BUILD_EXECUTABLE=referenceApp, which triggers
# Options.cmake inclusion inside the openbsw root CMakeLists.
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

# --- Overlay: DoIP interop fix -----------------------------------------------
# The upstream DoIpServerConnectionHandler::headerReceived() does not handle
# DiagnosticMessagePositiveAck (0x8002) / NegativeAck (0x8003) payload types
# sent by the tester (e.g. Eclipse OpenSOVD CDA), causing a Generic NACK 0x01.
# Our overlay adds a case to silently consume these payloads.
#
# Fix location: openbsw-overlay/libs/doip/src/doip/server/
#               DoIpServerConnectionHandler.cpp  lines 284-290
#
# Technique: remove the upstream source from the doip target's SOURCES property,
# then inject our patched copy into the same 'doip' library target.
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
# These are generic ISO 14229 implementations that augment the upstream uds lib.
add_library(
    uds_dtc_overlay STATIC
    openbsw-overlay/libs/uds/src/services/readdtcinformation/ReadDTCInformation.cpp
    openbsw-overlay/libs/uds/src/services/cleardiagnosticinformation/ClearDiagnosticInformation.cpp)

target_include_directories(
    uds_dtc_overlay
    PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/libs/uds/include")

target_link_libraries(uds_dtc_overlay PUBLIC uds)

# --- Overlay: Demo executable ------------------------------------------------
# Mirrors app.referenceApp but compiles our own UdsSystem (with DTC support)
# and the demo-specific simulation sources.

set(REFAPP_SRC "${OPENBSW_DIR}/executables/referenceApp/application/src")
set(REFAPP_INC "${OPENBSW_DIR}/executables/referenceApp/application/include")

add_executable(
    app.sovdDemo
    # Core application sources (from upstream referenceApp, unchanged)
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
        target_sources(
            app.sovdDemo
            PRIVATE
                # Demo overlay UdsSystem (replaces the upstream one)
                ${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/src/systems/UdsSystem.cpp
                # Upstream ReadIdentifierPot (unchanged)
                ${REFAPP_SRC}/uds/ReadIdentifierPot.cpp
                # Demo overlay sources
                ${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/src/uds/ReadIdentifierSimulated.cpp
                ${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/src/uds/DtcSimulator.cpp)
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

# --- Compile definitions (mirror OpenBSW root scope) -------------------------
# OpenBSW sets these via add_compile_definitions() at directory scope, which
# only applies within its own subdirectory.  We must propagate them explicitly.
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
# Overlay FIRST so that our UdsSystem.h / DtcSimulator.h etc. take precedence.
target_include_directories(
    app.sovdDemo
    PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/openbsw-overlay/app/include"
        "${REFAPP_INC}")

# --- Link libraries (mirrors app.referenceApp exactly) -----------------------
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
