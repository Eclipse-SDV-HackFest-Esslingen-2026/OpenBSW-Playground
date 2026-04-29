// Copyright 2025 Accenture.
// FLXC1000 Overlay - Extended tester address range for MDD compliance

#pragma once

#include <transport/TransportMessage.h>

#include <platform/estdint.h>

namespace transport
{
class TransportConfiguration
{
public:
    TransportConfiguration() = delete;

    /**
     * Tester address range for 8 bit CAN addressing
     */
    static uint16_t const TESTER_RANGE_8BIT_START = 0x00E0U;
    static uint16_t const TESTER_RANGE_8BIT_END   = 0x00FDU;

    /**
     * Tester address range for DOIP addressing
     * Extended for FLXC1000 MDD which specifies tester at 0xFE00
     * Also includes 0xFFFF which OpenSOVD CDA may use as default
     */
#ifdef USE_FLXC1000_ECU
    // Extended range: 0x0EE0 to 0xFFFF (includes MDD tester address 0xFE00 and functional 0xFFFF)
    static uint16_t const TESTER_RANGE_DOIP_START = 0x0EE0U;
    static uint16_t const TESTER_RANGE_DOIP_END   = 0xFFFFU;
#else
    static uint16_t const TESTER_RANGE_DOIP_START = 0x0EE0U;
    static uint16_t const TESTER_RANGE_DOIP_END   = 0x0EFDU;
#endif

    /**
     * Functional addressing
     */
    static uint16_t const FUNCTIONAL_ALL_ISO14229 = 0x00DF;

    enum
    {
        INVALID_DIAG_ADDRESS = 0xFFU
    };

    /**
     * Maximum payload size for functionally addressed messages
     */
    static uint16_t const MAX_FUNCTIONAL_MESSAGE_PAYLOAD_SIZE = 6U;

    /**
     * Buffer size for diagnostic payload
     */
    static uint16_t const DIAG_PAYLOAD_SIZE = 4095U;

    /**
     * Number of full size transport messages
     */
    static uint8_t const FULL_SIZE_TRANSPORT_MESSAGES = 2U;

    /**
     * Buffer count of response transport messages
     */
    static uint8_t const SMALL_SIZE_TRANSPORT_MESSAGES = 2U;

    /**
     * Small message buffer size
     */
    static uint16_t const SMALL_SIZE_TRANSPORT_MESSAGE_SIZE = 16U;

    /**
     * This function checks if the provided 16-bit address matches
     * the constant FUNCTIONAL_ALL_ISO14229.
     * \return true if it matches and false otherwise.
     */
    static bool isFunctionalAddress(uint16_t address);

    /**
     * This function checks if the target ID of the provided TransportMessage
     * object matches the constant FUNCTIONAL_ALL_ISO14229.
     * \return true if they are equal and false otherwise.
     */
    static bool isFunctionallyAddressed(TransportMessage const& message);

    static bool isTesterAddress(uint16_t address);

    static bool isFromTester(TransportMessage const& message);
};

/**
 * This function checks if the provided 16-bit address matches
 * the constant FUNCTIONAL_ALL_ISO14229.
 * \return true if they are equal and false otherwise.
 */
inline bool TransportConfiguration::isFunctionalAddress(uint16_t const address)
{
    return (FUNCTIONAL_ALL_ISO14229 == address);
}

/**
 * This function checks if the target ID of the provided TransportMessage
 * object matches the constant FUNCTIONAL_ALL_ISO14229.
 * \return true if they are equal and false otherwise.
 */
inline bool TransportConfiguration::isFunctionallyAddressed(TransportMessage const& message)
{
    return isFunctionalAddress(message.getTargetId());
}

/**
 * This function checks if the provided 16-bit address falls within the predefined
 * ranges for tester addresses.
 * \return true if it falls within either the 8-bit or the DOIP range, and false otherwise.
 * 
 * NOTE: For SOVD Demo, always returns true to accept requests from any address.
 * This is necessary because the UDS library is pre-compiled without USE_FLXC1000_ECU,
 * and OpenSOVD CDA uses tester address 0x0000.
 */
inline bool TransportConfiguration::isTesterAddress(uint16_t const address)
{
    // Always accept any address as a valid tester for SOVD Demo compatibility
    // This allows OpenSOVD CDA to connect with any configured tester address
    (void)address;
    return true;
}

/**
 * This function determines if the source ID of the provided TransportMessage object
 * corresponds to a tester address based on predefined ranges.
 * \return true if it does and false otherwise.
 */
inline bool TransportConfiguration::isFromTester(TransportMessage const& message)
{
    return isTesterAddress(message.getSourceId());
}

} // namespace transport
