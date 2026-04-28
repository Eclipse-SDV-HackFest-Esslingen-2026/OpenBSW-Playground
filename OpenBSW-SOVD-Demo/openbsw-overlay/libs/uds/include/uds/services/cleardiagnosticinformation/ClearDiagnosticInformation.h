// Copyright 2025 Accenture.

#pragma once

#include "uds/base/Service.h"
#include "uds/services/readdtcinformation/ReadDTCInformation.h"

namespace uds
{
/**
 * UDS service ClearDiagnosticInformation (0x14) per ISO 14229-1.
 *
 * Clears DTCs from the DTC store. Supports clearing all DTCs (groupOfDTC = 0xFFFFFF)
 * or a specific DTC by its 3-byte number.
 */
class ClearDiagnosticInformation : public Service
{
public:
    /**
     * Group of DTC value for "all DTCs".
     */
    static uint32_t const GROUP_OF_ALL_DTCS = 0xFFFFFFU;

    /**
     * Constructor.
     * \param dtcProvider reference to a DTC provider for clearing DTC data.
     */
    explicit ClearDiagnosticInformation(IDtcProvider& dtcProvider);

private:
    static uint8_t const EXPECTED_REQUEST_LENGTH = 3U;

    DiagReturnCode::Type verify(uint8_t const request[], uint16_t requestLength) override;

    DiagReturnCode::Type process(
        IncomingDiagConnection& connection,
        uint8_t const request[],
        uint16_t requestLength) override;

    IDtcProvider& _dtcProvider;
};

} // namespace uds
