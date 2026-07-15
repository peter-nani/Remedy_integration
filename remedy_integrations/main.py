import datetime
import json
import logging
import re
import ssl
import time

import requests

from silo.apps.sl1_data_model import (
    get_cred_array_from_id,
)
from silo.apps.storage import dbc_cursor
from suds.client import Client

from helpers import (
    acknowledge_event_sql,
    build_alert_payload,
    build_event_user_note,
    clean_ascii,
    clean_pc_resolution,
    convert_sl1_datetime_to_remedy,
    extract_mscI_message,
    extract_qradar_magnitude,
    extract_qradar_severity,
    get_application_type,
    get_component_dn,
    get_device_certificates,
    get_error_attempt,
    get_error_timestamp,
    get_interface_by_name,
    get_interface_description,
    get_interface_tags,
    get_response_attribute,
    get_root_device_ip,
    get_sql_instance_details,
    has_incident_number,
    has_interval_elapsed,
    is_clear_ticket_action,
    is_create_ticket_action,
    is_older_than_hours,
    parse_policy_id_list,
    prepend_error_note,
    replace_error_note,
    safe_threshold,
    starts_with_incident_number,
    strip_ilo_name,
    strip_oob_name,
    to_string,
    was_modified_within,
)

# Extract the ticket action type safely
ticket_action = str(EM7_VALUES['%n']).split(":")[2]

# Determine the correct log file path
if ticket_action in ["NewTicket", "ImmediateTicket"]:
    new_log_file_name = log_file_name
else:
    new_log_file_name = '/data/logs/SLRemedyIntegration/v1/ProdRemedy/UpdateTicket.log'
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

log_formatter = logging.Formatter(
    "%(asctime)s,%(levelname)s,%(lineno)s,%(message)s"
)

log_file_handler = logging.FileHandler(
    new_log_file_name
)

log_file_handler.setFormatter(
    log_formatter
)

logger.addHandler(
    log_file_handler
)

def get_create_event_id():
    return str(int(event_id) * -1)


def get_update_event_id():
    if int(event_id) >= 12632565:
        return str(int(event_id) * -1)

    return str(event_id)

def build_create_user_notes():
    user_notes = str(
        EM7_VALUES["%_user_note"]
    )

    pc_resolution = str(
        EM7_VALUES["%R"]
    )

    if not pc_resolution:
        return user_notes

    cleaned_resolution = clean_pc_resolution(
        pc_resolution
    )

    return (
        user_notes
        + cleaned_resolution
    )

def build_create_base_payload():
    return {
        "resource_name": str(
            EM7_VALUES["%X"]
        ),
        "subresource_name": str(
            EM7_VALUES["%Y"]
        ),
        "date_last": (
            convert_sl1_datetime_to_remedy(
                EM7_VALUES["%d"]
            )
        ),
        "severity": str(
            EM7_VALUES["%s"]
        ),
        "date_first": (
            convert_sl1_datetime_to_remedy(
                EM7_VALUES["%D"]
            )
        ),
        "device_ip": str(
            EM7_VALUES["%a"]
        ),
        "device_name": str(
            EM7_VALUES["%X"]
        ),
        "device_class": str(
            EM7_VALUES["%W"]
        ),
        "device_subclass": str(
            EM7_VALUES["%_class_name"]
        ),
        "device_id": str(
            EM7_VALUES["%x"]
        ),
        "counter": str(
            EM7_VALUES["%c"]
        ),
        "EID": get_create_event_id(),
        "user_notes": (
            build_create_user_notes()
        ),
    }

def add_create_source_fields(
    event_details,
):
    event_details.update(
        {
            "source": str(
                EM7_VALUES["%z"]
            ),
            "org_id": str(
                EM7_VALUES["%o"]
            ),
            "org_name": str(
                EM7_VALUES["%O"]
            ),
        }
    )

    return event_details

def add_create_event_fields(
    event_details,
):
    event_details.update(
        {
            "message": clean_ascii(
                EM7_VALUES["%M"]
            ),
            "evt_policy_name": str(
                EM7_VALUES[
                    "%_event_policy_name"
                ]
            ),
            "evt_policy_id": str(
                EM7_VALUES["%3"]
            ),
            "evt_policy_severity": str(
                EM7_VALUES["%s"]
            ),
            "user_del": str(
                EM7_VALUES["%4"]
            ),
            "date_active": (
                convert_sl1_datetime_to_remedy(
                    EM7_VALUES["%6"]
                )
            ),
        }
    )

    return event_details

def add_create_metric_fields(
    event_details,
):
    event_details.update(
        {
            "msg_val": "",
            "threshold": safe_threshold(
                EM7_VALUES["%T"]
            ),
            "label": str(
                EM7_VALUES["%Y"]
            ),
        }
    )

    return event_details

def add_create_relationship_fields(
    event_details,
):
    event_details.update(
        {
            "device_parent": str(
                EM7_VALUES[
                    "%_parent_name"
                ]
            ),
            "device_child": "",
            "correlation_reason": "",
        }
    )

    return event_details

def add_create_empty_fields(
    event_details,
):
    event_details.update(
        {
            "org_city": "",
            "org_state": "",
            "org_address": "",
            "date_del": "",
            "date_ack": "",
            "user_ack": "",
            "vendor_name": "",
            "vendor_case_id": "",
        }
    )

    return event_details

def add_create_application_type(
    event_details,
):
    event_details["application_type"] = (
        get_application_type(
            EM7_VALUES["%n"]
        )
    )

    return event_details

def build_create_payload():
    event_details = (
        build_create_base_payload()
    )

    event_details = (
        add_create_source_fields(
            event_details
        )
    )

    event_details = (
        add_create_event_fields(
            event_details
        )
    )

    event_details = (
        add_create_metric_fields(
            event_details
        )
    )

    event_details = (
        add_create_relationship_fields(
            event_details
        )
    )

    event_details = (
        add_create_empty_fields(
            event_details
        )
    )

    event_details = (
        add_create_application_type(
            event_details
        )
    )

    logger.info(
        "[EID:%s]: Default payload to "
        "create a ticket in remedy %s",
        event_id,
        event_details,
    )

    return event_details

def build_update_base_payload():
    return {
        "EID": get_update_event_id(),
        "severity": str(
            EM7_VALUES["%s"]
        ),
        "message": clean_ascii(
            EM7_VALUES["%M"]
        ),
        "date_last": (
            convert_sl1_datetime_to_remedy(
                EM7_VALUES["%d"]
            )
        ),
        "date_del": " ",
        "date_active": (
            convert_sl1_datetime_to_remedy(
                EM7_VALUES["%6"]
            )
        ),
        "date_ack": " ",
        "correlation_reason": " ",
        "user_ack": "svc_remedy",
        "user_del": str(
            EM7_VALUES["%4"]
        ),
        "user_notes": " ",
        "counter": str(
            EM7_VALUES["%c"]
        ),
        "msg_val": str(
            EM7_VALUES["%V"]
        ),
    }

def can_update_cleared_incident():
    if not has_incident_number(
        EM7_VALUES["%_ext_ticket_ref"]
    ):
        return False

    user_note = str(
        EM7_VALUES["%_user_note"]
    )

    if "Resolved" in user_note:
        return False

    if "Closed" in user_note:
        return False

    return True

