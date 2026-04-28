// Copyright 2025 Accenture.

#pragma once

#include "uds/dtc/DiagnosticTroubleCode.h"

#include <platform/estdint.h>

namespace uds
{
/**
 * In-memory store for Diagnostic Trouble Codes.
 *
 * This is a simple, statically-allocated DTC store suitable for embedded use.
 * Template parameter N defines the maximum number of DTCs.
 */
template<size_t N>
class DiagnosticTroubleCodeStore
{
public:
    /**
     * Supported DTC status availability mask (all bits supported in this implementation).
     */
    static uint8_t const STATUS_AVAILABILITY_MASK = 0xFFU;

    DiagnosticTroubleCodeStore();

    /**
     * Add a DTC definition to the store.
     * \return true if added successfully, false if store is full.
     */
    bool addDtc(uint32_t dtcNumber, uint8_t initialStatus = 0U);

    /**
     * Get a DTC by index.
     * \return pointer to DTC, or nullptr if index out of range.
     */
    DiagnosticTroubleCode* getDtcByIndex(size_t index);

    DiagnosticTroubleCode const* getDtcByIndex(size_t index) const;

    /**
     * Find a DTC by its number.
     * \return pointer to DTC, or nullptr if not found.
     */
    DiagnosticTroubleCode* findDtcByNumber(uint32_t dtcNumber);

    DiagnosticTroubleCode const* findDtcByNumber(uint32_t dtcNumber) const;

    /**
     * Get the number of DTCs currently stored.
     */
    size_t getCount() const;

    /**
     * Get the maximum capacity.
     */
    size_t getCapacity() const;

    /**
     * Count DTCs matching a given status mask.
     */
    size_t countByStatusMask(uint8_t mask) const;

    /**
     * Clear all DTCs (reset their status).
     */
    void clearAll();

    /**
     * Clear a specific DTC by number.
     * \return true if found and cleared.
     */
    bool clearByNumber(uint32_t dtcNumber);

    /**
     * Get status availability mask.
     */
    uint8_t getStatusAvailabilityMask() const;

private:
    DiagnosticTroubleCode _dtcs[N];
    size_t _count;
};

// Template implementations

template<size_t N>
DiagnosticTroubleCodeStore<N>::DiagnosticTroubleCodeStore() : _dtcs{}, _count(0U)
{}

template<size_t N>
bool DiagnosticTroubleCodeStore<N>::addDtc(uint32_t const dtcNumber, uint8_t const initialStatus)
{
    if (_count >= N)
    {
        return false;
    }
    _dtcs[_count] = DiagnosticTroubleCode(dtcNumber, initialStatus);
    ++_count;
    return true;
}

template<size_t N>
DiagnosticTroubleCode* DiagnosticTroubleCodeStore<N>::getDtcByIndex(size_t const index)
{
    if (index < _count)
    {
        return &_dtcs[index];
    }
    return nullptr;
}

template<size_t N>
DiagnosticTroubleCode const* DiagnosticTroubleCodeStore<N>::getDtcByIndex(size_t const index) const
{
    if (index < _count)
    {
        return &_dtcs[index];
    }
    return nullptr;
}

template<size_t N>
DiagnosticTroubleCode* DiagnosticTroubleCodeStore<N>::findDtcByNumber(uint32_t const dtcNumber)
{
    for (size_t i = 0U; i < _count; ++i)
    {
        if (_dtcs[i].getDtcNumber() == dtcNumber)
        {
            return &_dtcs[i];
        }
    }
    return nullptr;
}

template<size_t N>
DiagnosticTroubleCode const*
DiagnosticTroubleCodeStore<N>::findDtcByNumber(uint32_t const dtcNumber) const
{
    for (size_t i = 0U; i < _count; ++i)
    {
        if (_dtcs[i].getDtcNumber() == dtcNumber)
        {
            return &_dtcs[i];
        }
    }
    return nullptr;
}

template<size_t N>
size_t DiagnosticTroubleCodeStore<N>::getCount() const
{ return _count; }

template<size_t N>
size_t DiagnosticTroubleCodeStore<N>::getCapacity() const
{ return N; }

template<size_t N>
size_t DiagnosticTroubleCodeStore<N>::countByStatusMask(uint8_t const mask) const
{
    size_t count = 0U;
    for (size_t i = 0U; i < _count; ++i)
    {
        if (_dtcs[i].matchesStatusMask(mask))
        {
            ++count;
        }
    }
    return count;
}

template<size_t N>
void DiagnosticTroubleCodeStore<N>::clearAll()
{
    for (size_t i = 0U; i < _count; ++i)
    {
        _dtcs[i].clear();
    }
}

template<size_t N>
bool DiagnosticTroubleCodeStore<N>::clearByNumber(uint32_t const dtcNumber)
{
    DiagnosticTroubleCode* dtc = findDtcByNumber(dtcNumber);
    if (dtc != nullptr)
    {
        dtc->clear();
        return true;
    }
    return false;
}

template<size_t N>
uint8_t DiagnosticTroubleCodeStore<N>::getStatusAvailabilityMask() const
{ return STATUS_AVAILABILITY_MASK; }

} // namespace uds
