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
    """

    This helper normalizes values coming from event data, database results, or API responses so they can be safely logged, stored, or used in payload fields.

    Args:
        value: A value from the current integration workflow that needs to be converted to text.

    Returns:
        The supplied value as a string, or an empty string when the input is None.

    Side Effects:
        None.

    Failure Behaviour:
        The function handles None values safely and does not raise an exception.
    """
    if value is None:
        return ""

    return str(value)


def clean_ascii(value):
    """

    This helper cleans event message content so that Remedy payloads and log messages remain readable and do not contain control characters from SL1 data.

    Args:
        value: A string value that may contain unexpected control or non-printable characters.

    Returns:
        A cleaned string that keeps only printable characters.

    Side Effects:
        None.

    Failure Behaviour:
        The function converts missing values to an empty string and continues processing.
    """
    value = to_string(value)

    return "".join(
        character
        for character in value
        if character in PRINTABLE_CHARACTERS
    )


def clean_html(value):
    """

    This helper is used when SL1 event notes or resolutions contain HTML fragments that should be presented as plain text in Remedy and logs.

    Args:
        value: A value that may contain HTML tags and escaped entities.

    Returns:
        A cleaned plain-text string with HTML tags removed and entities decoded.

    Side Effects:
        None.

    Failure Behaviour:
        The function falls back to an empty string if the supplied value cannot be processed.
    """
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
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        value: The value supplied to this function by the current integration workflow.
        max_length: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    value = to_string(value)

    if len(value) <= max_length:
        return value

    return value[:max_length]


def clean_pc_resolution(value):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        value: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    value = clean_html(value)

    return truncate(
        value,
        4096,
    )


def safe_int(value, default=0):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        value: The value supplied to this function by the current integration workflow.
        default: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        value: The value supplied to this function by the current integration workflow.
        default: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def safe_threshold(value):
    """

    This helper is used when SL1 sends a threshold or magnitude value as a string or decimal and the integration needs a simple integer value.

    Args:
        value: A threshold or magnitude value from the current event.

    Returns:
        The integer form of the value, or 0 when conversion is not possible.

    Side Effects:
        None.

    Failure Behaviour:
        Invalid values fall back to 0.
    """
    try:
        return int(float(value))

    except (TypeError, ValueError):
        return 0


def convert_sl1_datetime_to_remedy(value):
    """

    This helper translates the date values received from ScienceLogic into the format expected by the Remedy SOAP payload.

    Args:
        value: An SL1 date string in the standard SL1 datetime format.

    Returns:
        A Remedy-compatible datetime string formatted for the ticket payload.

    Side Effects:
        None.

    Failure Behaviour:
        Invalid datetime values cause the function to raise a parsing error because the integration expects a valid SL1 timestamp.
    """
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
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        value: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    return datetime.datetime.strptime(
        to_string(value),
        SL1_DATETIME_FORMAT,
    )


def datetime_to_timestamp(value):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        value: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    return int(
        time.mktime(
            time.strptime(
                to_string(value),
                SL1_DATETIME_FORMAT,
            )
        )
    )


def current_timestamp():
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        None.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    return int(time.time())


def current_datetime():
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        None.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    return datetime.datetime.now()


def has_interval_elapsed(
    timestamp,
    interval_seconds,
):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        timestamp: The value supplied to this function by the current integration workflow.
        interval_seconds: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
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
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        date_last: The value supplied to this function by the current integration workflow.
        interval_seconds: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
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
    """

    This helper evaluates the current event state and returns a simple boolean result used by the surrounding workflow.

    Args:
        value: The value supplied to this function by the current integration workflow.
        hours: The value supplied to this function by the current integration workflow.

    Returns:
        True when the condition is met, otherwise False.

    Side Effects:
        None.

    Failure Behaviour:
        The function uses the existing implementation and does not add extra exception handling.
    """
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
    """

    This helper reads the relevant data from the current event, payload, or database context so the surrounding workflow can continue.

    Args:
        automation_policy_name: The value supplied to this function by the current integration workflow.

    Returns:
        The requested value for the calling workflow.

    Side Effects:
        May read event data, query the SL1 database, or access the current payload context.

    Failure Behaviour:
        The function follows the existing implementation and returns the best available result when the expected value is not present.
    """
    return to_string(
        automation_policy_name
    ).split(":")


