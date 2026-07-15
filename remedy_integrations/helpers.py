from __future__ import annotations

import datetime
import html
import re
import string
import time

import pytz


PRINTABLE_CHARACTERS = set(string.printable)

SL1_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
REMEDY_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p"

UTC_TIMEZONE = pytz.timezone("UTC")
REMEDY_TIMEZONE = pytz.timezone("America/New_York")

ERROR_NOTE_PATTERN = re.compile(
    r"(\d)-Error:(\d+)"
)


def to_string(value):
    if value is None:
        return ""

    return str(value)


def clean_ascii(value):
    value = to_string(value)

    return "".join(
        character
        for character in value
        if character in PRINTABLE_CHARACTERS
    )


def clean_html(value):
    value = clean_ascii(value)

    value = re.sub(
        r"<(br|p|BR|P|H|h|div|DIV|LI|li)\s*[^>]*>",
        "\n",
        value,
    )

    value = re.sub(
        r"<[^>]*>",
        "",
        value,
    )

    return html.unescape(value).strip()


def truncate(value, max_length):
    value = to_string(value)

    if len(value) <= max_length:
        return value

    return value[:max_length]


def clean_pc_resolution(value):
    value = clean_html(value)

    return truncate(
        value,
        4096,
    )


def safe_int(value, default=0):
    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def safe_threshold(value):
    try:
        return int(float(value))

    except (TypeError, ValueError):
        return 0


def convert_sl1_datetime_to_remedy(value):
    parsed_datetime = datetime.datetime.strptime(
        to_string(value),
        SL1_DATETIME_FORMAT,
    )

    utc_datetime = UTC_TIMEZONE.localize(
        parsed_datetime
    )

    remedy_datetime = utc_datetime.astimezone(
        REMEDY_TIMEZONE
    )

    return remedy_datetime.strftime(
        REMEDY_DATETIME_FORMAT
    )


def parse_sl1_datetime(value):
    return datetime.datetime.strptime(
        to_string(value),
        SL1_DATETIME_FORMAT,
    )


def datetime_to_timestamp(value):
    return int(
        time.mktime(
            time.strptime(
                to_string(value),
                SL1_DATETIME_FORMAT,
            )
        )
    )


def current_timestamp():
    return int(time.time())


def current_datetime():
    return datetime.datetime.now()


def has_interval_elapsed(
    timestamp,
    interval_seconds,
):
    elapsed_seconds = (
        current_timestamp()
        - int(float(timestamp))
    )

    return elapsed_seconds >= int(
        interval_seconds
    )


def was_modified_within(
    date_last,
    interval_seconds,
):
    modification_timestamp = datetime_to_timestamp(
        date_last
    )

    minimum_timestamp = (
        current_timestamp()
        - int(interval_seconds)
    )

    return (
        modification_timestamp
        > minimum_timestamp
    )


def is_older_than_hours(
    value,
    hours,
):
    event_datetime = parse_sl1_datetime(
        value
    )

    minimum_datetime = (
        current_datetime()
        - datetime.timedelta(
            hours=hours
        )
    )

    return (
        event_datetime
        <= minimum_datetime
    )


def get_automation_details(
    automation_policy_name,
):
    return to_string(
        automation_policy_name
    ).split(":")


def get_automation_action(
    automation_policy_name,
):
    details = get_automation_details(
        automation_policy_name
    )

    if len(details) <= 2:
        return ""

    return details[2].strip()


def get_application_type(
    automation_policy_name,
):
    details = get_automation_details(
        automation_policy_name
    )

    if len(details) <= 3:
        return ""

    return details[3].strip()


def is_create_ticket_action(
    automation_policy_name,
):
    return get_automation_action(
        automation_policy_name
    ) in (
        "NewTicket",
        "ImmediateTicket",
    )


def is_clear_ticket_action(
    automation_policy_name,
):
    return (
        "ClearTicket"
        in to_string(
            automation_policy_name
        )
    )


def has_incident_number(value):
    return (
        "INC"
        in to_string(value)
    )


def starts_with_incident_number(value):
    return (
        to_string(value)[:3]
        == "INC"
    )


def extract_regex_value(
    value,
    pattern,
    group=1,
):
    match = re.search(
        pattern,
        to_string(value),
    )

    if match is None:
        return None

    return match.group(group)


def extract_qradar_magnitude(message):
    value = extract_regex_value(
        message,
        r"QR_Offense_magnitude:(\w+)",
    )

    if value is None:
        return None

    return int(value)


def extract_qradar_severity(message):
    value = extract_regex_value(
        message,
        r"QR_Offense_Severity:(\w+)",
    )

    if value is None:
        return None

    return int(value)


def extract_mscI_message(message):
    match = re.search(
        r"MSCI_EID.*",
        to_string(message),
    )

    if match is None:
        return ""

    return match.group()


def extract_error_note(user_note):
    match = ERROR_NOTE_PATTERN.search(
        to_string(user_note)
    )

    if match is None:
        return None

    return {
        "raw": match.group(),
        "attempt": int(
            match.group(1)
        ),
        "timestamp": int(
            match.group(2)
        ),
    }


def build_error_note(
    attempt,
    timestamp=None,
):
    if timestamp is None:
        timestamp = current_timestamp()

    return "{}-Error:{}".format(
        attempt,
        timestamp,
    )