def build_clear_ticket_payload(
    updated_event_details,
):
    if not can_update_cleared_incident():
        return False

    updated_event_details["severity"] = 0

    logger.info(
        "[EID:%s]: Event payload to "
        "update an incident in remedy "
        "for cleared event in SL %s",
        event_id,
        updated_event_details,
    )

    return updated_event_details

def is_event_recently_modified():
    logger.info(
        "[EID:%s]: Checking if the event "
        "updated in last:%s sec. "
        "Event date_last:%s",
        event_id,
        modification_interval,
        EM7_VALUES["%d"],
    )

    is_recent = was_modified_within(
        EM7_VALUES["%d"],
        modification_interval,
    )

    logger.info(
        "[EID:%s]: Event modification "
        "window result: %s",
        event_id,
        is_recent,
    )

    return is_recent

def build_modified_event_payload(
    updated_event_details,
):
    if not is_event_recently_modified():
        logger.info(
            "[EID:%s]: Event did not "
            "update in last:%s sec. "
            "Event date_last:%s",
            event_id,
            modification_interval,
            EM7_VALUES["%d"],
        )

        return False

    if not has_incident_number(
        EM7_VALUES["%_ext_ticket_ref"]
    ):
        logger.info(
            "[EID:%s]: No incident "
            "number exists %s",
            event_id,
            EM7_VALUES[
                "%_ext_ticket_ref"
            ],
        )

        return False

    logger.info(
        "[EID:%s]: Found the incident "
        "number:%s",
        event_id,
        EM7_VALUES[
            "%_ext_ticket_ref"
        ],
    )

    logger.info(
        "[EID:%s]: Event payload to "
        "update an incident in remedy %s",
        event_id,
        updated_event_details,
    )

    return updated_event_details

def build_update_payload():
    updated_event_details = (
        build_update_base_payload()
    )

    if is_clear_ticket_action(
        EM7_VALUES["%n"]
    ):
        return build_clear_ticket_payload(
            updated_event_details
        )

    return build_modified_event_payload(
        updated_event_details
    )

def acknowledge_non_ticketable(
    reason,
):
    stats["ext_ticket_ref"] = reason

    update_event_sql = (
        "UPDATE master_events.events_active "
        "SET user_ack = {} "
        "WHERE id = {};"
    ).format(
        ack_user_non_tktable_alert,
        event_id,
    )

    logger.info(
        "[EID:%s]: Update Event SQL query is %s",
        event_id,
        update_event_sql,
    )

    response = dbc.execute(
        update_event_sql
    )

    if str(response) == "1":
        logger.info(
            "[EID:%s]: Successfully "
            "acknowledged event with "
            "svc_nonticketable user",
            event_id,
        )
    else:
        logger.error(
            "[EID:%s]: Failed to "
            "acknowledge event with "
            "svc_nonticketable user",
            event_id,
        )

        logger.error(
            "[EID:%s]: %s",
            event_id,
            response,
        )

def acknowledge_non_ticketable(
    reason,
):
    stats["ext_ticket_ref"] = reason

    update_event_sql = (
        "UPDATE master_events.events_active "
        "SET user_ack = {} "
        "WHERE id = {};"
    ).format(
        ack_user_non_tktable_alert,
        event_id,
    )

    logger.info(
        "[EID:%s]: Update Event SQL query is %s",
        event_id,
        update_event_sql,
    )

    response = dbc.execute(
        update_event_sql
    )

    if str(response) == "1":
        logger.info(
            "[EID:%s]: Successfully "
            "acknowledged event with "
            "svc_nonticketable user",
            event_id,
        )
    else:
        logger.error(
            "[EID:%s]: Failed to "
            "acknowledge event with "
            "svc_nonticketable user",
            event_id,
        )

        logger.error(
            "[EID:%s]: %s",
            event_id,
            response,
        )

def is_cdb_ticket_event():
    event_policy_ids = (
        ep_create_ticket_SLDB
        .strip("][")
        .split(",")
    )

    return str(
        EM7_VALUES["%3"]
    ) in event_policy_ids

def is_cdb_ticket_event():
    event_policy_ids = (
        ep_create_ticket_SLDB
        .strip("][")
        .split(",")
    )

    return str(
        EM7_VALUES["%3"]
    ) in event_policy_ids

def handle_cdb_collection_disabled(
    event_details,
):
    logger.info(
        "[EID:%s]: Collection objects "
        "disabled events Handling",
        event_id,
    )

    date_first = datetime.datetime.strptime(
        str(EM7_VALUES["%D"]),
        "%Y-%m-%d %H:%M:%S",
    )

    logger.info(
        "[EID:%s]: %s",
        event_id,
        date_first,
    )

    current_time = datetime.datetime.now()

    if date_first > (
        current_time
        - datetime.timedelta(hours=72)
    ):
        logger.info(
            "[EID:%s]: The Event create "
            "date is %s and it is not "
            "72 hours old event",
            event_id,
            date_first,
        )

        return False

    event_details["device_ip"] = str(
        cdb_device_ip
    )

    event_details["resource_name"] = str(
        cdb_device_name
    )

    event_details["device_name"] = str(
        cdb_device_name
    )

    return event_details

def get_interface_details():
    interface_id = EM7_VALUES["%y"]

    if str(interface_id) != "0":
        return interface_id, None

    sql = (
        "SELECT if_id, name "
        "FROM master_dev.device_interfaces "
        "WHERE name = '{}' "
        "AND did = {}"
    ).format(
        str(EM7_VALUES["%Y"]).strip(),
        EM7_VALUES["%x"],
    )

    logger.info(
        "[EID:%s]: tag_id_SQLQuery: %s",
        event_id,
        sql,
    )

    dbc.execute(sql)

    interface_details = dbc.fetchall()

    logger.info(
        "[EID:%s]: %s",
        event_id,
        interface_details,
    )

    return (
        interface_details[0][0],
        interface_details[0][1],
    )

def get_interface_tags(
    interface_id,
):
    sql = (
        "SELECT tag_name "
        "FROM master_dev."
        "device_interface_tags_map ditm "
        "JOIN master_dev."
        "device_interface_tags dit "
        "ON dit.tag_id = ditm.tag_id "
        "WHERE ditm.if_id = {}"
    ).format(
        interface_id
    )

    dbc.execute(sql)

    return [
        tag
        for tags in dbc.fetchall()
        for tag in tags
    ]

def get_interface_description(
    interface_id,
):
    sql = (
        "SELECT if_id, ifDescr "
        "FROM master_dev.device_interfaces "
        "WHERE if_id = {}"
    ).format(
        interface_id
    )

    logger.info(
        "[EID:%s]: port_des_SQL: %s",
        event_id,
        sql,
    )

    dbc.execute(sql)

    interface_details = dbc.fetchall()

    logger.info(
        "[EID:%s]: %s",
        event_id,
        interface_details,
    )

    return interface_details[0][1]