def get_automation_action(
    automation_policy_name,
):
    """

    This helper reads the relevant data from the current event, payload, or database context so the surrounding workflow can continue.

    Args:
        automation_policy_name: The value supplied to this function by the current integration workflow.

    Returns:
        The requested value for the calling workflow.

    Side Effects:
        May read event data, query the SL1 database, or access the current payload context.

    Failure Behaviour:
        The function follows the existing implementation and returns the best available result when the expected value is not present.
    """
    details = get_automation_details(
        automation_policy_name
    )

    if len(details) <= 2:
        return ""

    return details[2].strip()


def get_application_type(
    automation_policy_name,
):
    """

    This helper reads the relevant data from the current event, payload, or database context so the surrounding workflow can continue.

    Args:
        automation_policy_name: The value supplied to this function by the current integration workflow.

    Returns:
        The requested value for the calling workflow.

    Side Effects:
        May read event data, query the SL1 database, or access the current payload context.

    Failure Behaviour:
        The function follows the existing implementation and returns the best available result when the expected value is not present.
    """
    details = get_automation_details(
        automation_policy_name
    )

    if len(details) <= 3:
        return ""

    return details[3].strip()


def is_create_ticket_action(
    automation_policy_name,
):
    """

    This helper decides whether the workflow should build a create payload and call the Remedy create operation.

    Args:
        automation_policy_name: The policy name from the current SL1 event.

    Returns:
        True when the action is NewTicket or ImmediateTicket, otherwise False.

    Side Effects:
        None.

    Failure Behaviour:
        Missing or malformed values evaluate to False.
    """
    return get_automation_action(
        automation_policy_name
    ) in (
        "NewTicket",
        "ImmediateTicket",
    )


def is_clear_ticket_action(
    automation_policy_name,
):
    """

    This helper identifies events that should update an existing incident with a cleared state instead of creating a new ticket.

    Args:
        automation_policy_name: The policy name from the current SL1 event.

    Returns:
        True when the action includes ClearTicket, otherwise False.

    Side Effects:
        None.

    Failure Behaviour:
        Missing values evaluate to False.
    """
    return (
        "ClearTicket"
        in to_string(
            automation_policy_name
        )
    )


def has_incident_number(value):
    """

    This helper identifies whether an event already has a Remedy incident number that can be used for an update operation.

    Args:
        value: A ticket reference value from the current event or Remedy response.

    Returns:
        True when the value contains INC, otherwise False.

    Side Effects:
        None.

    Failure Behaviour:
        Missing values are treated as empty strings and evaluate to False.
    """
    return (
        "INC"
        in to_string(value)
    )


def starts_with_incident_number(value):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        value: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    return (
        to_string(value)[:3]
        == "INC"
    )


def extract_regex_value(
    value,
    pattern,
    group=1,
):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        value: The value supplied to this function by the current integration workflow.
        pattern: The value supplied to this function by the current integration workflow.
        group: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    match = re.search(
        pattern,
        to_string(value),
    )

    if match is None:
        return None

    return match.group(group)


def extract_qradar_magnitude(message):
    """

    This helper supports the QRadar-specific scenario handling that decides whether a ticket should be created.

    Args:
        message: The event message text that contains the QRadar metadata.

    Returns:
        The numeric magnitude value, or None when it cannot be found.

    Side Effects:
        None.

    Failure Behaviour:
        If the magnitude is missing or invalid, the function returns None.
    """
    value = extract_regex_value(
        message,
        r"QR_Offense_magnitude:(\w+)",
    )

    if value is None:
        return None

    return int(value)


