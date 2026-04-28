RG-7 Tests — Diagnostic Data Model
====================================

Test cases for MDD/ODX diagnostic description.

.. contents::
   :local:
   :depth: 1

.. test:: MDD DID definitions match ECU implementation
   :id: TEST_RG7_001
   :status: partial
   :tags: rg7, mdd
   :tests: REQ_RG7_001

   Parse MDD file and extract DID definitions. For each DID, send UDS 0x22
   with the DID bytes and verify ECU responds positively. Currently 6 of 7
   match; ``Identification`` (0xF100) has no ECU implementation.

.. test:: MDD DTC definitions match ECU simulation
   :id: TEST_RG7_002
   :status: manual
   :tags: rg7, mdd, dtc
   :tests: REQ_RG7_002

   Parse MDD file and extract DTC definitions. Read DTCs via UDS 0x19 0x02.
   Verify DTC numbers 0x010100–0x010500 appear in both MDD and ECU response.

.. test:: MDD DoIP communication parameters are correct
   :id: TEST_RG7_003
   :status: manual
   :tags: rg7, mdd, doip
   :tests: REQ_RG7_003

   Parse MDD file. Verify gateway address = 0x002A, tester address = 0x0EE0,
   functional address = 0xFFFF. Verify CDA successfully connects using these
   parameters.

.. test:: MDD supports dual protocol entries
   :id: TEST_RG7_004
   :status: manual
   :tags: rg7, mdd
   :tests: REQ_RG7_004

   Parse ``openbsw_ecu.json``. Verify ``com_param_refs`` contains entries for
   both DoIP and DoIP-DOBT protocols.

.. test:: MDD is regenerable from source JSON
   :id: TEST_RG7_005
   :status: manual
   :tags: rg7, mdd, tooling
   :tests: REQ_RG7_005

   Run ``generate_mdd.py`` from ``openbsw_ecu.json``. Verify output matches
   existing ``OpenBSW.mdd`` file (binary comparison or content equivalence).
