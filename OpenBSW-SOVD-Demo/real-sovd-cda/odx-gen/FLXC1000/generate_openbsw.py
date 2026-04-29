#!/usr/bin/env python3
"""
Generate OpenBSW C++ code for FLXC1000 ECU simulation.

This script reads the flxc1000_summary.json and generates:
- Flxc1000Simulator.h - Header for DTC and DID simulation
- Flxc1000Simulator.cpp - Implementation

The generated code follows OpenBSW coding conventions (east-const, naming, etc.)
"""

import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SUMMARY_FILE = os.path.join(SCRIPT_DIR, "flxc1000_summary.json")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "..", "openbsw-overlay", "app")

HEADER_TEMPLATE = '''\
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
{{

/**
 * FLXC1000 ECU Simulator.
 *
 * This simulator implements the diagnostic services defined in FLXC1000.mdd:
 * - {num_dtcs} DTCs (Diagnostic Trouble Codes)
 * - {num_dids} DIDs (Data Identifiers)
 *
 * Generated from: {mdd_file}
 */
class Flxc1000Simulator : public IDtcProvider
{{
public:
    // DTC codes
{dtc_constants}

    // DID identifiers
{did_constants}

    static size_t const MAX_DTCS = {max_dtcs}U;

    Flxc1000Simulator();

    /**
     * Initialize the simulator with configured DTCs and DIDs.
     */
    void init();

    /**
     * Advance the simulation one step. Call periodically (e.g., every 500ms).
     */
    void step();

    /**
     * Get the DTC store for direct access.
     */
    DiagnosticTroubleCodeStore<MAX_DTCS>& getDtcStore();

    // DID accessors
{did_getters}

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
{did_members}
    uint32_t _stepCounter;
    uint32_t _rngState;
}};

}} // namespace uds
'''

CPP_TEMPLATE = '''\
// Copyright 2025 Accenture.
// Auto-generated from FLXC1000.mdd - DO NOT EDIT

#include "uds/Flxc1000Simulator.h"

namespace uds
{{

Flxc1000Simulator::Flxc1000Simulator()
: _dtcStore()
{member_initializers}
, _stepCounter(0U)
, _rngState(42U)
{{}}

void Flxc1000Simulator::init()
{{
    // Register DTCs from FLXC1000.mdd
{dtc_init}
}}

void Flxc1000Simulator::step()
{{
    ++_stepCounter;

    // Step simulated sensor values
{did_step}

    // Randomly toggle DTC status bits to simulate a live vehicle
    _rngState          = (_rngState * 1103515245U + 12345U);
    uint32_t const rnd = (_rngState >> 16U) & 0xFFFFU;

    // Toggle a DTC every ~4 steps on average
    if ((_stepCounter % 4U) == 0U)
    {{
        size_t const dtcIndex      = rnd % _dtcStore.getCount();
        DiagnosticTroubleCode* dtc = _dtcStore.getDtcByIndex(dtcIndex);
        if (dtc != nullptr)
        {{
            if ((dtc->getStatusByte() & DiagnosticTroubleCode::TEST_FAILED) != 0U)
            {{
                if ((rnd & 0x01U) != 0U)
                {{
                    dtc->clearStatusBit(DiagnosticTroubleCode::TEST_FAILED);
                    dtc->clearStatusBit(DiagnosticTroubleCode::TEST_FAILED_THIS_OPERATION_CYCLE);
                }}
            }}
            else
            {{
                if ((rnd & 0x02U) != 0U)
                {{
                    dtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED);
                    dtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED_THIS_OPERATION_CYCLE);
                    dtc->setStatusBit(DiagnosticTroubleCode::CONFIRMED_DTC);
                    dtc->setStatusBit(DiagnosticTroubleCode::TEST_FAILED_SINCE_LAST_CLEAR);
                }}
            }}
        }}
    }}

{did_simulation}
}}

DiagnosticTroubleCodeStore<Flxc1000Simulator::MAX_DTCS>& Flxc1000Simulator::getDtcStore()
{{ return _dtcStore; }}

{did_getter_impls}

// IDtcProvider interface implementation

uint8_t Flxc1000Simulator::getStatusAvailabilityMask() const
{{ return _dtcStore.getStatusAvailabilityMask(); }}

size_t Flxc1000Simulator::countByStatusMask(uint8_t const mask) const
{{ return _dtcStore.countByStatusMask(mask); }}

size_t Flxc1000Simulator::getDtcCount() const
{{ return _dtcStore.getCount(); }}

DiagnosticTroubleCode const* Flxc1000Simulator::getDtcByIndex(size_t const index) const
{{ return _dtcStore.getDtcByIndex(index); }}

DiagnosticTroubleCode const* Flxc1000Simulator::findDtcByNumber(uint32_t const dtcNumber) const
{{ return _dtcStore.findDtcByNumber(dtcNumber); }}

void Flxc1000Simulator::clearAll()
{{ _dtcStore.clearAll(); }}

bool Flxc1000Simulator::clearByNumber(uint32_t const dtcNumber)
{{ return _dtcStore.clearByDtcNumber(dtcNumber); }}

}} // namespace uds
'''