def handle_interface_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: Interfaces Events Handling",
        event_id,
    )

    interface_id, interface_name = (
        get_interface_details()
    )

    logger.info(
        "[EID:%s]: Interface Event with "
        "ifId:%s, ifName:%s. Checking if "
        "interface has AUTO TICKET tag",
        event_id,
        interface_id,
        EM7_VALUES["%Y"],
    )

    tags = get_interface_tags(
        interface_id
    )

    if "AUTO TICKET" not in tags:
        logger.info(
            "[EID:%s]: AUTO TICKET or "
            "NetName tags not found. "
            "Acknowledging the alert with "
            "svc_nonticketable user",
            event_id,
        )

        acknowledge_non_ticketable(
            "Interface-NonTickable"
        )

        return False

    logger.info(
        "[EID:%s]: AUTO TICKET tag found. "
        "Extracting interface name to "
        "send to Remedy",
        event_id,
    )

    interface_description = (
        get_interface_description(
            interface_id
        )
    )

    event_details["application_type"] = (
        "NetworkPort"
    )

    if interface_name is not None:
        event_details["subresource_name"] = (
            interface_name
        )
    else:
        event_details["subresource_name"] = (
            interface_description
        )

    return event_details

def get_root_device_ip():
    sql = (
        "SELECT ld.ip "
        "FROM master_dev.legend_device ld "
        "WHERE ld.id = ("
        "SELECT cdm.root_did "
        "FROM master_dev.component_dev_map cdm "
        "WHERE cdm.component_did = {}"
        ")"
    ).format(
        EM7_VALUES["%x"]
    )

    return dbc.autofetch_value(sql)

def handle_root_component(
    event_details,
    application_type=None,
):
    event_details["device_ip"] = (
        get_root_device_ip()
    )

    event_details["resource_name"] = str(
        EM7_VALUES["%_root_name"]
    )

    event_details["device_name"] = str(
        EM7_VALUES["%_root_name"]
    )

    if application_type is not None:
        event_details["application_type"] = (
            application_type
        )

    return event_details

def handle_sql_database_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: SQL Server Database "
        "Events Handling",
        event_id,
    )

    component_id = EM7_VALUES["%x"]

    component_dn = dbc.autofetch_value(
        "SELECT dn "
        "FROM master_dev.component_dev_map "
        "WHERE component_did={}".format(
            component_id
        )
    )

    logger.info(
        "[EID:%s]: Component_DN: %s",
        event_id,
        component_dn,
    )

    event_details["resource_name"] = str(
        EM7_VALUES["%_root_name"]
    ).split(".")[0]

    event_details["device_name"] = str(
        EM7_VALUES["%X"]
    )

    event_details["subresource_name"] = str(
        EM7_VALUES["%_parent_name"]
    )

    event_details["message"] = (
        "DB_Name : "
        + str(EM7_VALUES["%X"])
        + " : "
        + event_details["message"]
    )

    event_details["application_type"] = (
        "DB_Database"
    )

    if component_dn:
        event_details["subresource_name"] = (
            str(component_dn).split("\\")[0]
            + ":"
            + str(
                EM7_VALUES["%_parent_name"]
            )
        )

    return event_details

def handle_sql_instance_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: SQL Server Instance "
        "Events Handling",
        event_id,
    )

    component_id = EM7_VALUES["%x"]

    component_dn = dbc.autofetch_value(
        "SELECT dn "
        "FROM master_dev.component_dev_map "
        "WHERE component_did={}".format(
            component_id
        )
    )

    logger.info(
        "[EID:%s]: Component_DN: %s",
        event_id,
        component_dn,
    )

    event_details["resource_name"] = str(
        EM7_VALUES["%_root_name"]
    ).split(".")[0]

    event_details["device_name"] = str(
        EM7_VALUES["%X"]
    )

    event_details["subresource_name"] = str(
        EM7_VALUES["%X"]
    )

    if component_dn:
        event_details["subresource_name"] = (
            str(component_dn).split("\\")[0]
            + ":"
            + str(EM7_VALUES["%X"])
        )

    event_details["application_type"] = (
        "DB_Instance"
    )

    return event_details

def handle_sql_server_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: SQL Server Events Handling",
        event_id,
    )

    component_id = EM7_VALUES["%x"]

    sql = (
        "SELECT ld.device, cdm.dn "
        "FROM master_dev.component_dev_map cdm "
        "JOIN master_dev.legend_device ld "
        "ON ld.id = cdm.component_did "
        "WHERE cdm.parent_did = {}"
    ).format(
        component_id
    )

    instance_name = ""
    component_dn = ""

    logger.info(
        "[EID:%s]: No Instance name "
        "available in event information",
        event_id,
    )

    if dbc.execute(sql) != 0:
        instance_details = dbc.fetchall()

        instance_name = instance_details[0][0]
        component_dn = instance_details[0][1]

        logger.info(
            "[EID:%s]: InstanceName: %s",
            event_id,
            instance_name,
        )

        logger.info(
            "[EID:%s]: Component_DN: %s",
            event_id,
            component_dn,
        )
    else:
        instance_name = event_details[
            "device_name"
        ]

    event_details["resource_name"] = str(
        EM7_VALUES["%_root_name"]
    ).split(".")[0]

    event_details["device_name"] = (
        instance_name
    )

    event_details["subresource_name"] = (
        instance_name
    )

    if component_dn:
        event_details["subresource_name"] = (
            str(component_dn).split("\\")[0]
            + ":"
            + instance_name
        )

    event_details["application_type"] = (
        "DB_Instance"
    )

    return event_details

def handle_mysql_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: Mysql Component "
        "events Handling",
        event_id,
    )

    event_details["resource_name"] = str(
        EM7_VALUES["%_root_name"]
    )

    event_details["device_name"] = str(
        EM7_VALUES["%_root_name"]
    )

    return event_details

def handle_cluster_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: Windows Cluster "
        "components events Handling",
        event_id,
    )

    event_details["resource_name"] = str(
        EM7_VALUES["%_root_name"]
    )

    event_details["device_name"] = str(
        EM7_VALUES["%_root_name"]
    )

    event_details["subresource_name"] = "0"

    event_details["application_type"] = (
        "Cluster"
    )

    return event_details

def handle_ssl_certificate_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: SSL Certificate expiry "
        "Event Handling",
        event_id,
    )

    sql = (
        "SELECT certificate "
        "FROM master_dev.device_certificates "
        "WHERE did = {}"
    ).format(
        device_ID
    )

    dbc.execute(sql)

    certificate_info = dbc.fetchall()

    certificates = [
        certificate[0]
        for certificate in certificate_info
    ]

    event_details["message"] = (
        event_details["message"]
        + " Certificate Information: "
        + str(certificates)
    )

    return event_details

def handle_vesta_forward_trap(
    event_details,
):
    logger.info(
        "[EID:%s]: Vesta "
        "ExternalActivityForwardTrap Handling",
        event_id,
    )

    case_number = str(
        event_details["message"]
        .split(":")[0]
        .split("#")[1]
    )

    vesta_device_ip = str(
        event_details["message"]
        .split("]")[0]
        .strip("[")
    )

    logger.info(
        "[EID:%s]: Motorola Case Number: %s",
        event_id,
        case_number,
    )

    message_parts = str(
        event_details["message"]
    ).split("]")

    event_details["message"] = (
        "".join(message_parts[1:])
        .strip(" ")
    )

    event_details["vendor_case_id"] = (
        case_number
    )

    event_details["vendor_name"] = (
        "Vesta Solutions"
    )

    event_details["device_ip"] = (
        vesta_device_ip
    )

    logger.info(
        "[EID:%s]: Vesta Payload: %s",
        event_id,
        event_details,
    )

    return event_details

