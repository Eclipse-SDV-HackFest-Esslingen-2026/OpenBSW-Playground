#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Generate ODX/PDX diagnostic description for the OpenBSW Reference ECU.
#
# This script reuses the CDA testcontainer's ODX generation modules to create
# a PDX file describing the OpenBSW ECU's diagnostic capabilities:
#   - 5 DTCs (0x010100..0x010500)
#   - 6 DIDs (0xCF01..0xCF12)
#   - DoIP logical address 0x002A, functional address 0xFFFF
#   - Standard UDS services: session control, reset, DTC read/clear
#
# Prerequisites:
#   pip install odxtools==11.0.0
#
# Usage:
#   cd real-sovd-cda/odx-gen
#   python generate_openbsw.py
#   # Produces: OpenBSW.pdx
#
# To convert to MDD (requires odx-converter with ODX XSD schema):
#   java -jar <path-to>/converter-all.jar OpenBSW.pdx

import sys
import os

# Add the CDA's ODX generation modules to the path
CDA_ODX_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "classic-diagnostic-adapter",
    "testcontainer",
    "odx",
)
sys.path.insert(0, os.path.abspath(CDA_ODX_DIR))

import odxtools
from odxtools.database import Database
from odxtools.diagdatadictionaryspec import DiagDataDictionarySpec
from odxtools.diaglayercontainer import DiagLayerContainer
from odxtools.diaglayers.basevariant import BaseVariant
from odxtools.diaglayers.basevariantraw import BaseVariantRaw
from odxtools.diaglayers.diaglayertype import DiagLayerType
from odxtools.diaglayers.ecuvariant import EcuVariant
from odxtools.diaglayers.ecuvariantraw import EcuVariantRaw
from odxtools.ecuvariantpattern import EcuVariantPattern
from odxtools.matchingparameter import MatchingParameter
from odxtools.odxlink import OdxLinkId, DocType, OdxDocFragment
from odxtools.parentref import ParentRef
from odxtools.compumethods.compucategory import CompuCategory
from odxtools.compumethods.identicalcompumethod import IdenticalCompuMethod
from odxtools.dataobjectproperty import DataObjectProperty
from odxtools.odxtypes import DataType
from odxtools.physicaltype import PhysicalType
from odxtools.standardlengthtype import StandardLengthType

from comparams import generate_comparam_refs
from helper import ref, derived_id
from metadata import (
    add_functional_classes,
    add_admin_data,
    add_company_datas,
    add_additional_audiences,
)
from shared import (
    add_common_datatypes,
    add_state_charts,
    add_common_diag_comms,
    add_service_did,
)
from dtc_services import (
    add_dtc_clear_services,
    add_dtc_read_services,
    add_dtc_setting_services,
)
from reset import add_reset_services

# ── OpenBSW ECU parameters ──────────────────────────────────────────────────
ECU_NAME = "OpenBSW"
LOGICAL_ADDRESS = 0x002A   # ECU DoIP logical address
GATEWAY_ADDRESS = 0x002A   # same as logical for single-ECU
FUNCTIONAL_ADDRESS = 0xFFFF

# ── DID definitions (from catalog.json) ─────────────────────────────────────
OPENBSW_DIDS = [
    # (service_name, property_name, did_hex, bit_length, long_name, writable)
    ("StaticData",      "StaticData",      0xCF01, 128, "Static identifier data",     False),
    ("ADC_Value",       "ADC_Value",       0xCF02, 16,  "ADC potentiometer value",    False),
    ("WritableData",    "WritableData",    0xCF03, 128, "Writable data identifier",   True),
    ("EngineTemp",      "EngineTemp",      0xCF10, 32,  "Engine coolant temperature", False),
    ("BatteryVoltage",  "BatteryVoltage",  0xCF11, 32,  "Battery voltage",            False),
    ("VehicleSpeed",    "VehicleSpeed",    0xCF12, 32,  "Vehicle speed",              False),
]


def add_openbsw_dids(dlr):
    """Register the OpenBSW ECU-specific DID read/write services."""
    for svc_name, prop_name, did, bit_length, long_name, writable in OPENBSW_DIDS:
        # Create a DOP for each DID
        if bit_length <= 8:
            base_type = DataType.A_UINT32
            phys_type = DataType.A_UINT32
        elif bit_length <= 32:
            base_type = DataType.A_UINT32
            phys_type = DataType.A_UINT32
        else:
            # For larger payloads, use bytefield
            base_type = DataType.A_BYTEFIELD
            phys_type = DataType.A_BYTEFIELD

        dop = DataObjectProperty(
            odx_id=derived_id(dlr, f"DOP.{svc_name}"),
            short_name=svc_name,
            compu_method=IdenticalCompuMethod(
                category=CompuCategory.IDENTICAL,
                physical_type=phys_type,
                internal_type=base_type,
            ),
            diag_coded_type=StandardLengthType(
                base_data_type=base_type,
                bit_length=bit_length,
            ),
            physical_type=PhysicalType(base_data_type=phys_type),
        )
        dlr.diag_data_dictionary_spec.data_object_props.append(dop)

        add_service_did(
            dlr,
            service_name=svc_name,
            property_name=prop_name,
            did=did,
            dop=dop,
            add_write=writable,
            funct_class="Ident",
            long_name=long_name,
        )


