// Copyright 2025 Accenture.
// Auto-generated for FLXC1000 ECU simulation

#include "systems/Flxc1000UdsSystem.h"

#include <busid/BusId.h>
#include <etl/array.h>
#include <lifecycle/LifecycleManager.h>
#include <transport/ITransportSystem.h>
#include <transport/TransportConfiguration.h>

namespace uds
{

// Static data for FLXC1000 DIDs
// DID F100: ECU Identification (3 bytes: variant pattern)
// Value 0x000101 (257) matches MDD variant pattern for FLXC1000_App_0101
uint8_t const identificationDataF100[] = {0x00, 0x01, 0x01}; // App variant 0101

// DID F186: Active Diagnostic Session (1 byte)
uint8_t const sessionDataF186[] = {0x01}; // Default session

// DID F190: VIN (17 bytes)
// Simulated VIN: "WFLXC1000TIMEMACH" (time machine reference)
etl::array<uint8_t, 17> vinDataF190 = {'W','F','L','X','C','1','0','0','0','T','I','M','E','M','A','C','H'};

Flxc1000UdsSystem::Flxc1000UdsSystem(
    lifecycle::LifecycleManager& lManager,
    transport::ITransportSystem& transportSystem,
    ::async::ContextType context,
    uint16_t udsAddress)
: AsyncLifecycleComponent()
, ::etl::singleton_base<Flxc1000UdsSystem>(*this)
, _udsLifecycleConnector(lManager)
, _transportSystem(transportSystem)
, _jobRoot()
, _diagnosticSessionControl(_udsLifecycleConnector, context, _dummySessionPersistence)
, _communicationControl()
, _udsConfiguration{
      udsAddress,
      transport::TransportConfiguration::FUNCTIONAL_ALL_ISO14229,
      transport::TransportConfiguration::DIAG_PAYLOAD_SIZE,
      ::busid::SELFDIAG,
      true,  /* activate outgoing pending */
      false, /* accept all requests */
      true,  /* copy functional requests */
      context}
, _udsDispatcher(
      _connectionPool, _sendJobQueue, _udsConfiguration, _diagnosticSessionControl, _jobRoot)
, _asyncDiagHelper(context)
, _readDataByIdentifier()
, _writeDataByIdentifier()
, _routineControl()
, _startRoutine()
, _stopRoutine()
, _requestRoutineResults()
, _testerPresent()
// FLXC1000 DIDs
, _readF100(Flxc1000Simulator::DID_IDENTIFICATION, identificationDataF100)
, _readF186(Flxc1000Simulator::DID_ACTIVE_DIAGNOSTIC_SESSION_DATA_IDENTIFIER, sessionDataF186)
, _readF190(Flxc1000Simulator::DID_VINDATA_IDENTIFIER, vinDataF190)
, _writeF190(Flxc1000Simulator::DID_VINDATA_IDENTIFIER, vinDataF190)
// FLXC1000 Simulator
, _flxcSimulator()
, _readDtcInformation(_flxcSimulator)
, _clearDiagnosticInformation(_flxcSimulator)
, _context(context)
, _timeout()
{ setTransitionContext(_context); }

void Flxc1000UdsSystem::init()
{
    (void)_udsDispatcher.init();
    AbstractDiagJob::setDefaultDiagSessionManager(_diagnosticSessionControl);
    _diagnosticSessionControl.setDiagDispatcher(&_udsDispatcher);
    _transportSystem.addTransportLayer(_udsDispatcher);
    _flxcSimulator.init();
    addDiagJobs();

    transitionDone();
}

void Flxc1000UdsSystem::run()
{
    ::async::scheduleAtFixedRate(_context, *this, _timeout, 10, ::async::TimeUnit::MILLISECONDS);
    transitionDone();
}

void Flxc1000UdsSystem::shutdown()
{
    removeDiagJobs();
    _diagnosticSessionControl.setDiagDispatcher(nullptr);
    _diagnosticSessionControl.shutdown();
    _transportSystem.removeTransportLayer(_udsDispatcher);
    (void)_udsDispatcher.shutdown(
        transport::AbstractTransportLayer::ShutdownDelegate::
            create<Flxc1000UdsSystem, &Flxc1000UdsSystem::shutdownComplete>(*this));
}

void Flxc1000UdsSystem::shutdownComplete(transport::AbstractTransportLayer&)
{
    _timeout.cancel();
    transitionDone();
}

DiagDispatcher& Flxc1000UdsSystem::getUdsDispatcher() { return _udsDispatcher; }

IAsyncDiagHelper& Flxc1000UdsSystem::getAsyncDiagHelper() { return _asyncDiagHelper; }

IDiagSessionManager& Flxc1000UdsSystem::getDiagSessionManager() { return _diagnosticSessionControl; }

DiagnosticSessionControl& Flxc1000UdsSystem::getDiagnosticSessionControl()
{ return _diagnosticSessionControl; }

CommunicationControl& Flxc1000UdsSystem::getCommunicationControl() { return _communicationControl; }

ReadDataByIdentifier& Flxc1000UdsSystem::getReadDataByIdentifier() { return _readDataByIdentifier; }

void Flxc1000UdsSystem::addDiagJobs()
{
    // 22 - ReadDataByIdentifier
    (void)_jobRoot.addAbstractDiagJob(_readDataByIdentifier);
    (void)_jobRoot.addAbstractDiagJob(_readF100);  // ECU Identification
    (void)_jobRoot.addAbstractDiagJob(_readF186);  // Active Session
    (void)_jobRoot.addAbstractDiagJob(_readF190);  // VIN

    // 2E - WriteDataByIdentifier
    (void)_jobRoot.addAbstractDiagJob(_writeDataByIdentifier);
    (void)_jobRoot.addAbstractDiagJob(_writeF190); // VIN (writable)

    // 31 - Routine Control
    (void)_jobRoot.addAbstractDiagJob(_routineControl);
    (void)_jobRoot.addAbstractDiagJob(_startRoutine);
    (void)_jobRoot.addAbstractDiagJob(_stopRoutine);
    (void)_jobRoot.addAbstractDiagJob(_requestRoutineResults);

    // 19 - ReadDTCInformation
    (void)_jobRoot.addAbstractDiagJob(_readDtcInformation);

    // 14 - ClearDiagnosticInformation
    (void)_jobRoot.addAbstractDiagJob(_clearDiagnosticInformation);

    // F200 - FluxCapacitor Power Consumption (simulated)
    (void)_jobRoot.addAbstractDiagJob(_flxcSimulator.getFluxCapacitorPowerConsumption());

    // Services
    (void)_jobRoot.addAbstractDiagJob(_testerPresent);
    (void)_jobRoot.addAbstractDiagJob(_diagnosticSessionControl);
    (void)_jobRoot.addAbstractDiagJob(_communicationControl);
}

void Flxc1000UdsSystem::removeDiagJobs()
{
    // 22 - ReadDataByIdentifier
    _jobRoot.removeAbstractDiagJob(_readDataByIdentifier);
    _jobRoot.removeAbstractDiagJob(_readF100);
    _jobRoot.removeAbstractDiagJob(_readF186);
    _jobRoot.removeAbstractDiagJob(_readF190);

    // 2E - WriteDataByIdentifier
    _jobRoot.removeAbstractDiagJob(_writeDataByIdentifier);
    _jobRoot.removeAbstractDiagJob(_writeF190);

    // 31 - Routine Control
    _jobRoot.removeAbstractDiagJob(_routineControl);
    _jobRoot.removeAbstractDiagJob(_startRoutine);
    _jobRoot.removeAbstractDiagJob(_stopRoutine);
    _jobRoot.removeAbstractDiagJob(_requestRoutineResults);

    // 19 - ReadDTCInformation
    _jobRoot.removeAbstractDiagJob(_readDtcInformation);

    // 14 - ClearDiagnosticInformation
    _jobRoot.removeAbstractDiagJob(_clearDiagnosticInformation);

    // F200 - FluxCapacitor
    _jobRoot.removeAbstractDiagJob(_flxcSimulator.getFluxCapacitorPowerConsumption());

    // Services
    _jobRoot.removeAbstractDiagJob(_testerPresent);
    _jobRoot.removeAbstractDiagJob(_diagnosticSessionControl);
    _jobRoot.removeAbstractDiagJob(_communicationControl);
}

void Flxc1000UdsSystem::execute()
{
    // Step the simulator approximately every 500ms (50 * 10ms cycle)
    static uint32_t counter = 0U;
    ++counter;
    if ((counter % 50U) == 0U)
    {
        _flxcSimulator.step();
    }
}

} // namespace uds
