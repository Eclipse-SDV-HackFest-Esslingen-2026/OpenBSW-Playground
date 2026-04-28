// Copyright 2025 Accenture.

#pragma once

#include "platform/estdint.h"

namespace uds
{
/**
 * Represents a single Diagnostic Trouble Code (DTC) per ISO 14229.
 *
 * Each DTC has a 3-byte DTC number and a status byte per ISO 14229-1 Annex D.
 */
class DiagnosticTroubleCode
{
public:
    /**
     * DTC status bit definitions per ISO 14229-1 Annex D.
     */
    enum StatusBit : uint8_t
    {
        TEST_FAILED                           = 0x01U,
        TEST_FAILED_THIS_OPERATION_CYCLE      = 0x02U,
        PENDING_DTC                           = 0x04U,
        CONFIRMED_DTC                         = 0x08U,
        TEST_NOT_COMPLETED_SINCE_LAST_CLEAR   = 0x10U,
        TEST_FAILED_SINCE_LAST_CLEAR          = 0x20U,
        TEST_NOT_COMPLETED_THIS_OPERATION_CYC = 0x40U,
        WARNING_INDICATOR_REQUESTED           = 0x80U
    };

    DiagnosticTroubleCode();

    DiagnosticTroubleCode(uint32_t dtcNumber, uint8_t initialStatus);

    /**
     * Get the 3-byte DTC number (only lower 24 bits used).
     */
    uint32_t getDtcNumber() const;

    /**
     * Get the DTC high byte.
     */
    uint8_t getDtcHighByte() const;

    /**
     * Get the DTC middle byte.
     */
    uint8_t getDtcMiddleByte() const;

    /**
     * Get the DTC low byte.
     */
    uint8_t getDtcLowByte() const;

    /**
     * Get the current status byte.
     */
    uint8_t getStatusByte() const;

    /**
     * Set a status bit.
     */
    void setStatusBit(uint8_t bit);

    /**
     * Clear a status bit.
     */
    void clearStatusBit(uint8_t bit);

    /**
     * Set entire status byte.
     */
    void setStatusByte(uint8_t status);

    /**
     * Check if this DTC matches a status mask (any bit in mask matches any bit in status).
     */
    bool matchesStatusMask(uint8_t mask) const;

    /**
     * Clear the DTC (reset status to initial cleared state).
     */
    void clear();

    /**
     * Check if this DTC is active (has any status bits set).
     */
    bool isActive() const;

private:
    uint32_t _dtcNumber;
    uint8_t _statusByte;
};

// Inline implementations

inline DiagnosticTroubleCode::DiagnosticTroubleCode() : _dtcNumber(0U), _statusByte(0U) {}

inline DiagnosticTroubleCode::DiagnosticTroubleCode(
    uint32_t const dtcNumber, uint8_t const initialStatus)
: _dtcNumber(dtcNumber & 0x00FFFFFFU), _statusByte(initialStatus)
{}

inline uint32_t DiagnosticTroubleCode::getDtcNumber() const { return _dtcNumber; }

inline uint8_t DiagnosticTroubleCode::getDtcHighByte() const
{ return static_cast<uint8_t>((_dtcNumber >> 16U) & 0xFFU); }

inline uint8_t DiagnosticTroubleCode::getDtcMiddleByte() const
{ return static_cast<uint8_t>((_dtcNumber >> 8U) & 0xFFU); }

inline uint8_t DiagnosticTroubleCode::getDtcLowByte() const
{ return static_cast<uint8_t>(_dtcNumber & 0xFFU); }

inline uint8_t DiagnosticTroubleCode::getStatusByte() const { return _statusByte; }

inline void DiagnosticTroubleCode::setStatusBit(uint8_t const bit) { _statusByte |= bit; }

inline void DiagnosticTroubleCode::clearStatusBit(uint8_t const bit)
{ _statusByte &= static_cast<uint8_t>(~bit); }

inline void DiagnosticTroubleCode::setStatusByte(uint8_t const status) { _statusByte = status; }

inline bool DiagnosticTroubleCode::matchesStatusMask(uint8_t const mask) const
{ return (_statusByte & mask) != 0U; }

inline void DiagnosticTroubleCode::clear()
{ _statusByte = TEST_NOT_COMPLETED_SINCE_LAST_CLEAR | TEST_NOT_COMPLETED_THIS_OPERATION_CYC; }

inline bool DiagnosticTroubleCode::isActive() const { return _statusByte != 0U; }

} // namespace uds