def handle_vesta_msci_trap(
    event_details,
):
    logger.info(
        "[EID:%s]: "
        "vstExternalActivityMSCITrap Handling",
        event_id,
    )

    motorola_event_id = str(
        EM7_VALUES["%Y"]
    ).split(":")[0]

    vesta_device_ip = str(
        event_details["message"]
        .split("]")[0]
        .strip("[")
    )

    event_details["vendor_case_id"] = (
        motorola_event_id
    )

    event_details["vendor_name"] = (
        "MSCI Vesta Solutions"
    )

    event_details["device_ip"] = (
        vesta_device_ip
    )

    event_details["message"] = str(
        re.search(
            r"MSCI_EID.*",
            str(event_details["message"]),
        ).group()
    )

    if "MSCI_TRAP_Source" in str(
        EM7_VALUES["%X"]
    ):
        event_details["user_notes"] = (
            str(vesta_device_ip)
            + " - Asset doesn't exist in "
            "Public Safety ScienceLogic"
        )

    logger.info(
        "[EID:%s]: Vesta "
        "ExternalActivityMSCITrap Payload: %s",
        event_id,
        event_details,
    )

    return event_details

def handle_ilo_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: ILO Events Handling",
        event_id,
    )

    device_name = str(
        EM7_VALUES["%X"]
    )

    device_name = (
        device_name
        .strip("-ILO.")
        .strip("-ilo.")
        .strip("-iLO.")
    )

    event_details["resource_name"] = (
        device_name
    )

    event_details["device_name"] = (
        device_name
    )

    return event_details

def handle_oob_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: OOB Events Handling",
        event_id,
    )

    device_name = str(
        EM7_VALUES["%X"]
    )

    device_name = (
        device_name
        .lstrip("OOB")
        .lstrip("oob")
        .lstrip("Oob")
    )

    event_details["resource_name"] = (
        device_name
    )

    event_details["device_name"] = (
        device_name
    )

    return event_details

def handle_netapp_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: NetApp Events Handling",
        event_id,
    )

    root_name = str(
        EM7_VALUES["%_root_name"]
    )

    if root_name:
        event_details["device_ip"] = (
            get_root_device_ip()
        )

        event_details["resource_name"] = (
            root_name
        )

        event_details["device_name"] = (
            root_name
        )

        event_details["subresource_name"] = str(
            EM7_VALUES["%X"]
        )

        event_details["message"] = (
            str(EM7_VALUES["%X"])
            + " : "
            + event_details["message"]
        )

    event_details["application_type"] = (
        "Cluster"
    )

    return event_details

def handle_rackarmor_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: RackArmor Camera Handling",
        event_id,
    )

    message = event_details["message"]

    event_details["device_ip"] = (
        message.split("(")[1].split(")")[0]
    )

    device_name = (
        message
        .split("(")[0]
        .split("-")[1]
        .strip()
    )

    event_details["resource_name"] = (
        device_name
    )

    event_details["device_name"] = (
        device_name
    )

    return event_details

def handle_rackarmor_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: RackArmor Camera Handling",
        event_id,
    )

    message = event_details["message"]

    event_details["device_ip"] = (
        message.split("(")[1].split(")")[0]
    )

    device_name = (
        message
        .split("(")[0]
        .split("-")[1]
        .strip()
    )

    event_details["resource_name"] = (
        device_name
    )

    event_details["device_name"] = (
        device_name
    )

    return event_details

def handle_vmax_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: Dell EMC Vmax "
        "events handling",
        event_id,
    )

    event_details["device_ip"] = (
        get_root_device_ip()
    )

    event_details["resource_name"] = str(
        EM7_VALUES["%_root_name"]
    )

    event_details["device_name"] = str(
        EM7_VALUES["%_root_name"]
    )

    event_details["message"] = (
        str(EM7_VALUES["%X"])
        + " : "
        + str(EM7_VALUES["%_parent_name"])
        + " : "
        + event_details["message"]
    )

    return event_details

def handle_qradar_scenario(
    event_details,
):
    logger.info(
        "[EID:%s]: QRadar Events Handling",
        event_id,
    )

    magnitude_match = re.search(
        r"QR_Offense_magnitude:(\w+)",
        str(event_details["message"]),
    )

    magnitude = int(
        magnitude_match.groups()[0]
    )

    severity_match = re.search(
        r"QR_Offense_Severity:(\w+)",
        str(event_details["message"]),
    )

    severity = int(
        severity_match.groups()[0]
    )

    logger.info(
        "[EID:%s]: QRadar Magnitude "
        "Value is %s",
        event_id,
        magnitude,
    )

    logger.info(
        "[EID:%s]: QRadar Severity "
        "Value is %s",
        event_id,
        severity,
    )

    if magnitude > int(
        qradar_magnitude_ticketing_threshold
    ):
        return event_details

    logger.info(
        "[EID:%s]: Magnitude value does "
        "not match ticketing criteria. "
        "Ignoring ticketing",
        event_id,
    )

    acknowledge_non_ticketable(
        "Qradar-NonTickable"
    )

    return False

def scenarios_handling(
    event_details,
):
    try:
        logger.info(
            "[EID:%s]: Entered into "
            "the scenarios loop",
            event_id,
        )

        if int(EM7_VALUES["%3"]) == int(
            availability_ep_id
        ):
            event_details = (
                handle_availability_scenario(
                    event_details
                )
            )

            if event_details is False:
                return False

        if is_cdb_ticket_event():
            return handle_cdb_scenario(
                event_details
            )

        if int(EM7_VALUES["%2"]) == 7:
            return handle_interface_scenario(
                event_details
            )

        if (
            str(EM7_VALUES["%a"]) == ""
            and str(EM7_VALUES["%O"])
            == "Public Safety NICE Support"
        ):
            return handle_root_component(
                event_details,
                application_type="Device",
            )

        if (
            str(EM7_VALUES["%a"]) == ""
            and str(EM7_VALUES["%O"])
            == "Public Safety PDCAD"
        ):
            return handle_root_component(
                event_details,
                application_type="Device",
            )

        device_class = str(
            EM7_VALUES["%_class_name"]
        )

        if "SQL Server Database" in device_class:
            return handle_sql_database_scenario(
                event_details
            )

        if "SQL Server Instance" in device_class:
            return handle_sql_instance_scenario(
                event_details
            )

        if device_class == "SQL Server":
            return handle_sql_server_scenario(
                event_details
            )

        if device_class in [
            "MySQL Server",
            "MySQL Instance",
        ]:
            return handle_mysql_scenario(
                event_details
            )

        if device_class in [
            "Cluster Networks",
            "Cluster Nodes",
            "Cluster Roles and Services",
            "Cluster Network",
            "Cluster Node",
            "Cluster Role / Service",
        ]:
            return handle_cluster_scenario(
                event_details
            )

        if device_class in [
            "BIG-IP Local Traffic Manager",
            "BIG-IP LTM Virtual Server",
            "BIG-IP LTM Pool",
            "BIG-IP LTM Pool Member",
            "BIG-IP LTM Node",
        ]:
            return handle_root_component(
                event_details
            )

        event_policy_name = str(
            EM7_VALUES["%_event_policy_name"]
        )

        if (
            event_policy_name
            == "SSL: Certificate has expired: "
            "AutoTicket"
        ):
            return (
                handle_ssl_certificate_scenario(
                    event_details
                )
            )

        if (
            "vstExternalActivityForwardTrap"
            in event_policy_name
            and "ecpprb08"
            not in str(EM7_VALUES["%X"])
        ):
            return handle_vesta_forward_trap(
                event_details
            )

        if (
            "vstExternalActivityMSCITrap"
            in event_policy_name
        ):
            return handle_vesta_msci_trap(
                event_details
            )

        device_name = str(
            EM7_VALUES["%X"]
        )

        if (
            "-ILO." in device_name
            or "-ilo." in device_name
            or "-iLO." in device_name
        ):
            return handle_ilo_scenario(
                event_details
            )

        if device_name.startswith(
            ("OOB", "oob", "Oob")
        ):
            return handle_oob_scenario(
                event_details
            )

        if (
            "NetApp" in event_policy_name
            or "NetAPP" in event_policy_name
        ):
            return handle_netapp_scenario(
                event_details
            )

        if "RackArmor" in event_policy_name:
            return handle_rackarmor_scenario(
                event_details
            )

        if (
            "SFTY: Dell EMC: VMAX Unisphere"
            in event_policy_name
        ):
            return handle_vmax_scenario(
                event_details
            )

        if "QRadar" in event_policy_name:
            return handle_qradar_scenario(
                event_details
            )

        return event_details

    except Exception as error:
        logger.exception(
            "[EID:%s]: scenarios_handling "
            "function error: %s",
            event_id,
            error,
        )

        return False
    

