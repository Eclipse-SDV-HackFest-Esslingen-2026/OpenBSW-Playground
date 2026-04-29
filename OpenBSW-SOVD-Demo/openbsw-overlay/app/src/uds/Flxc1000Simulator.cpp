// Copyright 2025 Accenture.
// Auto-generated from FLXC1000.mdd - DO NOT EDIT

#include "uds/Flxc1000Simulator.h"

namespace uds
{

Flxc1000Simulator::Flxc1000Simulator()
: _dtcStore()
, _fluxCapacitorPowerConsumption(DID_FLUX_CAPACITOR_POWER_CONSUMPTION, 1210U, 0U, 2100U) // 1.21 GW
, _stepCounter(0U)
, _rngState(42U)
{}

void Flxc1000Simulator::init()
{
    // Register DTCs from FLXC1000.mdd
    (void)_dtcStore.addDtc(DTC_CODE1, 0U);
    (void)_dtcStore.addDtc(DTC_CODE3, 0U);
    (void)_dtcStore.addDtc(DTC_CODE4, 0U);
    (void)_dtcStore.addDtc(DTC_CODE5, 0U);
    (void)_dtcStore.addDtc(DTC_CODE6, 0U);
    (void)_dtcStore.addDtc(DTC_CODE2, 0U);
}

void Flxc1000Simulator::step()
{
    ++_stepCounter;

    // Step simulated Flux Capacitor power consumption
    _fluxCapacitorPowerConsumption.step();

    // Randomly toggle DTC status bits
    _rngState          = (_rngState * 1103515245U + 12345U);
    uint32_t const rnd = (_rngState >> 16U) & 0xFFFFU;

    if ((_stepCounter % 4U) == 0U)
    {
        size_t const dtcIndex      = rnd % _dtcStore.getCount();
        DiagnosticTroubleCode* dtc = _dtcStore.getDtcByIndex(dtcIndex);
        if (dtc != nullptr)
        {
            if ((dtc->getStatusByte() & DiagnosticTroubleCode::TEST_FAILED) != 0U)
            {
                if ((rnd & 0x01U) != 0U)
                {
                    dtc->clearStatusBit(DiagnosticTroubleCode::TEST_FAILED);
                    dtc->clearStatusBit(DiagnosticTroubleCode::TEST_FAILED_THIS_OPERATION_CYCLE);
                }
            }
            else
            {
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
}

DiagnosticTroubleCodeStore<Flxc1000Simulator::MAX_DTCS>& Flxc1000Simulator::getDtcStore()
{ return _dtcStore; }

ReadIdentifierSimulated& Flxc1000Simulator::getFluxCapacitorPowerConsumption()
{ return _fluxCapacitorPowerConsumption; }

uint8_t Flxc1000Simulator::getStatusAvailabilityMask() const
{ return _dtcStore.getStatusAvailabilityMask(); }

size_t Flxc1000Simulator::countByStatusMask(uint8_t const mask) const
{ return _dtcStore.countByStatusMask(mask); }

size_t Flxc1000Simulator::getDtcCount() const
{ return _dtcStore.getCount(); }

DiagnosticTroubleCode const* Flxc1000Simulator::getDtcByIndex(size_t const index) const
{ return _dtcStore.getDtcByIndex(index); }

DiagnosticTroubleCode const* Flxc1000Simulator::findDtcByNumber(uint32_t const dtcNumber) const
{ return _dtcStore.findDtcByNumber(dtcNumber); }

void Flxc1000Simulator::clearAll()
{ _dtcStore.clearAll(); }

bool Flxc1000Simulator::clearByNumber(uint32_t const dtcNumber)
{ return _dtcStore.clearByNumber(dtcNumber); }

} // namespace uds
