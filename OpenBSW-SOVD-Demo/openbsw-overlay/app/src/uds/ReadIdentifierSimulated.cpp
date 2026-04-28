// Copyright 2025 Accenture.

#include "uds/ReadIdentifierSimulated.h"

#include "uds/connection/IncomingDiagConnection.h"

#include <etl/unaligned_type.h>

namespace uds
{

ReadIdentifierSimulated::ReadIdentifierSimulated(
    uint16_t const identifier,
    uint32_t const initialValue,
    uint32_t const minValue,
    uint32_t const maxValue,
    DiagSessionMask const sessionMask)
: DataIdentifierJob(_implementedRequest, sessionMask)
, _currentValue(initialValue)
, _minValue(minValue)
, _maxValue(maxValue)
, _seed(identifier * 7U + 13U) // Simple seed from identifier
{
    _implementedRequest[0] = 0x22U;
    _implementedRequest[1] = static_cast<uint8_t>((identifier >> 8U) & 0xFFU);
    _implementedRequest[2] = static_cast<uint8_t>(identifier & 0xFFU);
}

void ReadIdentifierSimulated::step()
{
    // Simple linear congruential generator for pseudo-random walk
    _seed              = (_seed * 1103515245U + 12345U);
    uint32_t const rnd = (_seed >> 16U) & 0x7FFFU;

    // Random step: -2, -1, 0, +1, +2 weighted toward center
    int32_t const delta = static_cast<int32_t>(rnd % 5U) - 2;
    int32_t newValue    = static_cast<int32_t>(_currentValue) + delta;

    if (newValue < static_cast<int32_t>(_minValue))
    {
        newValue = static_cast<int32_t>(_minValue);
    }
    if (newValue > static_cast<int32_t>(_maxValue))
    {
        newValue = static_cast<int32_t>(_maxValue);
    }
    _currentValue = static_cast<uint32_t>(newValue);
}

uint32_t ReadIdentifierSimulated::getCurrentValue() const { return _currentValue; }

void ReadIdentifierSimulated::setValue(uint32_t const value)
{
    _currentValue = value;
    if (_currentValue < _minValue)
    {
        _currentValue = _minValue;
    }
    if (_currentValue > _maxValue)
    {
        _currentValue = _maxValue;
    }
}

DiagReturnCode::Type ReadIdentifierSimulated::process(
    IncomingDiagConnection& connection,
    uint8_t const* const /* request */,
    uint16_t const /* requestLength */)
{
    PositiveResponse& response = connection.releaseRequestGetResponse();

    ::etl::be_int32_t responseValue(static_cast<int32_t>(_currentValue));
    (void)response.appendData(static_cast<uint8_t*>(responseValue.data()), responseValue.size());
    (void)connection.sendPositiveResponseInternal(response.getLength(), *this);

    return DiagReturnCode::OK;
}

} // namespace uds
