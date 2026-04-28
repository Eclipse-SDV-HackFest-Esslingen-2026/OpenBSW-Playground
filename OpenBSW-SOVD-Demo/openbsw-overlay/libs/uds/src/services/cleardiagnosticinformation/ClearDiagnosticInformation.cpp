// Copyright 2025 Accenture.

#include "uds/services/cleardiagnosticinformation/ClearDiagnosticInformation.h"

#include "uds/connection/IncomingDiagConnection.h"
#include "uds/session/DiagSession.h"

namespace uds
{

ClearDiagnosticInformation::ClearDiagnosticInformation(IDtcProvider& dtcProvider)
: Service(ServiceId::CLEAR_DIAGNOSTIC_INFORMATION, DiagSession::ALL_SESSIONS())
, _dtcProvider(dtcProvider)
{ setDefaultDiagReturnCode(DiagReturnCode::ISO_REQUEST_OUT_OF_RANGE); }

DiagReturnCode::Type
ClearDiagnosticInformation::verify(uint8_t const* const request, uint16_t const requestLength)
{
    DiagReturnCode::Type result = Service::verify(request, requestLength);
    if (result == DiagReturnCode::OK)
    {
        // Request must contain exactly 3 bytes (groupOfDTC)
        if (requestLength != EXPECTED_REQUEST_LENGTH)
        {
            result = DiagReturnCode::ISO_INVALID_FORMAT;
        }
    }
    return result;
}

DiagReturnCode::Type ClearDiagnosticInformation::process(
    IncomingDiagConnection& connection,
    uint8_t const* const request,
    uint16_t const /* requestLength */)
{
    uint32_t const groupOfDtc = (static_cast<uint32_t>(request[0]) << 16U)
                                | (static_cast<uint32_t>(request[1]) << 8U)
                                | static_cast<uint32_t>(request[2]);

    if (groupOfDtc == GROUP_OF_ALL_DTCS)
    {
        _dtcProvider.clearAll();
    }
    else
    {
        if (!_dtcProvider.clearByNumber(groupOfDtc))
        {
            return DiagReturnCode::ISO_REQUEST_OUT_OF_RANGE;
        }
    }

    // Service 0x14 sends an empty positive response (no sub-function, no data)
    PositiveResponse& response = connection.releaseRequestGetResponse();
    (void)connection.sendPositiveResponseInternal(response.getLength(), *this);
    return DiagReturnCode::OK;
}

} // namespace uds
