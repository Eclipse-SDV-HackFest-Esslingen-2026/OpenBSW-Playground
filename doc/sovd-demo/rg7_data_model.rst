RG-7 — Diagnostic Data Model (MDD / ODX)
=========================================

Requirements for the ECU diagnostic description used by the CDA.

.. contents::
   :local:
   :depth: 1

.. req:: MDD describes 7 DIDs with correct SID + DID hex values
   :id: REQ_RG7_001
   :status: partial
   :tags: rg7, mdd, odx
   :satisfies: SPEC_ARCH_MDD

   MDD describes 7 DIDs with correct SID + DID hex values.
   6 of 7 match ECU; ``Identification`` uses 0xF100 (ECU has no such DID).

.. req:: MDD describes 5 DTCs with DTC numbers matching ECU simulation
   :id: REQ_RG7_002
   :status: done
   :tags: rg7, mdd, dtc
   :satisfies: SPEC_ARCH_MDD

   MDD describes 5 DTCs with DTC numbers matching ECU simulation.
   0x010100–0x010500.

.. req:: MDD describes DoIP communication parameters
   :id: REQ_RG7_003
   :status: done
   :tags: rg7, mdd, doip
   :satisfies: SPEC_ARCH_MDD

   MDD describes DoIP communication parameters.
   Gateway 0x002A, tester 0x0EE0, functional 0xFFFF.

.. req:: MDD supports both DoIP and DoIP-DOBT protocol entries
   :id: REQ_RG7_004
   :status: done
   :tags: rg7, mdd
   :satisfies: SPEC_ARCH_MDD

   MDD supports both DoIP and DoIP-DOBT protocol entries.
   Dual ``com_param_refs`` in JSON.

.. req:: MDD is regenerable from openbsw_ecu.json via generate_mdd.py
   :id: REQ_RG7_005
   :status: done
   :tags: rg7, mdd, tooling
   :satisfies: SPEC_ARCH_MDD

   MDD is regenerable from ``openbsw_ecu.json`` via ``generate_mdd.py``.
   FlatBuffers + Protobuf toolchain.
