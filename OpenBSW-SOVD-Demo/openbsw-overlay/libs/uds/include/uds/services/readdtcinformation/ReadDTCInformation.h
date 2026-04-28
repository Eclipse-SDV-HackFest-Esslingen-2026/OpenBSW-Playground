// Copyright 2025 Accenture.

#pragma once

#include "uds/base/Service.h"
#include "uds/dtc/DiagnosticTroubleCode.h"

namespace uds
{
/**
 * Interface for providing DTC data to UDS services.
 *
 * This decouples the UDS service from the concrete DTC store implementation.
 */
class IDtcProvider
{
public:
    virtual ~IDtcProvider() = default;

    /**
     * Get the DTC status availability mask.
     */
    virtual uint8_t getStatusAvailabilityMask() const = 0;

    /**
     * Get the count of DTCs matching a status mask.
     */
    virtual size_t countByStatusMask(uint8_t mask) const = 0;

    /**
     * Get the total number of stored DTCs.
     */
    virtual size_t getDtcCount() const = 0;

    /**
     * Get a DTC by index.
     * \return pointer to DTC or nullptr if out of range.
     */
    virtual DiagnosticTroubleCode const* getDtcByIndex(size_t index) const = 0;

    /**
     * Find a DTC by its 3-byte number.
     * \return pointer to DTC or nullptr if not found.
     */
    virtual DiagnosticTroubleCode const* findDtcByNumber(uint32_t dtcNumber) const = 0;

    /**
     * Clear all DTCs.
     */
    virtual void clearAll() = 0;

    /**
     * Clear a specific DTC by number.
     * \return true if found and cleared.
     */
    virtual bool clearByNumber(uint32_t dtcNumber) = 0;
};

/**
 * UDS service ReadDTCInformation (0x19) per ISO 14229-1.
 *
 * Supported subfunctions:
 *  - 0x01: reportNumberOfDTCByStatusMask
 *  - 0x02: reportDTCByStatusMask
 *  - 0x06: reportDTCExtDataRecordByDTCNumber
 */
class ReadDTCInformation : public Service
{
public:
    /**
     * Subfunction IDs per ISO 14229-1.
     */
    enum SubFunction : uint8_t
    {
        REPORT_NUMBER_OF_DTC_BY_STATUS_MASK      = 0x01U,
        REPORT_DTC_BY_STATUS_MASK                = 0x02U,
        REPORT_DTC_EXT_DATA_RECORD_BY_DTC_NUMBER = 0x06U
    };

    /**
     * DTC format identifier (ISO 14229-1: ISO 14229-1 DTC format).
     */
    static uint8_t const DTC_FORMAT_IDENTIFIER = 0x01U;

    /**
     * Constructor.
     * \param dtcProvider reference to a DTC provider for accessing DTC data.
     */
    explicit ReadDTCInformation(IDtcProvider& dtcProvider);

private:
    DiagReturnCode::Type verify(uint8_t const request[], uint16_t requestLength) override;

    DiagReturnCode::Type process(
        IncomingDiagConnection& connection,
        uint8_t const request[],
        uint16_t requestLength) override;

    DiagReturnCode::Type
    processReportNumberOfDtcByStatusMask(IncomingDiagConnection& connection, uint8_t statusMask);

    DiagReturnCode::Type
    processReportDtcByStatusMask(IncomingDiagConnection& connection, uint8_t statusMask);

    DiagReturnCode::Type processReportDtcExtDataRecord(
        IncomingDiagConnection& connection, uint8_t const request[], uint16_t requestLength);

    IDtcProvider& _dtcProvider;
};

} // namespace uds