def extract_qradar_severity(message):
    """

    This helper supports the QRadar-specific scenario handling that evaluates ticket eligibility.

    Args:
        message: The event message text that contains the QRadar metadata.

    Returns:
        The numeric severity value, or None when it cannot be found.

    Side Effects:
        None.

    Failure Behaviour:
        If the severity is missing or invalid, the function returns None.
    """
    value = extract_regex_value(
        message,
        r"QR_Offense_Severity:(\w+)",
    )

    if value is None:
        return None

    return int(value)


def extract_mscI_message(message):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        message: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    match = re.search(
        r"MSCI_EID.*",
        to_string(message),
    )

    if match is None:
        return ""

    return match.group()


def extract_error_note(user_note):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        user_note: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
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
    """

    This helper formats the retry marker used by the integration to track repeated failing attempts.

    Args:
        attempt: The retry attempt number to write into the marker.
        timestamp: An optional timestamp to include in the marker.

    Returns:
        The formatted retry marker string.

    Side Effects:
        None.

    Failure Behaviour:
        When no timestamp is provided, the current time is used.
    """
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
    """

    This helper is used when the first ticket creation failure is recorded in the SL1 event user note.

    Args:
        user_note: The existing user note text.
        attempt: The retry attempt number to prepend.

    Returns:
        A new user note containing the retry marker and original note text.

    Side Effects:
        None.

    Failure Behaviour:
        Missing values are converted to strings and processed safely.
    """
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
    """

    This helper advances the retry marker when the integration retries ticket handling after a previous failure.

    Args:
        user_note: The current user note text.
        attempt: The next retry attempt number.

    Returns:
        The updated user note with the new retry marker.

    Side Effects:
        None.

    Failure Behaviour:
        If no existing marker is present, the function adds a new marker at the beginning.
    """
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
    """

    This helper is used during exception handling to determine the current retry level.

    Args:
        user_note: The user note text that may contain a retry marker.

    Returns:
        The retry attempt number, or 0 when no marker exists.

    Side Effects:
        None.

    Failure Behaviour:
        Missing or malformed markers return 0.
    """
    error_note = extract_error_note(
        user_note
    )

    if error_note is None:
        return 0

    return error_note["attempt"]


