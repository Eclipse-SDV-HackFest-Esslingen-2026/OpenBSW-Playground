// Copyright 2025 Accenture.
// Auto-generated for FLXC1000 ECU simulation

#pragma once

#include <async/Async.h>
#include <async/IRunnable.h>
#include <etl/singleton_base.h>
#include <lifecycle/AsyncLifecycleComponent.h>
#include <uds/DiagDispatcher.h>
#include <uds/DummySessionPersistence.h>
#include <uds/Flxc1000Simulator.h>
#include <uds/ReadIdentifierPot.h>
#include <uds/ReadIdentifierSimulated.h>
#include <uds/UdsLifecycleConnector.h>
#include <uds/async/AsyncDiagHelper.h>
#include <uds/async/AsyncDiagJob.h>
#include <uds/jobs/ReadIdentifierFromMemory.h>
#include <uds/jobs/WriteIdentifierToMemory.h>
#include <uds/services/cleardiagnosticinformation/ClearDiagnosticInformation.h>
#include <uds/services/communicationcontrol/CommunicationControl.h>
#include <uds/services/readdata/ReadDataByIdentifier.h>
#include <uds/services/readdtcinformation/ReadDTCInformation.h>
#include <uds/services/routinecontrol/RequestRoutineResults.h>
#include <uds/services/routinecontrol/RoutineControl.h>
#include <uds/services/routinecontrol/StartRoutine.h>
#include <uds/services/routinecontrol/StopRoutine.h>
#include <uds/services/sessioncontrol/DiagnosticSessionControl.h>
#include <uds/services/testerpresent/TesterPresent.h>
#include <uds/services/writedata/WriteDataByIdentifier.h>

namespace lifecycle
{
class LifecycleManager;
}

namespace transport
{
class ITransportSystem;
}

namespace uds
{

/**
 * UDS System configured for FLXC1000 ECU.
 *
 * Provides diagnostic services matching FLXC1000.mdd:
 * - DIDs: F100 (Identification), F186 (Session), F190 (VIN), F200 (FluxCapacitor)
 * - DTCs: 6 fault codes
 */
class Flxc1000UdsSystem
: public lifecycle::AsyncLifecycleComponent
, public ::etl::singleton_base<Flxc1000UdsSystem>
, private ::async::IRunnable
{
public:
    Flxc1000UdsSystem(
        lifecycle::LifecycleManager& lManager,
        transport::ITransportSystem& transportSystem,
        ::async::ContextType context,
        uint16_t udsAddress);

    void init() override;
    void run() override;
    void shutdown() override;

    DiagDispatcher& getUdsDispatcher();
    IAsyncDiagHelper& getAsyncDiagHelper();
    IDiagSessionManager& getDiagSessionManager();
    DiagnosticSessionControl& getDiagnosticSessionControl();
    CommunicationControl& getCommunicationControl();
    ReadDataByIdentifier& getReadDataByIdentifier();

private:
    void addDiagJobs();
    void removeDiagJobs();
    void shutdownComplete(transport::AbstractTransportLayer&);
    void execute() override;

    UdsLifecycleConnector _udsLifecycleConnector;
    transport::ITransportSystem& _transportSystem;
    DummySessionPersistence _dummySessionPersistence;

    DiagJobRoot _jobRoot;
    DiagnosticSessionControl _diagnosticSessionControl;
    CommunicationControl _communicationControl;
    DiagnosisConfiguration _udsConfiguration;
    ::etl::pool<IncomingDiagConnection, 5> _connectionPool;
    ::etl::queue<TransportJob, 16> _sendJobQueue;
    DiagDispatcher _udsDispatcher;
    uds::declare::AsyncDiagHelper<5> _asyncDiagHelper;

    ReadDataByIdentifier _readDataByIdentifier;
    WriteDataByIdentifier _writeDataByIdentifier;
    RoutineControl _routineControl;
    StartRoutine _startRoutine;
    StopRoutine _stopRoutine;
    RequestRoutineResults _requestRoutineResults;
    TesterPresent _testerPresent;

    // FLXC1000 specific DIDs
    ReadIdentifierFromMemory _readF100;  // ECU Identification
    ReadIdentifierFromMemory _readF186;  // Active Diagnostic Session
    ReadIdentifierFromMemory _readF190;  // VIN
    WriteIdentifierToMemory _writeF190;  // VIN (writable)

    // FLXC1000 Simulator (includes F200 FluxCapacitor and DTCs)
    Flxc1000Simulator _flxcSimulator;
    ReadDTCInformation _readDtcInformation;
    ClearDiagnosticInformation _clearDiagnosticInformation;

    ::async::ContextType _context;
    ::async::TimeoutType _timeout;
};

} // namespace uds
