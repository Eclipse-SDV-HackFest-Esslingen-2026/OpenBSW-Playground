// Copyright 2025 Accenture.

#pragma once

#include "platform/estdint.h"
#include "uds/jobs/DataIdentifierJob.h"

namespace uds
{
/**
 * A ReadDataByIdentifier job that returns a simulated sensor value.
 *
 * The value changes over time using a simple pseudo-random walk within
 * configurable bounds. Ideal for hackathon demos showing live diagnostic data.
 */
class ReadIdentifierSimulated : public DataIdentifierJob
{
public:
    /**
     * Constructor.
     * \param identifier The 2-byte DID (e.g., 0xCF10)
     * \param initialValue Starting value for the simulated sensor
     * \param minValue Lower bound for the simulated sensor
     * \param maxValue Upper bound for the simulated sensor
     * \param sessionMask Sessions in which this DID is available
     */
    ReadIdentifierSimulated(
        uint16_t identifier,
        uint32_t initialValue,
        uint32_t minValue,
        uint32_t maxValue,
        DiagSessionMask sessionMask = DiagSession::ALL_SESSIONS());

    /**
     * Advance the simulation one step (call periodically from a cyclic task).
     */
    void step();

    /**
     * Get the current simulated value.
     */
    uint32_t getCurrentValue() const;

    /**
     * Force-set the value (e.g., for console commands or test injection).
     */
    void setValue(uint32_t value);

private:
    DiagReturnCode::Type process(
        IncomingDiagConnection& connection,
        uint8_t const request[],
        uint16_t requestLength) override;

    uint8_t _implementedRequest[3];
    uint32_t _currentValue;
    uint32_t _minValue;
    uint32_t _maxValue;
    uint32_t _seed;
};

} // namespace uds
