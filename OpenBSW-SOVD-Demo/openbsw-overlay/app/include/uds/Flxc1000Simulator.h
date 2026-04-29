// Copyright 2025 Accenture.
// Auto-generated from FLXC1000.mdd - DO NOT EDIT

#pragma once

#include "uds/ReadIdentifierSimulated.h"
#include "uds/dtc/DiagnosticTroubleCode.h"
#include "uds/dtc/DiagnosticTroubleCodeStore.h"
#include "uds/services/readdtcinformation/ReadDTCInformation.h"
#include "uds/jobs/ReadIdentifierFromMemory.h"
#include "uds/jobs/WriteIdentifierToMemory.h"

#include <etl/array.h>
#include <platform/estdint.h>

namespace uds
{

/**
 * FLXC1000 ECU Simulator.
 *
 * Implements diagnostics from FLXC1000.mdd:
 * - 6 DTCs
 * - 4 DIDs including simulated FluxCapacitorPowerConsumption
 */
class Flxc1000Simulator : public IDtcProvider
{
public:
    // DTC codes (from MDD)
    static uint32_t const DTC_CODE1                 = 0x01E240U;
    static uint32_t const DTC_CODE3                 = 0x01E241U;
    static uint32_t const DTC_CODE4                 = 0x01E242U;
    static uint32_t const DTC_CODE5                 = 0x01E243U;
    static uint32_t const DTC_CODE6                 = 0x01E244U;
    static uint32_t const DTC_CODE2                 = 0x039447U;

    // DID identifiers (from MDD)
    static uint16_t const DID_IDENTIFICATION                            = 0xF100U;
    static uint16_t const DID_ACTIVE_DIAGNOSTIC_SESSION_DATA_IDENTIFIER = 0xF186U;
    static uint16_t const DID_VINDATA_IDENTIFIER                        = 0xF190U;
    static uint16_t const DID_FLUX_CAPACITOR_POWER_CONSUMPTION          = 0xF200U;

    static size_t const MAX_DTCS = 16U;

    Flxc1000Simulator();

    void init();
    void step();

    DiagnosticTroubleCodeStore<MAX_DTCS>& getDtcStore();

    // Simulated sensor DID
    ReadIdentifierSimulated& getFluxCapacitorPowerConsumption();

    // IDtcProvider interface
    uint8_t getStatusAvailabilityMask() const override;
    size_t countByStatusMask(uint8_t mask) const override;
    size_t getDtcCount() const override;
    DiagnosticTroubleCode const* getDtcByIndex(size_t index) const override;
    DiagnosticTroubleCode const* findDtcByNumber(uint32_t dtcNumber) const override;
    void clearAll() override;
    bool clearByNumber(uint32_t dtcNumber) override;

private:
    DiagnosticTroubleCodeStore<MAX_DTCS> _dtcStore;
    ReadIdentifierSimulated _fluxCapacitorPowerConsumption;
    uint32_t _stepCounter;
    uint32_t _rngState;
};

} // namespace uds