def add_base_variant(dlc, database):
    """Create the base variant with all OpenBSW ECU diagnostic services."""
    doc_frags = dlc.odx_id.doc_fragments
    base_variant = BaseVariantRaw(
        odx_id=OdxLinkId(local_id=f"BV.{ECU_NAME}", doc_fragments=doc_frags),
        short_name=ECU_NAME,
        comparam_refs=generate_comparam_refs(
            ecu_name=ECU_NAME,
            logical_address=LOGICAL_ADDRESS,
            functional_address=FUNCTIONAL_ADDRESS,
            gateway_address=GATEWAY_ADDRESS,
            database=database,
        ),
        variant_type=DiagLayerType.BASE_VARIANT,
        parent_refs=[
            ParentRef(
                layer_ref=ref(
                    OdxLinkId(
                        local_id="PROTO.UDS_Ethernet_DoIP",
                        doc_fragments=(
                            OdxDocFragment(
                                doc_name="UDS_Ethernet_DoIP",
                                doc_type=DocType.CONTAINER,
                            ),
                        ),
                    )
                )
            ),
            ParentRef(
                layer_ref=ref(
                    OdxLinkId(
                        local_id="PROTO.UDS_Ethernet_DoIP_DOBT",
                        doc_fragments=(
                            OdxDocFragment(
                                doc_name="UDS_Ethernet_DoIP_DOBT",
                                doc_type=DocType.CONTAINER,
                            ),
                        ),
                    )
                )
            ),
        ],
        diag_data_dictionary_spec=DiagDataDictionarySpec(),
    )

    # Foundation: functional classes, datatypes, state charts
    add_functional_classes(base_variant)
    add_common_datatypes(base_variant)
    add_state_charts(base_variant)

    # Common UDS services (session control 10 xx, VIN, identification)
    add_common_diag_comms(base_variant)

    # ECU reset (11 xx)
    add_reset_services(base_variant)

    # DTC setting (85 xx)
    add_dtc_setting_services(base_variant)

    # DTC read (19 xx)
    add_dtc_read_services(base_variant)

    # DTC clear (14 xx)
    add_dtc_clear_services(base_variant)

    # OpenBSW-specific DIDs
    add_openbsw_dids(base_variant)

    dlc.base_variants.append(BaseVariant(diag_layer_raw=base_variant))


def add_variant(dlc, name, identification_pattern):
    """Add an ECU variant (application or boot)."""
    doc_frags = dlc.odx_id.doc_fragments
    variant = EcuVariantRaw(
        odx_id=OdxLinkId(
            local_id=f"EV.{ECU_NAME}.{name}", doc_fragments=doc_frags
        ),
        short_name=name,
        variant_type=DiagLayerType.ECU_VARIANT,
        ecu_variant_patterns=[
            EcuVariantPattern(
                matching_parameters=[
                    MatchingParameter(
                        expected_value=str(identification_pattern),
                        diag_comm_snref="Identification_Read",
                        out_param_if_snref="Identification",
                    )
                ]
            )
        ],
        parent_refs=[ParentRef(layer_ref=ref(dlc.base_variants[0].odx_id))],
        diag_data_dictionary_spec=DiagDataDictionarySpec(),
    )
    dlc.ecu_variants.append(EcuVariant(diag_layer_raw=variant))


def generate():
    """Generate the OpenBSW ECU PDX file."""
    print(f"Generating ODX for {ECU_NAME} (logical addr 0x{LOGICAL_ADDRESS:04X})")

    database = Database()
    database.short_name = ECU_NAME

    # Load base ODX protocol definitions (shipped with CDA testcontainer)
    base_dir = os.path.join(CDA_ODX_DIR, "base")
    for odx_filename in (
        "ISO_13400_2.odx-cs",
        "ISO_14229_5.odx-cs",
        "ISO_14229_5_on_ISO_13400_2.odx-c",
        "UDS_Ethernet_DoIP.odx-d",
        "UDS_Ethernet_DoIP_DOBT.odx-d",
    ):
        database.add_odx_file(os.path.join(base_dir, odx_filename))

    database.refresh()

    doc_frags = (OdxDocFragment(ECU_NAME, DocType.CONTAINER),)

    dlc = DiagLayerContainer(
        odx_id=OdxLinkId(f"DLC.{ECU_NAME}", doc_fragments=doc_frags),
        short_name=ECU_NAME,
    )
    add_admin_data(dlc)
    add_company_datas(dlc)
    add_additional_audiences(dlc)

    add_base_variant(dlc, database)

    # Add a default application variant
    add_variant(dlc, f"{ECU_NAME}_App_Default", 0x000001)

    database.diag_layer_containers.append(dlc)
    database.refresh()

    output_path = os.path.join(os.path.dirname(__file__), f"{ECU_NAME}.pdx")
    odxtools.write_pdx_file(output_path, database)
    print(f"Written: {output_path}")
    print()
    print("Next step – convert to MDD (requires odx-converter):")
    print(f"  java -jar <path-to>/converter-all.jar {output_path}")


if __name__ == "__main__":
    generate()
