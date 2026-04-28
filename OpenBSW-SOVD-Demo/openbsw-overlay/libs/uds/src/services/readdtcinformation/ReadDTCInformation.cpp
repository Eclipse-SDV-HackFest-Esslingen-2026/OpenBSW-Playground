// Copyright 2025 Accenture.

#include "uds/services/readdtcinformation/ReadDTCInformation.h"

#include "uds/connection/IncomingDiagConnection.h"
#include "uds/session/DiagSession.h"

namespace uds
{

ReadDTCInformation::ReadDTCInformation(IDtcProvider& dtcProvider)
: Service(ServiceId::READ_DTC_INFORMATION, DiagSession::ALL_SESSIONS()), _dtcProvider(dtcProvider)
{ setDefaultDiagReturnCode(DiagReturnCode::ISO_SUBFUNCTION_NOT_SUPPORTED); }

DiagReturnCode::Type
ReadDTCInformation::verify(uint8_t const* const request, uint16_t const requestLength)
{
    DiagReturnCode::Type result = Service::verify(request, requestLength);
    if (result == DiagReturnCode::OK)
    {
        // Minimum: service ID (already stripped) + subfunction + at least 1 parameter byte
        if (requestLength < 2U)
        {
            result = DiagReturnCode::ISO_INVALID_FORMAT;
        }
    }
    return result;
}

DiagReturnCode::Type ReadDTCInformation::process(
    IncomingDiagConnection& connection, uint8_t const* const request, uint16_t const requestLength)
{
    uint8_t const subFunction = request[0] & 0x7FU; // Mask out suppress positive response bit

    switch (subFunction)
    {
        case REPORT_NUMBER_OF_DTC_BY_STATUS_MASK:
        {
            if (requestLength < 2U)
            {
                return DiagReturnCode::ISO_INVALID_FORMAT;
            }
            return processReportNumberOfDtcByStatusMask(connection, request[1]);
        }
        case REPORT_DTC_BY_STATUS_MASK:
        {
            if (requestLength < 2U)
            {
                return DiagReturnCode::ISO_INVALID_FORMAT;
            }
            return processReportDtcByStatusMask(connection, request[1]);
        }
        case REPORT_DTC_EXT_DATA_RECORD_BY_DTC_NUMBER:
        {
            return processReportDtcExtDataRecord(connection, request, requestLength);
        }
        default:
        {
            return DiagReturnCode::ISO_SUBFUNCTION_NOT_SUPPORTED;
        }
    }
}

DiagReturnCode::Type ReadDTCInformation::processReportNumberOfDtcByStatusMask(
    IncomingDiagConnection& connection, uint8_t const statusMask)
{
    PositiveResponse& response = connection.releaseRequestGetResponse();

    // Response: subfunction (0x01) + statusAvailabilityMask + DTCFormatIdentifier + DTCCount(2
    // bytes)
    uint8_t const availabilityMask = _dtcProvider.getStatusAvailabilityMask();

    // Apply availability mask to the requested mask
    uint8_t const effectiveMask = statusMask & availabilityMask;
    size_t const count          = _dtcProvider.countByStatusMask(effectiveMask);

    (void)response.appendUint8(REPORT_NUMBER_OF_DTC_BY_STATUS_MASK);
    (void)response.appendUint8(availabilityMask);
    (void)response.appendUint8(DTC_FORMAT_IDENTIFIER);
    (void)response.appendUint8(static_cast<uint8_t>((count >> 8U) & 0xFFU));
    (void)response.appendUint8(static_cast<uint8_t>(count & 0xFFU));

    (void)connection.sendPositiveResponseInternal(response.getLength(), *this);
    return DiagReturnCode::OK;
}

DiagReturnCode::Type ReadDTCInformation::processReportDtcByStatusMask(
    IncomingDiagConnection& connection, uint8_t const statusMask)
{
    PositiveResponse& response = connection.releaseRequestGetResponse();

    uint8_t const availabilityMask = _dtcProvider.getStatusAvailabilityMask();
    uint8_t const effectiveMask    = statusMask & availabilityMask;

    // Response: subfunction (0x02) + statusAvailabilityMask + [DTC(3 bytes) + statusByte]*
    (void)response.appendUint8(REPORT_DTC_BY_STATUS_MASK);
    (void)response.appendUint8(availabilityMask);

    size_t const dtcCount = _dtcProvider.getDtcCount();
    for (size_t i = 0U; i < dtcCount; ++i)
    {
        DiagnosticTroubleCode const* dtc = _dtcProvider.getDtcByIndex(i);
        if ((dtc != nullptr) && dtc->matchesStatusMask(effectiveMask))
        {
            (void)response.appendUint8(dtc->getDtcHighByte());
            (void)response.appendUint8(dtc->getDtcMiddleByte());
            (void)response.appendUint8(dtc->getDtcLowByte());
            (void)response.appendUint8(dtc->getStatusByte());
        }
    }

    (void)connection.sendPositiveResponseInternal(response.getLength(), *this);
    return DiagReturnCode::OK;
}

DiagReturnCode::Type ReadDTCInformation::processReportDtcExtDataRecord(
    IncomingDiagConnection& connection, uint8_t const* const request, uint16_t const requestLength)
{
    // Request: subfunction(0x06) + DTC(3 bytes) + DTCExtDataRecordNumber(1 byte)
    if (requestLength < 5U)
    {
        return DiagReturnCode::ISO_INVALID_FORMAT;
    }

    uint32_t const dtcNumber = (static_cast<uint32_t>(request[1]) << 16U)
                               | (static_cast<uint32_t>(request[2]) << 8U)
                               | static_cast<uint32_t>(request[3]);

    DiagnosticTroubleCode const* dtc = _dtcProvider.findDtcByNumber(dtcNumber);
    if (dtc == nullptr)
    {
        return DiagReturnCode::ISO_REQUEST_OUT_OF_RANGE;
    }

    PositiveResponse& response = connection.releaseRequestGetResponse();

    // Response: subfunction(0x06) + DTC(3 bytes) + statusByte + extDataRecordNumber + data
    (void)response.appendUint8(REPORT_DTC_EXT_DATA_RECORD_BY_DTC_NUMBER);
    (void)response.appendUint8(dtc->getDtcHighByte());
    (void)response.appendUint8(dtc->getDtcMiddleByte());
    (void)response.appendUint8(dtc->getDtcLowByte());
    (void)response.appendUint8(dtc->getStatusByte());
    // Extended data record number (echo request)
    (void)response.appendUint8(request[4]);
    // Extended data: occurrence counter (simulated as 1 if testFailed, 0 otherwise)
    uint8_t const occurrenceCounter
        = (dtc->getStatusByte() & DiagnosticTroubleCode::TEST_FAILED) != 0U ? 0x01U : 0x00U;
    (void)response.appendUint8(occurrenceCounter);

    (void)connection.sendPositiveResponseInternal(response.getLength(), *this);
    return DiagReturnCode::OK;
}

} // namespace uds
