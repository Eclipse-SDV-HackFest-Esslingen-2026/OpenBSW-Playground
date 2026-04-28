// Copyright 2025 Accenture.

#pragma once

#include "uds/ReadIdentifierSimulated.h"
#include "uds/dtc/DiagnosticTroubleCode.h"
#include "uds/dtc/DiagnosticTroubleCodeStore.h"
#include "uds/services/readdtcinformation/ReadDTCInformation.h"

#include <platform/estdint.h>

namespace uds
{
/**
 * DTC Simulator for hackathon demos.
 *
 * This module:
 * - Owns a DTC store with pre-defined demo DTCs
 * - Implements IDtcProvider for the ReadDTCInformation and ClearDiagnosticInformation services
 * - Periodically toggles DTC status bits to simulate a live vehicle
 * - Steps simulated sensor values (engine temp, battery voltage, vehicle speed)
 *
 * Call step() from a periodic task (e.g., every 500ms–1000ms).
 */
class DtcSimulator : public IDtcProvider
{
public:
    /**
     * Demo DTC numbers (ISO 14229 format: 3 bytes).
     */
    static uint32_t const DTC_ENGINE_OVERTEMP     = 0x010100U;
    static uint32_t const DTC_BATTERY_VOLTAGE_LOW = 0x010200U;
    static uint32_t const DTC_COMMUNICATION_FAULT = 0x010300U;
    static uint32_t const DTC_SENSOR_MALFUNCTION  = 0x010400U;
    static uint32_t const DTC_BRAKE_SYSTEM_FAULT  = 0x010500U;

    /**
     * Demo DID identifiers.
     */
    static uint16_t const DID_ENGINE_TEMP   = 0xCF10U;
    static uint16_t const DID_BATTERY_VOLT  = 0xCF11U;
    static uint16_t const DID_VEHICLE_SPEED = 0xCF12U;

    static size_t const MAX_DTCS = 16U;

    DtcSimulator();

    /**
     * Initialize the simulator with demo DTCs and sensor values.
     */
    void init();

    /**
     * Advance the simulation one step. Call periodically (e.g., every 500ms).
     * Randomly toggles DTC status bits and updates simulated sensor values.
     */
    void step();

    /**
     * Get the DTC store (for direct access if needed).
     */
    DiagnosticTroubleCodeStore<MAX_DTCS>& getDtcStore();

    /**
     * Get the simulated sensor DID jobs (for registering with UdsSystem).
     */
    ReadIdentifierSimulated& getEngineTemp();
    ReadIdentifierSimulated& getBatteryVoltage();
    ReadIdentifierSimulated& getVehicleSpeed();

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
    ReadIdentifierSimulated _engineTemp;
    ReadIdentifierSimulated _batteryVoltage;
    ReadIdentifierSimulated _vehicleSpeed;
    uint32_t _stepCounter;
    uint32_t _rngState;
};

} // namespace uds