def get_credential(
    credential_id,
):
    logger.debug(
        "[EID:%s]: Loading credential ID: %s",
        event_id,
        credential_id,
    )

    credential = get_cred_array_from_id(
        dbc,
        int(credential_id),
    )

    if not credential:
        raise ValueError(
            "Credential not found for ID: {}".format(
                credential_id
            )
        )

    return credential

def get_credential_details(
    credential,
):
    url = credential.get("curl_url")
    username = credential.get("cred_user")
    password = credential.get("cred_pwd")

    if not url:
        raise ValueError(
            "Credential curl_url is missing"
        )

    if not username:
        raise ValueError(
            "Credential username is missing"
        )

    if password is None:
        raise ValueError(
            "Credential password is missing"
        )

    return url, username, password

def build_sl_api_url(
    sl_url,
    end_point,
):
    return (
        str(sl_url).rstrip("/")
        + "/api/"
        + str(end_point).lstrip("/")
    )

def call_sl_api(
    end_point,
    data,
):
    try:
        logger.info(
            "[EID:%s]: Calling SL1 API "
            "endpoint: %s",
            event_id,
            end_point,
        )

        sl_credential = get_credential(
            sl_db_credential_id
        )

        (
            sl_url,
            sl_username,
            sl_password,
        ) = get_credential_details(
            sl_credential
        )

        sl_api_url = build_sl_api_url(
            sl_url,
            end_point,
        )

        logger.debug(
            "[EID:%s]: SL1 API URL: %s",
            event_id,
            sl_api_url,
        )

        sl_api_response = requests.post(
            sl_api_url,
            data=json.dumps(data),
            headers={
                "Content-Type": "application/json"
            },
            auth=(
                sl_username,
                sl_password,
            ),
            verify=False,
        )

        logger.info(
            "[EID:%s]: SL1 API response "
            "status code: %s",
            event_id,
            sl_api_response.status_code,
        )

        return sl_api_response

    except Exception as error:
        logger.exception(
            "[EID:%s]: call_sl_api "
            "function error: %s",
            event_id,
            error,
        )

        return None
    
def disable_soap_ssl_verification():
    if hasattr(
        ssl,
        "_create_unverified_context",
    ):
        ssl._create_default_https_context = (
            ssl._create_unverified_context
        )

def create_remedy_client(
    remedy_ticket_url,
):
    logger.info(
        "[EID:%s]: Creating Remedy "
        "SOAP client",
        event_id,
    )

    return Client(
        str(remedy_ticket_url),
        cache=None,
    )

def create_remedy_authentication(
    remedy_operations,
    remedy_username,
    remedy_password,
):
    remedy_auth = (
        remedy_operations.factory.create(
            "AuthenticationInfo"
        )
    )

    remedy_auth.userName = (
        remedy_username
    )

    remedy_auth.password = (
        remedy_password
    )

    return remedy_auth

def configure_remedy_client(
    remedy_operations,
    remedy_auth,
):
    remedy_operations.set_options(
        soapheaders=(
            remedy_auth
        )
    )

    return remedy_operations

def call_remedy_web_service():
    try:
        logger.info(
            "[EID:%s]: Initialising Remedy "
            "web service",
            event_id,
        )

        remedy_credential = get_credential(
            remedy_create_update_ticket_webservice_credential_id
        )

        (
            remedy_ticket_url,
            remedy_username,
            remedy_password,
        ) = get_credential_details(
            remedy_credential
        )

        stats["TRRT"] = str(
            datetime.datetime.now()
        )

        disable_soap_ssl_verification()

        remedy_operations = (
            create_remedy_client(
                remedy_ticket_url
            )
        )

        remedy_auth = (
            create_remedy_authentication(
                remedy_operations,
                remedy_username,
                remedy_password,
            )
        )

        remedy_operations = (
            configure_remedy_client(
                remedy_operations,
                remedy_auth,
            )
        )

        logger.info(
            "[EID:%s]: Remedy SOAP client "
            "initialised successfully",
            event_id,
        )

        return remedy_operations

    except Exception as error:
        logger.exception(
            "[EID:%s]: "
            "call_remedy_web_service "
            "function error: %s",
            event_id,
            error,
        )

        return None
    
def create_remedy_ticket(
    create_payload,
):
    remedy_client = (
        call_remedy_web_service()
    )

    if remedy_client is None:
        raise RuntimeError(
            "Unable to initialise "
            "Remedy web service"
        )

    logger.info(
        "[EID:%s]: Calling Remedy "
        "Create_Operation",
        event_id,
    )

    remedy_response = (
        remedy_client
        .service
        .Create_Operation(
            **create_payload
        )
    )

    stats["TRRT"] = str(
        datetime.datetime.now()
    )

    logger.info(
        "[EID:%s]: Response received from "
        "Remedy Webservice: %s",
        event_id,
        remedy_response,
    )

    return remedy_response

def update_remedy_ticket(
    update_payload,
):
    remedy_client = (
        call_remedy_web_service()
    )

    if remedy_client is None:
        raise RuntimeError(
            "Unable to initialise "
            "Remedy web service"
        )

    logger.info(
        "[EID:%s]: Calling Remedy "
        "Update_Operation",
        event_id,
    )

    remedy_response = (
        remedy_client
        .service
        .Update_Operation(
            **update_payload
        )
    )

    stats["TRRT"] = str(
        datetime.datetime.now()
    )

    logger.info(
        "[EID:%s]: Response received from "
        "Remedy Update Webservice: %s",
        event_id,
        remedy_response,
    )

    return remedy_response

def update_remedy_ticket(
    update_payload,
):
    remedy_client = call_remedy_web_service()

    if remedy_client is None:
        raise RuntimeError(
            "Unable to initialise Remedy web service"
        )

    logger.info(
        "[EID:%s]: Calling Remedy Modify_Operation",
        event_id,
    )

    remedy_response = (
        remedy_client
        .service
        .Modify_Operation(
            **update_payload
        )
    )

    stats["TRRT"] = str(
        datetime.datetime.now()
    )

    logger.info(
        "[EID:%s]: Response received from "
        "Remedy Webservice: %s",
        event_id,
        remedy_response,
    )

    return remedy_response