def get_error_timestamp(user_note):
    """

    This helper is used to decide whether enough time has passed before a retry should proceed.

    Args:
        user_note: The user note text containing the retry marker.

    Returns:
        The embedded timestamp as an integer, or None when it is absent.

    Side Effects:
        None.

    Failure Behaviour:
        If the marker cannot be parsed, the function returns None.
    """
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
    """

    This helper formats the case status, assigned group, and incident reference into the text expected by the integration.

    Args:
        case_status: The Remedy case status to include.
        assigned_group: The Remedy assigned group to include.
        ext_ticket_ref: The Remedy incident reference to include.

    Returns:
        A formatted bracketed user note string.

    Side Effects:
        None.

    Failure Behaviour:
        Missing values are converted to empty strings.
    """
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
    """

    This helper reads the relevant data from the current event, payload, or database context so the surrounding workflow can continue.

    Args:
        response: The value supplied to this function by the current integration workflow.
        attribute_name: The value supplied to this function by the current integration workflow.
        default: The value supplied to this function by the current integration workflow.

    Returns:
        The requested value for the calling workflow.

    Side Effects:
        May read event data, query the SL1 database, or access the current payload context.

    Failure Behaviour:
        The function follows the existing implementation and returns the best available result when the expected value is not present.
    """
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
    """

    This helper uses the SL1 database connection to retrieve the IP address of the parent or root device needed for the Remedy payload.

    Args:
        dbc: The SL1 database cursor object.
        component_device_id: The component device identifier used in the query.

    Returns:
        The root device IP returned by the database query.

    Side Effects:
        Queries the SL1 database.

    Failure Behaviour:
        If no value is found, the database helper returns None.
    """
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
    """

    This helper retrieves the configuration data needed for SQL and database-specific scenario handling.

    Args:
        dbc: The SL1 database cursor object.
        component_id: The component identifier used in the query.

    Returns:
        The component distinguished name returned by the database query.

    Side Effects:
        Queries the SL1 database.

    Failure Behaviour:
        If no value is found, the database helper returns None.
    """
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
    """

    This helper updates the SL1 event acknowledgement field so the event is no longer pending action after ticket processing.

    Args:
        dbc: The SL1 database cursor object.
        event_id: The SL1 event identifier to update.
        user_id: The user identifier that should appear in the acknowledgement field.

    Returns:
        The result returned by the database execution call.

    Side Effects:
        Updates an SL1 event via the database.

    Failure Behaviour:
        The function relies on the underlying database execution result and does not add extra handling.
    """
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
    """

    This helper supports network interface scenario handling that needs the interface identifier and name for the payload.

    Args:
        dbc: The SL1 database cursor object.
        device_id: The device identifier to search within.
        interface_name: The interface name used in the query.

    Returns:
        The matching interface row as returned by the database query, or None when no interface matches.

    Side Effects:
        Queries the SL1 database.

    Failure Behaviour:
        If no rows are found, the function returns None.
    """
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
    """

    This helper is used by the interface scenario to determine whether the interface is eligible for ticket creation.

    Args:
        dbc: The SL1 database cursor object.
        interface_id: The interface identifier used in the query.

    Returns:
        A list of tag names associated with the interface.

    Side Effects:
        Queries the SL1 database.

    Failure Behaviour:
        If no tags are found, the function returns an empty list.
    """
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
    """

    This helper provides the interface description used by the interface scenario when the event payload needs the port name.

    Args:
        dbc: The SL1 database cursor object.
        interface_id: The interface identifier whose description is needed.

    Returns:
        The interface description row, or None when no matching interface exists.

    Side Effects:
        Queries the SL1 database.

    Failure Behaviour:
        If no matching interface is found, the function returns None.
    """
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
    """

    This helper is used by the SQL Server scenario logic to identify the database instance and component path for the payload.

    Args:
        dbc: The SL1 database cursor object.
        parent_component_id: The parent component identifier used in the query.

    Returns:
        A dictionary with the instance name and component distinguished name, or None when no data is found.

    Side Effects:
        Queries the SL1 database.

    Failure Behaviour:
        If the query returns no rows, the function returns None.
    """
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
    """

    This helper supports the SSL certificate scenario by retrieving the device certificates from the SL1 database.

    Args:
        dbc: The SL1 database cursor object.
        device_id: The device identifier used in the database query.

    Returns:
        A list of certificate values belonging to the device.

    Side Effects:
        Queries the SL1 database.

    Failure Behaviour:
        If no certificates are found, the function returns an empty list.
    """
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
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        device_name: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    return (
        to_string(device_name)
        .strip("-ILO.")
        .strip("-ilo.")
        .strip("-iLO.")
    )


def strip_oob_name(device_name):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        device_name: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
    return (
        to_string(device_name)
        .lstrip("OOB")
        .lstrip("oob")
        .lstrip("Oob")
    )


def parse_policy_id_list(value):
    """

    This helper supports the SL1 to Remedy workflow by carrying out the operation defined by the current function implementation.

    Args:
        value: The value supplied to this function by the current integration workflow.

    Returns:
        The value returned by the current implementation.

    Side Effects:
        May write logs, update payload data, or touch the surrounding workflow state.

    Failure Behaviour:
        The function follows the existing implementation and uses the same failure behaviour already present in the code.
    """
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
    """

    This helper prepares the alert structure that the integration sends when a non-ticketable or failure condition needs to be recorded in ScienceLogic.

    Args:
        message: The alert message text.
        device_id: The device identifier that should be associated with the alert.

    Returns:
        A dictionary payload for the SL1 alert API call.

    Side Effects:
        None.

    Failure Behaviour:
        The function does not raise an exception for missing values; it converts them to strings.
    """
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