def to_cpp_name(name: str) -> str:
    """Convert a name like 'Code1' to 'DTC_CODE1' or 'FluxCapacitor_Read' to 'DID_FLUX_CAPACITOR'."""
    # Remove _Read, _Write suffixes
    name = name.replace('_Read', '').replace('_Write', '')
    # Convert CamelCase to UPPER_SNAKE_CASE
    result = []
    for i, c in enumerate(name):
        if c.isupper() and i > 0 and name[i-1].islower():
            result.append('_')
        result.append(c.upper())
    return ''.join(result)

def main():
    with open(SUMMARY_FILE) as f:
        summary = json.load(f)
    
    dtcs = summary['dtcs']
    dids = summary['dids']
    
    # Generate DTC constants
    dtc_constants = []
    for dtc in dtcs:
        cpp_name = f"DTC_{to_cpp_name(dtc['name'])}"
        dtc_constants.append(f"    static uint32_t const {cpp_name:<30} = 0x{dtc['code_decimal']:06X}U;")
    
    # Generate DID constants
    did_constants = []
    for did in dids:
        cpp_name = f"DID_{to_cpp_name(did['name'])}"
        did_constants.append(f"    static uint16_t const {cpp_name:<40} = 0x{did['did_decimal']:04X}U;")
    
    # Generate DID member declarations
    did_members = []
    did_getters = []
    member_initializers = []
    did_step = []
    did_simulation = []
    did_getter_impls = []
    
    for did in dids:
        cpp_name = to_cpp_name(did['name'])
        member_name = f"_{cpp_name[0].lower()}{cpp_name[1:]}"
        
        if did['semantic'] == 'CURRENTDATA':
            # This is a simulated sensor value
            did_members.append(f"    ReadIdentifierSimulated {member_name};")
            did_getters.append(f"    ReadIdentifierSimulated& get{cpp_name}();")
            
            # Determine reasonable bounds based on the DID
            if 'Power' in did['name'] or 'Flux' in did['name']:
                initial, min_val, max_val = 1210, 0, 2100  # 1.21 GW scaled
            else:
                initial, min_val, max_val = 100, 0, 255
            
            member_initializers.append(f", {member_name}(DID_{cpp_name}, {initial}U, {min_val}U, {max_val}U)")
            did_step.append(f"    {member_name}.step();")
            did_getter_impls.append(f"ReadIdentifierSimulated& Flxc1000Simulator::get{cpp_name}()\n{{ return {member_name}; }}")
    
    # Generate header
    header = HEADER_TEMPLATE.format(
        num_dtcs=len(dtcs),
        num_dids=len(dids),
        mdd_file="FLXC1000.mdd",
        dtc_constants='\n'.join(dtc_constants) or "    // No DTCs defined",
        did_constants='\n'.join(did_constants) or "    // No DIDs defined",
        max_dtcs=max(len(dtcs) + 2, 16),  # Some buffer
        did_getters='\n'.join(did_getters) or "    // No simulated DIDs",
        did_members='\n'.join(did_members) or "    // No simulated DID members"
    )
    
    # Generate DTC init code
    dtc_init = []
    for dtc in dtcs:
        cpp_name = f"DTC_{to_cpp_name(dtc['name'])}"
        dtc_init.append(f"    (void)_dtcStore.addDtc({cpp_name}, 0U);")
    
    # Generate implementation
    impl = CPP_TEMPLATE.format(
        member_initializers='\n'.join(member_initializers) if member_initializers else "",
        dtc_init='\n'.join(dtc_init) or "    // No DTCs to initialize",
        did_step='\n'.join(did_step) or "    // No simulated DIDs to step",
        did_simulation="    // Simulation logic can be extended here",
        did_getter_impls='\n\n'.join(did_getter_impls) or "// No simulated DID getters"
    )
    
    # Write files
    os.makedirs(os.path.join(OUTPUT_DIR, "include", "uds"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "src", "uds"), exist_ok=True)
    
    header_path = os.path.join(OUTPUT_DIR, "include", "uds", "Flxc1000Simulator.h")
    impl_path = os.path.join(OUTPUT_DIR, "src", "uds", "Flxc1000Simulator.cpp")
    
    with open(header_path, 'w') as f:
        f.write(header)
    print(f"Generated: {header_path}")
    
    with open(impl_path, 'w') as f:
        f.write(impl)
    print(f"Generated: {impl_path}")
    
    print(f"\nSummary:")
    print(f"  DTCs: {len(dtcs)}")
    print(f"  DIDs: {len(dids)}")

if __name__ == "__main__":
    main()