def get_remedy_response_value(
    remedy_response,
    field_name,
    default_value,
):
    if field_name not in str(
        remedy_response
    ):
        return default_value

    value = getattr(
        remedy_response,
        field_name,
        None,
    )

    if value is None:
        return default_value

    return str(value)

def build_incident_event_data(
    remedy_response,
):
    event_ext_ticket_ref = str(
        remedy_response.ext_ticket_ref
    )

    case_status = get_remedy_response_value(
        remedy_response,
        "HDCaseStatus",
        "No_case_status",
    )

    assigned_group = get_remedy_response_value(
        remedy_response,
        "Assigned_Group",
        "No_assigned_group",
    )

    event_user_note = (
        "["
        + case_status
        + ":"
        + assigned_group
        + ":"
        + event_ext_ticket_ref
        + "]"
    )

    event_force_ticket_uri = (
        str(force_ticket_uri)
        + event_ext_ticket_ref
        + '"'
    )

    return {
        "user_ack": (
            "/api/account/"
            + str(ack_user_tktable_alert)
        ),
        "ext_ticket_ref": (
            event_ext_ticket_ref
        ),
        "user_note": event_user_note,
        "force_ticket_uri": (
            event_force_ticket_uri
        ),
    }

def build_non_ticketable_response_data(
    remedy_response,
):
    return {
        "user_ack": (
            "/api/account/"
            + str(ack_user_tktable_alert)
        ),
        "ext_ticket_ref": str(
            remedy_response.ext_ticket_ref
        ),
    }


def build_incident_app_failure_data(
    remedy_response,
):
    event_ext_ticket_ref = str(
        remedy_response.ext_ticket_ref
    )

    case_status = (
        "No_case_status"
    )

    assigned_group = (
        "No_assigned_group"
    )

    if remedy_response.HDCaseStatus:
        case_status = str(
            remedy_response.HDCaseStatus
        )

    if remedy_response.Assigned_Group:
        assigned_group = str(
            remedy_response.Assigned_Group
        )

    event_user_note = (
        "["
        + case_status
        + ":"
        + assigned_group
        + ":"
        + event_ext_ticket_ref
        + "]"
    )

    return {
        "user_ack": (
            "/api/account/"
            + str(ack_user_tktable_alert)
        ),
        "ext_ticket_ref": (
            event_ext_ticket_ref
        ),
        "user_note": event_user_note,
    }

def send_incident_app_failure_alert():
    alert_data = build_alert_payload(
        message=(
            "Incident App Failure on EID:"
            + str(event_id)
            + " with original Severity: "
            + str(EM7_VALUES["%S"])
        ),
        device_id=cdb_device_id,
    )

    sl_alert_res = call_sl_api(
        "alert",
        alert_data,
    )

    if (
        sl_alert_res is not None
        and sl_alert_res.status_code == 201
    ):
        logger.info(
            "[EID:%s]: Incident App Failure "
            "event inserted successfully",
            event_id,
        )

        return

    logger.info(
        "[EID:%s]: Failed to insert "
        "Incident App Failure event",
        event_id,
    )

def build_event_data_from_remedy_response(
    remedy_response,
):
    ext_ticket_ref = str(
        remedy_response.ext_ticket_ref
    )

    if ext_ticket_ref[:3] == "INC":
        event_data = build_incident_event_data(
            remedy_response
        )

        logger.info(
            "[EID:%s]: Updating event with "
            "following incident data %s",
            event_id,
            event_data,
        )

        return event_data

    if ext_ticket_ref in [
        "AutoTicketing Disabled",
        "Planned Outage",
    ]:
        event_data = (
            build_non_ticketable_response_data(
                remedy_response
            )
        )

        logger.info(
            "[EID:%s]: Updating event with "
            "following incident data %s",
            event_id,
            event_data,
        )

        return event_data

    if ext_ticket_ref == "Incident App Failure":
        event_data = (
            build_incident_app_failure_data(
                remedy_response
            )
        )

        logger.info(
            "[EID:%s]: Updating event with "
            "following incident data %s",
            event_id,
            event_data,
        )

        send_incident_app_failure_alert()

        return event_data

    return {}

def update_sl1_event(
    event_data,
):
    logger.info(
        "[EID:%s]: Updating ScienceLogic event",
        event_id,
    )

    return call_sl_api(
        "event/" + str(event_id),
        event_data,
    )

def is_sl1_event_update_successful(
    sl_update_response,
):
    return (
        sl_update_response is not None
        and sl_update_response.status_code == 200
    )

def log_sl1_event_update_failure(
    sl_update_response,
    remedy_response,
):
    logger.error(
        "[EID:%s]: Incident with incident "
        "number %s created in Remedy but "
        "got an error while updating event "
        "in ScienceLogic",
        event_id,
        str(
            remedy_response.ext_ticket_ref
        ),
    )

    if sl_update_response is None:
        logger.error(
            "[EID:%s]: SL1 API returned "
            "no response",
            event_id,
        )

        return

    try:
        logger.error(
            "[EID:%s]: %s",
            event_id,
            sl_update_response.json(),
        )

    except Exception:
        logger.error(
            "[EID:%s]: %s",
            event_id,
            sl_update_response,
        )

def handle_remedy_create_response(
    remedy_response,
):
    stats["ext_ticket_ref"] = str(
        remedy_response.ext_ticket_ref
    )

    event_data = (
        build_event_data_from_remedy_response(
            remedy_response
        )
    )

    sl_update_response = update_sl1_event(
        event_data
    )

    if is_sl1_event_update_successful(
        sl_update_response
    ):
        logger.info(
            "[EID:%s]: Incident with incident "
            "number: %s created in Remedy and "
            "successfully updated to event in "
            "ScienceLogic, acknowledged with "
            "svc_remedy user",
            event_id,
            str(
                remedy_response.ext_ticket_ref
            ),
        )

        return True

    log_sl1_event_update_failure(
        sl_update_response,
        remedy_response,
    )

    return False

def handle_create_ticket():
    create_payload = build_create_payload()

    create_payload = scenarios_handling(
        create_payload
    )

    if create_payload is False:
        logger.info(
            "[EID:%s]: This event identified "
            "as non ticketable event after "
            "scenarios check, ignoring "
            "ticketing on this event",
            event_id,
        )

        return True

    logger.info(
        "[EID:%s]: Create Ticket payload "
        "after scenarios check is: %s",
        event_id,
        create_payload,
    )

    remedy_create_response = (
        create_remedy_ticket(
            create_payload
        )
    )

    stats["ext_ticket_ref"] = str(
        remedy_create_response.ext_ticket_ref
    )

    return handle_remedy_create_response(
        remedy_create_response
    )

def handle_update_ticket():
    update_payload = build_update_payload()

    stats["ext_ticket_ref"] = str(
        EM7_VALUES["%_ext_ticket_ref"]
    )

    if not update_payload:
        return True

    remedy_update_response = (
        update_remedy_ticket(
            update_payload
        )
    )

    if len(remedy_update_response) != 0:
        logger.info(
            "[EID:%s]: Ticket:%s is updated "
            "successfully in Remedy",
            event_id,
            str(
                EM7_VALUES[
                    "%_ext_ticket_ref"
                ]
            ),
        )

        return True

    logger.error(
        "[EID:%s]: %s",
        event_id,
        remedy_update_response,
    )

    return False