def prepend_error_note(
    user_note,
    attempt,
):
    error_note = build_error_note(
        attempt
    )

    return "[{}] {}".format(
        error_note,
        to_string(user_note),
    )


def replace_error_note(
    user_note,
    attempt,
):
    error_note = extract_error_note(
        user_note
    )

    if error_note is None:
        return prepend_error_note(
            user_note,
            attempt,
        )

    new_error_note = build_error_note(
        attempt
    )

    return to_string(
        user_note
    ).replace(
        "[{}]".format(
            error_note["raw"]
        ),
        "[{}]".format(
            new_error_note
        ),
    )


def get_error_attempt(user_note):
    error_note = extract_error_note(
        user_note
    )

    if error_note is None:
        return 0

    return error_note["attempt"]


def get_error_timestamp(user_note):
    error_note = extract_error_note(
        user_note
    )

    if error_note is None:
        return None

    return error_note["timestamp"]


def build_event_user_note(
    case_status,
    assigned_group,
    ext_ticket_ref,
):
    return "[{}:{}:{}]".format(
        to_string(case_status),
        to_string(assigned_group),
        to_string(ext_ticket_ref),
    )


def get_response_attribute(
    response,
    attribute_name,
    default="",
):
    value = getattr(
        response,
        attribute_name,
        None,
    )

    if value is None:
        return default

    return to_string(value)


def get_root_device_ip(
    dbc,
    component_device_id,
):
    query = (
        "SELECT ld.ip "
        "FROM master_dev.legend_device ld "
        "WHERE ld.id = ("
        "SELECT cdm.root_did "
        "FROM master_dev.component_dev_map cdm "
        "WHERE cdm.component_did = {}"
        ")"
    ).format(
        component_device_id
    )

    return dbc.autofetch_value(
        query
    )


def get_component_dn(
    dbc,
    component_id,
):
    query = (
        "SELECT dn "
        "FROM master_dev.component_dev_map "
        "WHERE component_did={}"
    ).format(
        component_id
    )

    return dbc.autofetch_value(
        query
    )


def acknowledge_event_sql(
    dbc,
    event_id,
    user_id,
):
    query = (
        "update master_events.events_active ea "
        "set user_ack ={} "
        "where ea.id = {};"
    ).format(
        user_id,
        event_id,
    )

    return dbc.execute(
        query
    )


def get_interface_by_name(
    dbc,
    device_id,
    interface_name,
):
    query = (
        "select if_id, name "
        "from master_dev.device_interfaces "
        "where name = '{}' "
        "and did = {}"
    ).format(
        to_string(
            interface_name
        ).strip(),
        device_id,
    )

    dbc.execute(query)

    rows = dbc.fetchall()

    if not rows:
        return None

    return rows[0]


def get_interface_tags(
    dbc,
    interface_id,
):
    query = (
        "SELECT tag_name "
        "FROM master_dev.device_interface_tags_map ditm "
        "JOIN master_dev.device_interface_tags dit "
        "ON dit.tag_id = ditm.tag_id "
        "WHERE ditm.if_id = {}"
    ).format(
        interface_id
    )

    dbc.execute(query)

    rows = dbc.fetchall()

    return [
        tag
        for tags in rows
        for tag in tags
    ]


def get_interface_description(
    dbc,
    interface_id,
):
    query = (
        "select if_id, ifDescr "
        "from master_dev.device_interfaces "
        "where if_id = {}"
    ).format(
        interface_id
    )

    dbc.execute(query)

    rows = dbc.fetchall()

    if not rows:
        return None

    return rows[0]


def get_sql_instance_details(
    dbc,
    parent_component_id,
):
    query = (
        "SELECT ld.device, cdm.dn "
        "FROM master_dev.component_dev_map cdm "
        "JOIN master_dev.legend_device ld "
        "ON ld.id = cdm.component_did "
        "WHERE cdm.parent_did = {}"
    ).format(
        parent_component_id
    )

    result = dbc.execute(query)

    if result == 0:
        return None

    rows = dbc.fetchall()

    if not rows:
        return None

    return {
        "instance_name": rows[0][0],
        "component_dn": rows[0][1],
    }


def get_device_certificates(
    dbc,
    device_id,
):
    query = (
        "SELECT certificate "
        "FROM master_dev.device_certificates dc "
        "WHERE dc.did = {}"
    ).format(
        device_id
    )

    dbc.execute(query)

    rows = dbc.fetchall()

    return [
        certificate[0]
        for certificate in rows
    ]


def strip_ilo_name(device_name):
    return (
        to_string(device_name)
        .strip("-ILO.")
        .strip("-ilo.")
        .strip("-iLO.")
    )


def strip_oob_name(device_name):
    return (
        to_string(device_name)
        .lstrip("OOB")
        .lstrip("oob")
        .lstrip("Oob")
    )


def parse_policy_id_list(value):
    return [
        item.strip()
        for item in (
            to_string(value)
            .strip("][")
            .split(",")
        )
        if item.strip()
    ]


def build_alert_payload(
    message,
    device_id,
):
    return {
        "force_ytype": "0",
        "force_yid": "0",
        "force_yname": "",
        "message": to_string(message),
        "value": "",
        "threshold": "",
        "message_time": "",
        "aligned_resource": (
            "/api/device/{}"
        ).format(
            device_id
        ),
    }
