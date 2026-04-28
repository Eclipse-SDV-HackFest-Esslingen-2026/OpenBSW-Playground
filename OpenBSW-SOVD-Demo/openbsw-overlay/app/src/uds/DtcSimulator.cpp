// Copyright 2025 Accenture.

#include "uds/DtcSimulator.h"

namespace uds
{

DtcSimulator::DtcSimulator()
: _dtcStore()
, _engineTemp(DID_ENGINE_TEMP, 90U, 70U, 130U) // Engine temp: 70–130 °C, start 90
, _batteryVoltage(
      DID_BATTERY_VOLT, 128U, 100U, 150U)         // Battery: 10.0–15.0V scaled (x10), start 12.8
, _vehicleSpeed(DID_VEHICLE_SPEED, 60U, 0U, 220U) // Speed: 0–220 km/h, start 60
, _stepCounter(0U)
, _rngState(42U)
{}

void DtcSimulator::init()
{
    // Register demo DTCs with initial cleared state
    (void)_dtcStore.addDtc(DTC_ENGINE_OVERTEMP, 0U);
    (void)_dtcStore.addDtc(DTC_BATTERY_VOLTAGE_LOW, 0U);
    (void)_dtcStore.addDtc(DTC_COMMUNICATION_FAULT, 0U);
    (void)_dtcStore.addDtc(DTC_SENSOR_MALFUNCTION, 0U);
    (void)_dtcStore.addDtc(DTC_BRAKE_SYSTEM_FAULT, 0U);
}

void DtcSimulator::step()
{
    ++_stepCounter;

    // Step simulated sensor values
    _engineTemp.step();
    _batteryVoltage.step();
    _vehicleSpeed.step();

    // Every N steps, randomly toggle DTC status bits
    // This creates a realistic "faults come and go" behaviour for the demo
    _rngState          = (_rngState * 1103515245U + 12345U);
    uint32_t const rnd = (_rngState >> 16U) & 0xFFFFU;

    // Toggle a DTC every ~4 steps on average
    if ((_stepCounter % 4U) == 0U)
    {
        size_t const dtcIndex      = rnd % _dtcStore.getCount();
        DiagnosticTroubleCode* dtc = _dtcStore.getDtcByIndex(dtcIndex);
        if (dtc != nullptr)
        {
            if ((dtc->getStatusByte() & DiagnosticTroubleCode::TEST_FAILED) != 0U)
            {
                // Fault is active → randomly clear it (50% chance)
                if ((rnd & 0x01U) != 0U)
                {
                    dtc->clearStatusBit(DiagnosticTroubleCode::TEST_FAILED);
                    dtc->clearStatusBit(DiagnosticTroubleCode::TEST_FAILED_THIS_OPERATION_CYCLE);
                }
            }
            else
            {
                // Fault is inactive → randomly set it (50% chance)
                if ((rnd & 0x02U) != 0U)
                {
                    dtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED);
                    dtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED_THIS_OPERATION_CYCLE);
                    dtc->setStatusBit(DiagnosticTroubleCode::CONFIRMED_DTC);
                    dtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED_SINCE_LAST_CLEAR);
                }
            }
        }
    }

    // Link engine temp DTC to simulated engine temperature
    uint32_t const engineTempValue   = _engineTemp.getCurrentValue();
    DiagnosticTroubleCode* engineDtc = _dtcStore.findDtcByNumber(DTC_ENGINE_OVERTEMP);
    if (engineDtc != nullptr)
    {
        if (engineTempValue > 120U)
        {
            engineDtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED);
            engineDtc->setStatusBit(DiagnosticTroubleCode::CONFIRMED_DTC);
            engineDtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED_SINCE_LAST_CLEAR);
        }
        else if (engineTempValue < 100U)
        {
            engineDtc->clearStatusBit(DiagnosticTroubleCode::TEST_FAILED);
        }
    }

    // Link battery voltage DTC to simulated voltage
    uint32_t const batteryValue       = _batteryVoltage.getCurrentValue();
    DiagnosticTroubleCode* batteryDtc = _dtcStore.findDtcByNumber(DTC_BATTERY_VOLTAGE_LOW);
    if (batteryDtc != nullptr)
    {
        if (batteryValue < 110U) // Below 11.0V
        {
            batteryDtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED);
            batteryDtc->setStatusBit(DiagnosticTroubleCode::CONFIRMED_DTC);
            batteryDtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED_SINCE_LAST_CLEAR);
        }
        else if (batteryValue > 120U) // Above 12.0V
        {
            batteryDtc->clearStatusBit(DiagnosticTroubleCode::TEST_FAILED);
        }
    }
}

DiagnosticTroubleCodeStore<DtcSimulator::MAX_DTCS>& DtcSimulator::getDtcStore()
{ return _dtcStore; }

ReadIdentifierSimulated& DtcSimulator::getEngineTemp() { return _engineTemp; }

ReadIdentifierSimulated& DtcSimulator::getBatteryVoltage() { return _batteryVoltage; }

ReadIdentifierSimulated& DtcSimulator::getVehicleSpeed() { return _vehicleSpeed; }

// IDtcProvider interface implementation

uint8_t DtcSimulator::getStatusAvailabilityMask() const
{ return _dtcStore.getStatusAvailabilityMask(); }

size_t DtcSimulator::countByStatusMask(uint8_t const mask) const
{ return _dtcStore.countByStatusMask(mask); }

size_t DtcSimulator::getDtcCount() const { return _dtcStore.getCount(); }

DiagnosticTroubleCode const* DtcSimulator::getDtcByIndex(size_t const index) const
{ return _dtcStore.getDtcByIndex(index); }

DiagnosticTroubleCode const* DtcSimulator::findDtcByNumber(uint32_t const dtcNumber) const
{ return _dtcStore.findDtcByNumber(dtcNumber); }

void DtcSimulator::clearAll() { _dtcStore.clearAll(); }

bool DtcSimulator::clearByNumber(uint32_t const dtcNumber)
{ return _dtcStore.clearByNumber(dtcNumber); }

} // namespace uds