def ticket_handling(
    ticket_status=False,
):
    try:
        if is_create_ticket_action(
            EM7_VALUES["%n"]
        ):
            ticket_status = (
                handle_create_ticket()
            )

        else:
            ticket_status = (
                handle_update_ticket()
            )

        return {
            "ticket_status": ticket_status,
            "result": "Success",
        }

    except Exception as error:
        logger.exception(
            "[EID:%s]: ticket_handling "
            "function error: %s",
            event_id,
            error,
        )

        return {
            "ticket_status": ticket_status,
            "result": error,
        }

def get_error_marker(
    user_note,
):
    error_match = re.search(
        r"\d-Error:\d+",
        str(user_note),
    )

    if error_match is None:
        return None

    return error_match.group()

def get_error_marker(
    user_note,
):
    error_match = re.search(
        r"\d-Error:\d+",
        str(user_note),
    )

    if error_match is None:
        return None

    return error_match.group()

def get_marker_timestamp(
    error_marker,
):
    if not error_marker:
        return None

    return int(
        float(
            error_marker.split(":")[1]
        )
    )

def build_error_marker(
    retry_number,
):
    return (
        str(retry_number)
        + "-Error:"
        + str(int(time.time()))
    )

def build_first_error_user_note(
    user_note,
):
    error_marker = build_error_marker(
        retry_number=1
    )

    return (
        "["
        + error_marker
        + "] "
        + str(user_note)
    )


def replace_error_marker(
    user_note,
    current_marker,
    next_retry_number,
):
    next_marker = build_error_marker(
        retry_number=next_retry_number
    )

    current_marker_with_brackets = (
        "["
        + current_marker
        + "]"
    )

    next_marker_with_brackets = (
        "["
        + next_marker
        + "]"
    )

    return str(user_note).replace(
        current_marker_with_brackets,
        next_marker_with_brackets,
    )

def update_retry_user_note(
    updated_user_note,
):
    event_data = {
        "user_note": str(
            updated_user_note
        )
    }

    logger.info(
        "[EID:%s]: Updating event with "
        "following data %s",
        event_id,
        event_data,
    )

    sl_update_response = call_sl_api(
        "event/" + str(event_id),
        event_data,
    )

    if (
        sl_update_response is not None
        and sl_update_response.status_code == 200
    ):
        logger.info(
            "[EID:%s]: Failed to create "
            "ticket and user_note field is "
            "updated with %s",
            event_id,
            event_data,
        )

        return True

    logger.error(
        "[EID:%s]: Failed to update "
        "retry user note in ScienceLogic",
        event_id,
    )

    if sl_update_response is not None:
        logger.error(
            "[EID:%s]: %s",
            event_id,
            sl_update_response,
        )

    return False
def register_first_ticket_failure(
    user_note,
    error_msg,
):
    updated_user_note = (
        build_first_error_user_note(
            user_note
        )
    )

    stats["ext_ticket_ref"] = (
        "1-Error"
        + str(error_msg)
    )

    logger.info(
        "[EID:%s]: Registering first "
        "ticket creation failure",
        event_id,
    )

    update_retry_user_note(
        updated_user_note
    )

def record_retry_waiting(
    retry_number,
    error_msg,
):
    stats["ext_ticket_ref"] = (
        str(retry_number)
        + "-Error "
        + str(error_msg)
    )

    logger.info(
        "[EID:%s]: Could not process for "
        "ticket creation as it does not "
        "reach the retry interval",
        event_id,
    )

def retry_ticket_handling(
    ticket_status,
):
    logger.info(
        "[EID:%s]: Retrying ticket handling",
        event_id,
    )

    return ticket_handling(
        ticket_status
    )

def move_to_next_error_level(
    user_note,
    current_marker,
    next_retry_number,
    error_msg,
):
    updated_user_note = (
        replace_error_marker(
            user_note=user_note,
            current_marker=current_marker,
            next_retry_number=(
                next_retry_number
            ),
        )
    )

    stats["ext_ticket_ref"] = (
        str(next_retry_number)
        + "-Error "
        + str(error_msg)
    )

    logger.info(
        "[EID:%s]: Moving ticket failure "
        "to retry level %s",
        event_id,
        next_retry_number,
    )

    update_retry_user_note(
        updated_user_note
    )

def build_final_failure_event_data():
    return {
        "user_ack": (
            "/api/account/"
            + str(ack_user_tktable_alert)
        ),
        "user_note": "6-Failure",
    }

def build_final_failure_alert(
    error_msg,
):
    return build_alert_payload(
        message=(
            "Remedy Ticket Creation Failed: "
            "AutoTicket Creation Failed on EID:"
            + str(event_id)
            + "; ERROR:"
            + str(error_msg)
        ),
        device_id=device_ID,
    )

def send_final_failure_alert(
    error_msg,
):
    alert_data = build_final_failure_alert(
        error_msg
    )

    sl_alert_response = call_sl_api(
        "alert",
        alert_data,
    )

    if (
        sl_alert_response is not None
        and sl_alert_response.status_code == 201
    ):
        logger.info(
            "[EID:%s]: 6-Failure event "
            "is inserted successfully",
            event_id,
        )

        return True

    logger.info(
        "[EID:%s]: Failed to insert "
        "6-Failure event",
        event_id,
    )

    return False

def handle_final_ticket_failure(
    error_msg,
):
    event_data = (
        build_final_failure_event_data()
    )

    stats["ext_ticket_ref"] = (
        "6-Failure "
        + str(error_msg)
    )

    logger.info(
        "[EID:%s]: Updating event with "
        "following data %s",
        event_id,
        event_data,
    )

    sl_update_response = call_sl_api(
        "event/" + str(event_id),
        event_data,
    )

    if (
        sl_update_response is None
        or sl_update_response.status_code != 200
    ):
        logger.error(
            "[EID:%s]: Failed to update "
            "event with 6-Failure",
            event_id,
        )

        if sl_update_response is not None:
            logger.error(
                "[EID:%s]: %s",
                event_id,
                sl_update_response,
            )

        return False

    logger.info(
        "[EID:%s]: Failed to create ticket "
        "and user_note field is updated "
        "with %s",
        event_id,
        event_data,
    )

    send_final_failure_alert(
        error_msg
    )

    return True

def handle_existing_retry_failure(
    user_note,
    error_msg,
    ticket_status,
):
    error_marker = get_marker_timestamp(
        user_note
    )

    if error_marker is None:
        logger.error(
            "[EID:%s]: Error marker could "
            "not be extracted from user note",
            event_id,
        )

        return

    retry_number = get_error_retry_number(
        error_marker
    )

    error_timestamp = get_error_timestamp(
        error_marker
    )

    logger.info(
        "[EID:%s]: Current retry level: %s",
        event_id,
        retry_number,
    )

    if not is_retry_interval_reached(
        error_timestamp
    ):
        record_retry_waiting(
            retry_number=retry_number,
            error_msg=error_msg,
        )

        return

    ticket_handling_response = (
        retry_ticket_handling(
            ticket_status
        )
    )

    if ticket_handling_response[
        "ticket_status"
    ]:
        logger.info(
            "[EID:%s]: Ticket retry "
            "completed successfully",
            event_id,
        )

        return

    if retry_number == 5:
        handle_final_ticket_failure(
            error_msg
        )

        return

    next_retry_number = (
        retry_number + 1
    )

    move_to_next_error_level(
        user_note=user_note,
        current_marker=error_marker,
        next_retry_number=(
            next_retry_number
        ),
        error_msg=error_msg,
    )


def exception_handling(
    event_id,
    ext_ticket_ref,
    user_note,
    error_msg,
    ticket_status,
):
    try:
        logger.info(
            "[EID:%s]: Entered "
            "exception handling",
            event_id,
        )

        if "-Error" not in str(user_note):
            register_first_ticket_failure(
                user_note=user_note,
                error_msg=error_msg,
            )

            return

        handle_existing_retry_failure(
            user_note=user_note,
            error_msg=error_msg,
            ticket_status=ticket_status,
        )

    except Exception as error:
        logger.exception(
            "[EID:%s]: exception_handling "
            "function error: %s",
            event_id,
            error,
        )

#********************************MIAN FUNCTIONALITY**************************************************

def get_runbook_variables():
    return {
        "event_id": event_id,
        "event_message": EM7_VALUES["%M"],
        "event_policy_id": EM7_VALUES["%3"],
        "event_policy_name": EM7_VALUES[
            "%_event_policy_name"
        ],
        "automation_policy_name": EM7_VALUES["%n"],
        "device_id": EM7_VALUES["%x"],
        "device_name": EM7_VALUES["%X"],
        "device_ip": EM7_VALUES["%a"],
        "device_class": EM7_VALUES[
            "%_class_name"
        ],
        "device_category": EM7_VALUES["%W"],
        "subresource_name": EM7_VALUES["%Y"],
        "sub_entity_id": EM7_VALUES["%y"],
        "parent_name": EM7_VALUES[
            "%_parent_name"
        ],
        "root_name": EM7_VALUES[
            "%_root_name"
        ],
        "source": EM7_VALUES["%z"],
        "org_id": EM7_VALUES["%o"],
        "org_name": EM7_VALUES["%O"],
        "severity": EM7_VALUES["%s"],
        "original_severity": EM7_VALUES["%S"],
        "counter": EM7_VALUES["%c"],
        "threshold": EM7_VALUES["%T"],
        "message_value": EM7_VALUES["%V"],
        "date_first": EM7_VALUES["%D"],
        "date_last": EM7_VALUES["%d"],
        "date_active": EM7_VALUES["%6"],
        "user_deleted": EM7_VALUES["%4"],
        "user_note": EM7_VALUES[
            "%_user_note"
        ],
        "ext_ticket_ref": EM7_VALUES[
            "%_ext_ticket_ref"
        ],
        "pc_resolution": EM7_VALUES["%R"],
    }

def log_runbook_variables():
    runbook_variables = (
        get_runbook_variables()
    )

    logger.info(
        "[EID:%s]: RBA Variables: %s",
        event_id,
        runbook_variables,
    )

def get_event_message():
    return str(
        EM7_VALUES["%M"]
    )

def is_event_message_blank():
    event_message = get_event_message()

    return not event_message.strip()

def build_blank_event_message_alert():
    return {
        "force_ytype": "0",
        "force_yid": "0",
        "force_yname": "",
        "message": (
            "Blank Event Message Check: EID: "
            + str(event_id)
            + ";DeviceName: "
            + str(EM7_VALUES["%X"])
            + ";EventPolicy: "
            + str(
                EM7_VALUES[
                    "%_event_policy_name"
                ]
            )
        ),
        "value": "",
        "threshold": "",
        "message_time": "",
        "aligned_resource": (
            "/api/device/"
            + str(cdb_device_id)
        ),
    }

def handle_blank_event_message():
    logger.info(
        "[EID:%s]: Blank event message detected",
        event_id,
    )

    alert_data = (
        build_blank_event_message_alert()
    )

    sl_alert_response = call_sl_api(
        "alert",
        alert_data,
    )

    if (
        sl_alert_response is not None
        and sl_alert_response.status_code == 201
    ):
        logger.info(
            "[EID:%s]: Blank Event Message "
            "Notification inserted successfully",
            event_id,
        )

        return True

    logger.info(
        "[EID:%s]: Failed to insert "
        "Blank Event Message Notification",
        event_id,
    )

    return False

def get_current_event_ticket_details():
    return {
        "ext_ticket_ref": str(
            EM7_VALUES[
                "%_ext_ticket_ref"
            ]
        ),
        "user_note": str(
            EM7_VALUES[
                "%_user_note"
            ]
        ),
    }

def run_ticket_process():
    logger.info(
        "[EID:%s]: Starting ticket handling",
        event_id,
    )

    ticket_response = ticket_handling(
        ticket_status=False
    )

    logger.info(
        "[EID:%s]: Ticket handling "
        "response: %s",
        event_id,
        ticket_response,
    )

    return ticket_response

def is_ticket_process_successful(
    ticket_response,
):
    return bool(
        ticket_response.get(
            "ticket_status",
            False,
        )
    )

def get_ticket_process_error(
    ticket_response,
):
    return ticket_response.get(
        "result",
        "Unknown ticket processing error",
    )

def handle_ticket_process_failure(
    ticket_response,
):
    event_ticket_details = (
        get_current_event_ticket_details()
    )

    error_message = (
        get_ticket_process_error(
            ticket_response
        )
    )

    logger.error(
        "[EID:%s]: Ticket handling failed: %s",
        event_id,
        error_message,
    )

    exception_handling(
        event_id=event_id,
        ext_ticket_ref=(
            event_ticket_details[
                "ext_ticket_ref"
            ]
        ),
        user_note=(
            event_ticket_details[
                "user_note"
            ]
        ),
        error_msg=error_message,
        ticket_status=(
            ticket_response.get(
                "ticket_status",
                False,
            )
        ),
    )

def update_final_stats():
    stats["AET"] = str(
        datetime.datetime.now()
    )

    if not stats.get(
        "ext_ticket_ref"
    ):
        stats["ext_ticket_ref"] = str(
            EM7_VALUES[
                "%_ext_ticket_ref"
            ]
        )

def log_stats():
    logger.info(
        "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s",
        stats["EID"],
        stats["Device_ID"],
        stats["Device_Name"],
        stats["date_first"],
        stats["date_last"],
        stats["date_del"],
        stats["ext_ticket_ref"],
        stats["AST"],
        stats["AET"],
        stats["TRQT"],
        stats["TRRT"],
    )

def handle_main_failure(
    error,
):
    logger.exception(
        "[EID:%s]: Unexpected main "
        "execution error: %s",
        event_id,
        error,
    )

    event_ticket_details = (
        get_current_event_ticket_details()
    )

    exception_handling(
        event_id=event_id,
        ext_ticket_ref=(
            event_ticket_details[
                "ext_ticket_ref"
            ]
        ),
        user_note=(
            event_ticket_details[
                "user_note"
            ]
        ),
        error_msg=error,
        ticket_status=False,
    )

def process_event():
    log_runbook_variables()

    ticket_response = run_ticket_process()

    if is_event_message_blank():
        handle_blank_event_message()

    if not is_ticket_process_successful(
        ticket_response
    ):
        handle_ticket_process_failure(
            ticket_response
        )

    return ticket_response

def main():
    try:
        logger.info(
            "[EID:%s]: Remedy integration started",
            event_id,
        )

        process_event()

    except Exception as error:
        handle_main_failure(
            error
        )

    finally:
        update_final_stats()

        log_stats()

        logger.info(
            "[EID:%s]: Remedy integration completed",
            event_id,
        )

main()
