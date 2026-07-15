# ScienceLogic SL1 – Remedy Ticket Integration

## Overview

This automation integrates ScienceLogic SL1 events with the Remedy ticketing system.

The purpose of the automation is simple:

> Whenever ScienceLogic processes an event through the configured Run Book Automation, determine whether the event is ticketable, apply the required business rules, create or update a Remedy incident, and update the ScienceLogic event with the ticket result.

The integration supports both ticket creation and ticket updates.

The code has been rearranged into two Python files to make it easier to maintain and execute inside the ScienceLogic SL1 environment.

```text
main.py
helpers.py
```

The refactoring is primarily a code rearrangement.

The existing business rules, Remedy payload structure, ScienceLogic API interactions, database lookups and retry behaviour are intended to remain unchanged.

---

# Architecture

The overall execution flow is:

```text
ScienceLogic Event
        |
        v
Run Book Automation
        |
        v
main.py
        |
        +--> Read EM7_VALUES
        |
        +--> Initialise database connection
        |
        +--> Initialise logging
        |
        +--> Build Remedy payload
        |
        +--> Apply scenario handling
        |
        +--> Create or update Remedy ticket
        |
        +--> Process Remedy response
        |
        +--> Update ScienceLogic event
        |
        +--> Handle retry or failure
        |
        v
Final statistics and logs
```

The integration communicates with three main components:

```text
ScienceLogic SL1
        |
        | Run Book Event Variables
        |
        v
Python Integration
        |
        +---------------------+
        |                     |
        v                     v
SL1 REST API            Remedy SOAP API
```

The integration also directly queries the ScienceLogic database for specific scenario information.

---

# Files

## main.py

`main.py` contains all ScienceLogic and Remedy integration logic.

This includes:

* SL1 Run Book execution
* Logging configuration
* Database connection
* Remedy payload construction
* Scenario handling
* ScienceLogic database queries
* ScienceLogic REST API calls
* Remedy SOAP calls
* Ticket creation
* Ticket updates
* Remedy response processing
* Event acknowledgement
* Retry handling
* Failure handling
* Final execution flow

Any function that depends on the following remains in `main.py`:

```text
EM7_VALUES
event_id
device_ID
dbc
stats
logger
ScienceLogic database tables
ScienceLogic REST API
Remedy SOAP API
```

Examples include:

```text
build_create_payload
build_update_payload
scenarios_handling
call_sl_api
call_remedy_web_service
create_remedy_ticket
update_remedy_ticket
ticket_handling
exception_handling
process_event
main
```

---

## helpers.py

`helpers.py` contains only generic reusable utility functions.

A helper function should receive an input and return an output without knowing anything about ScienceLogic or Remedy.

Example:

```text
Input
  |
  v
Helper Function
  |
  v
Output
```

The helper module contains functionality for:

* String conversion
* ASCII cleanup
* HTML cleanup
* String truncation
* Number conversion
* Threshold conversion
* Date and time conversion
* Automation policy parsing
* Regex extraction
* QRadar message parsing
* Error marker parsing
* Incident number checks
* Small value transformations

Examples include:

```text
to_string
clean_ascii
clean_html
truncate
clean_pc_resolution
safe_int
safe_float
safe_threshold
convert_sl1_datetime_to_remedy
get_application_type
is_create_ticket_action
is_clear_ticket_action
has_incident_number
extract_regex_value
extract_qradar_magnitude
extract_qradar_severity
```

`helpers.py` must not directly access:

```text
EM7_VALUES
dbc
stats
event_id
logger
ScienceLogic tables
ScienceLogic APIs
Remedy APIs
```

---

# Requirements

The automation is designed to execute inside the ScienceLogic SL1 Run Book environment.

The following ScienceLogic modules must be available:

```python
from silo.apps.sl1_data_model import get_cred_array_from_id
from silo.apps.storage import dbc_cursor
```

The following Python packages are required:

```text
requests
pytz
suds
```

The code also uses Python standard library modules:

```text
datetime
json
logging
re
ssl
string
time
html
```

The ScienceLogic execution environment must provide the `EM7_VALUES` Run Book variable dictionary.

The required configuration values must also be available from the Run Book Action or execution environment.

Examples include:

```text
log_file_name
sl_db_credential_id
remedy_create_update_ticket_webservice_credential_id
ack_user_tktable_alert
ack_user_non_tktable_alert
force_ticket_uri
availability_ep_id
availability_latency_ep_id
ep_create_ticket_SLDB
cdb_device_id
cdb_device_ip
cdb_device_name
modification_interval
qradar_magnitude_ticketing_threshold
```

These values are not hard-coded by the integration.

They are expected to be provided by the ScienceLogic Run Book Action configuration.

---

# Initialisation

When the script starts, it first determines the log file.

Create and immediate-ticket actions use the configured integration log file.

Update actions use:

```text
/data/logs/SLRemedyIntegration/v1/ProdRemedy/UpdateTicket.log
```

The action type is identified from the Automation Policy name.

The Automation Policy name is split using `:`.

Example:

```text
Remedy:Ticket:NewTicket:Device
```

The third value represents the action.

```text
NewTicket
ImmediateTicket
ClearTicket
```

The fourth value represents the application type.

Example:

```text
Device
NetworkPort
DB_Database
DB_Instance
Cluster
```

---

# Logging

The integration uses Python file logging.

The logger is configured as:

```text
Logger name: current module name
Log level: DEBUG
Output: File
```

The log format is:

```text
timestamp,level,line_number,message
```

Example:

```text
2026-07-14 10:10:25,INFO,125,[EID:123456]: Remedy integration started
```

Most integration log messages contain the ScienceLogic Event ID.

Example:

```text
[EID:123456]
```

This makes it possible to trace the complete processing flow for one event.

---

# Runtime Values

The integration reads important values from `EM7_VALUES`.

The main runtime values include:

```text
event_id
event_message
event_policy
device_ID
ext_ticket_ref
user_note
```

A legacy ScienceLogic database cursor is created using:

```text
dbc_cursor(legacy=True)
```

The integration also maintains a statistics dictionary.

The statistics contain:

```text
EID
Device_ID
Device_Name
date_first
date_last
date_del
ext_ticket_ref
AST
AET
TRQT
TRRT
```

`AST` represents the automation start time.

`AET` represents the automation end time.

`TRQT` is retained as part of the existing statistics structure.

`TRRT` records Remedy request or response timing information used by the existing integration.

---

# Main Execution Flow

The execution starts by calling:

```text
main()
```

The high-level flow is:

```text
main
 |
 v
process_event
 |
 v
ticket_handling
 |
 +--> Create Ticket
 |
 +--> Update Ticket
 |
 v
Success?
 |
 +--> Yes --> Complete
 |
 +--> No --> exception_handling
 |
 v
Update final statistics
 |
 v
Write final log
```

---

# Ticket Action Detection

The integration reads the Automation Policy name from:

```text
EM7_VALUES["%n"]
```

The Automation Policy name determines whether the event is a create-ticket or update-ticket operation.

The following actions create Remedy tickets:

```text
NewTicket
ImmediateTicket
```

All other supported actions are processed through the update-ticket flow.

---

# Create Ticket Flow

The create-ticket flow starts with:

```text
build_create_payload
```

The default Remedy payload is created from ScienceLogic event information.

The payload contains:

```text
resource_name
subresource_name
date_last
severity
date_first
device_ip
device_name
device_class
device_subclass
device_id
counter
EID
user_notes
source
org_id
org_name
message
evt_policy_name
evt_policy_id
evt_policy_severity
user_del
date_active
msg_val
threshold
label
device_parent
device_child
correlation_reason
org_city
org_state
org_address
date_del
date_ack
user_ack
vendor_name
vendor_case_id
application_type
```

For create operations, the ScienceLogic Event ID is converted to a negative value before being sent to Remedy.

Example:

```text
ScienceLogic EID: 123456

Remedy EID: -123456
```

---

# PC Resolution Processing

The ScienceLogic event policy cause or resolution text is read from:

```text
EM7_VALUES["%R"]
```

The value is cleaned before it is added to the Remedy user notes.

The processing includes:

```text
Remove non-ASCII characters
Convert selected HTML tags to new lines
Remove remaining HTML tags
Decode HTML entities
Trim whitespace
Limit the value to 4096 characters
```

The cleaned value is appended to the existing ScienceLogic user note.

---

# Scenario Handling

After the default create payload is generated, it is passed to:

```text
scenarios_handling
```

The scenario handler applies event-specific business rules.

The scenario order is important.

The current order is:

```text
1. Device Availability
2. CDB Redirection
3. Interface Events
4. NICE Support Components
5. PDCAD Components
6. SQL Server Database
7. SQL Server Instance
8. SQL Server
9. MySQL
10. Windows Cluster
11. F5 BIG-IP
12. SSL Certificate
13. Vesta Forward Trap
14. Vesta MSCI Trap
15. ILO
16. OOB
17. NetApp
18. RackArmor
19. Dell EMC VMAX
20. QRadar
```

The scenario order must not be changed without reviewing the business impact.

---

# Availability Event Handling

Availability events are checked for an active Device Availability and Latency event on the same device.

If the related event exists:

```text
Ticket creation is skipped
```

The event is acknowledged using the configured non-ticketable service account.

The statistics external ticket reference is set to:

```text
Availability-NonTickable
```

---

# CDB Event Handling

Configured CDB event policies are redirected to the ScienceLogic CDB device.

The original device name is added to the event message.

The payload device information is replaced with:

```text
cdb_device_ip
cdb_device_name
```

Event policy ID `7419` has a special rule.

The event must be at least 72 hours old before a ticket is created.

If the event is less than 72 hours old:

```text
Ticket creation is skipped
```

---

# Interface Event Handling

Interface events are identified using the ScienceLogic sub-entity type.

The interface ID is obtained from the event.

If the interface ID is `0`, the integration searches the ScienceLogic database using:

```text
Device ID
Interface name
```

The integration then checks the interface tags.

The interface must contain:

```text
AUTO TICKET
```

If the tag is missing:

```text
Ticket creation is skipped
Event is acknowledged as non-ticketable
```

The statistics external ticket reference is set to:

```text
Interface-NonTickable
```

For ticketable interfaces, the application type is changed to:

```text
NetworkPort
```

The interface name or interface description is used as the Remedy subresource name.

---

# NICE and PDCAD Component Handling

Component events belonging to:

```text
Public Safety NICE Support
Public Safety PDCAD
```

and having no direct device IP are redirected to their root ScienceLogic device.

The integration retrieves the root device IP from the ScienceLogic database.

The payload is updated with:

```text
Root device IP
Root device name
Application type: Device
```

---

# SQL Server Database Handling

SQL Server Database events use the root device as the Remedy resource.

The component distinguished name is retrieved from the ScienceLogic database.

The Remedy application type is:

```text
DB_Database
```

The database name is added to the Remedy message.

When a component distinguished name is available, it is used to build the subresource name.

---

# SQL Server Instance Handling

SQL Server Instance events use the root device as the Remedy resource.

The component distinguished name is retrieved from the ScienceLogic database.

The Remedy application type is:

```text
DB_Instance
```

The instance information is used to construct the Remedy subresource name.

---

# SQL Server Handling

For SQL Server parent component events, the integration searches for a child SQL instance.

When an instance is found:

```text
Instance name
Component distinguished name
```

are used to construct the Remedy payload.

If no instance is found, the existing payload device name is used.

The application type is:

```text
DB_Instance
```

---

# MySQL Handling

The following device classes are handled as MySQL components:

```text
MySQL Server
MySQL Instance
```

The Remedy resource and device names are replaced with the ScienceLogic root device name.

---

# Windows Cluster Handling

Windows cluster component classes are mapped to the root device.

The Remedy application type is:

```text
Cluster
```

The subresource name is set to:

```text
0
```

---

# F5 BIG-IP Handling

F5 BIG-IP component events are redirected to the root ScienceLogic device.

Supported classes include:

```text
BIG-IP Local Traffic Manager
BIG-IP LTM Virtual Server
BIG-IP LTM Pool
BIG-IP LTM Pool Member
BIG-IP LTM Node
```

The root device IP and root device name are used in the Remedy payload.

---

# SSL Certificate Handling

The SSL certificate expiry event policy is specially handled.

The integration retrieves all certificates associated with the device from the ScienceLogic database.

The certificate information is appended to the Remedy event message.

---

# Vesta Forward Trap Handling

Vesta Forward Trap events extract:

```text
Motorola case number
Vesta device IP
```

from the event message.

The Remedy vendor information is set to:

```text
Vendor Name: Vesta Solutions
Vendor Case ID: extracted case number
```

The event message is cleaned before being sent to Remedy.

---

# Vesta MSCI Trap Handling

Vesta MSCI events extract the Motorola event ID from the ScienceLogic subresource name.

The source device IP is extracted from the event message.

The Remedy vendor information is:

```text
Vendor Name: MSCI Vesta Solutions
Vendor Case ID: Motorola Event ID
```

The Remedy message is reduced to the MSCI event message beginning with:

```text
MSCI_EID
```

If the ScienceLogic device name contains:

```text
MSCI_TRAP_Source
```

the Remedy user notes indicate that the asset does not exist in Public Safety ScienceLogic.

---

# ILO Handling

ILO device names are normalised before being sent to Remedy.

The ILO naming variations handled are:

```text
-ILO.
-ilo.
-iLO.
```

The normalised device name is used as:

```text
resource_name
device_name
```

---

# OOB Handling

Out-of-band device names beginning with:

```text
OOB
oob
Oob
```

are normalised.

The resulting device name is used as:

```text
resource_name
device_name
```

---

# NetApp Handling

NetApp events use the root ScienceLogic device when a root device exists.

The payload is updated with:

```text
Root device IP
Root device name
Original component name as subresource
```

The component name is also added to the Remedy message.

The application type is:

```text
Cluster
```

---

# RackArmor Handling

RackArmor events extract the device IP and device name directly from the event message.

The extracted values are used as:

```text
device_ip
resource_name
device_name
```

---

# Dell EMC VMAX Handling

Dell EMC VMAX events use the root ScienceLogic device.

The Remedy message is enriched with:

```text
Component name
Parent component name
Original event message
```

---

# QRadar Handling

QRadar events extract:

```text
QR_Offense_magnitude
QR_Offense_Severity
```

from the event message.

The magnitude is compared with:

```text
qradar_magnitude_ticketing_threshold
```

If the magnitude is greater than the configured threshold:

```text
Ticket creation continues
```

Otherwise:

```text
Ticket creation is skipped
Event is acknowledged as non-ticketable
```

The statistics external ticket reference is set to:

```text
Qradar-NonTickable
```

QRadar severity is currently parsed and logged but is not used in the ticketing decision.

---

# Remedy Web Service

Remedy is accessed through a SOAP web service.

The Remedy credentials are retrieved from the ScienceLogic credential store using:

```text
remedy_create_update_ticket_webservice_credential_id
```

The credential provides:

```text
curl_url
cred_user
cred_pwd
```

The Suds SOAP client is created using the configured Remedy URL.

An `AuthenticationInfo` SOAP header is created.

The Remedy username and password are assigned to the authentication header.

The SOAP header is then attached to the Remedy client.

---

# Remedy Ticket Creation

Ticket creation uses the Remedy SOAP operation:

```text
Create_Operation
```

The final scenario-processed payload is passed to the operation.

The Remedy response is then processed.

---

# Remedy Create Response Handling

The integration handles the following Remedy responses:

```text
INC Incident Number
AutoTicketing Disabled
Planned Outage
Incident App Failure
```

---

# Normal Remedy Incident

If the Remedy external ticket reference begins with:

```text
INC
```

the integration reads:

```text
HDCaseStatus
Assigned_Group
ext_ticket_ref
```

The ScienceLogic event user note is built as:

```text
[CaseStatus:AssignedGroup:IncidentNumber]
```

The ScienceLogic event is updated with:

```text
user_ack
ext_ticket_ref
user_note
force_ticket_uri
```

The event is acknowledged using the configured Remedy ticketable service account.

---

# AutoTicketing Disabled and Planned Outage

When Remedy returns:

```text
AutoTicketing Disabled
```

or:

```text
Planned Outage
```

the ScienceLogic event is updated with:

```text
user_ack
ext_ticket_ref
```

No normal Remedy incident number is expected.

---

# Incident App Failure

When Remedy returns:

```text
Incident App Failure
```

the ScienceLogic event is updated with:

```text
user_ack
ext_ticket_ref
user_note
```

An additional ScienceLogic alert is created.

The alert message contains:

```text
Incident App Failure on EID
Original Event Severity
```

The alert is aligned to the configured CDB device.

---

# Update Ticket Flow

Update payloads are created using:

```text
build_update_payload
```

The Remedy update operation is:

```text
Modify_Operation
```

For events with an Event ID greater than or equal to:

```text
12632565
```

the Event ID is converted to a negative value.

Older event IDs remain unchanged.

---

# Clear Ticket Handling

Clear actions are identified using:

```text
ClearTicket
```

The event must contain a Remedy incident number.

The ScienceLogic user note must not contain:

```text
Resolved
Closed
```

When these conditions are satisfied, the update payload severity is changed to:

```text
0
```

The payload is then sent to Remedy.

---

# Normal Ticket Update

For normal ticket updates, the event must have been modified inside the configured:

```text
modification_interval
```

The event must also contain a Remedy incident number.

If either condition fails:

```text
The Remedy update is skipped
```

If both conditions are satisfied:

```text
Modify_Operation
```

is called.

---

# ScienceLogic REST API

The integration uses the ScienceLogic REST API for:

```text
Updating events
Creating alerts
```

ScienceLogic credentials are retrieved using:

```text
sl_db_credential_id
```

The API URL is built using:

```text
credential curl_url
/api/
endpoint
```

The request uses HTTP Basic Authentication.

The request body is JSON.

SSL certificate verification is currently disabled.

---

# Exception and Retry Handling

Ticket failures are tracked using the ScienceLogic event user note.

The retry sequence is:

```text
1-Error
2-Error
3-Error
4-Error
5-Error
6-Failure
```

The error marker format is:

```text
[1-Error:TIMESTAMP]
```

Example:

```text
[1-Error:1784000000]
```

The timestamp records when the current retry level was created.

---

# First Ticket Failure

When ticket processing fails and the event user note does not contain an error marker, the integration adds:

```text
[1-Error:TIMESTAMP]
```

to the beginning of the existing user note.

Example:

```text
[1-Error:1784000000] Existing user note
```

---

# Retry Interval

Before retrying a failed ticket, the integration compares the error marker timestamp with:

```text
retry_interval
```

If the retry interval has not been reached:

```text
Ticket processing is not retried
```

If the retry interval has been reached:

```text
ticket_handling
```

is executed again.

The current implementation retains the original:

```text
retry_interval = 0
```

This means the retry is eligible whenever the Run Book executes again.

---

# Retry Progression

If a retry fails, the error marker is replaced.

Example:

```text
1-Error
   |
   v
2-Error
   |
   v
3-Error
   |
   v
4-Error
   |
   v
5-Error
```

Each new error marker receives a new timestamp.

---

# Final Failure

If ticket creation fails again after `5-Error`, the event is moved to:

```text
6-Failure
```

The ScienceLogic event is updated with:

```text
user_ack
user_note = 6-Failure
```

The event is acknowledged using the configured ticketable service account.

After the ScienceLogic event update succeeds, a new ScienceLogic alert is created.

The alert message begins with:

```text
Remedy Ticket Creation Failed:
AutoTicket Creation Failed on EID
```

The alert is aligned to the original event device.

---

# Statistics

The integration records execution statistics.

The statistics include:

```text
EID
Device_ID
Device_Name
date_first
date_last
date_del
ext_ticket_ref
AST
AET
TRQT
TRRT
```

At the end of execution:

```text
AET
```

must be updated with the current date and time.

The final statistics must be logged in the existing field order to preserve compatibility with operational log parsing.

---

# Important Maintenance Rules

This integration contains several event-specific business rules.

When changing the code:

1. Do not change scenario execution order without reviewing the business impact.

2. Do not change Remedy payload field names without confirming the Remedy SOAP contract.

3. Do not change `Create_Operation` or `Modify_Operation` names.

4. Do not change the retry marker format.

5. Do not remove the `1-Error` to `6-Failure` lifecycle.

6. Do not move ScienceLogic database functions into `helpers.py`.

7. Do not allow `helpers.py` to directly access `EM7_VALUES`.

8. Do not log ScienceLogic or Remedy credential passwords.

9. Preserve the final statistics field order if external log parsing depends on it.

10. Test all special scenarios before production deployment.

---

# Recommended Test Scenarios

Before deploying the rearranged code, test at least the following:

```text
Normal NewTicket event
ImmediateTicket event
ClearTicket event
Normal incident update
Availability suppression
CDB event
CDB policy 7419 less than 72 hours
CDB policy 7419 greater than 72 hours
Interface with AUTO TICKET tag
Interface without AUTO TICKET tag
NICE component
PDCAD component
SQL Server Database
SQL Server Instance
SQL Server parent component
MySQL
Windows Cluster
F5 BIG-IP
SSL certificate expiry
Vesta Forward Trap
Vesta MSCI Trap
ILO device
OOB device
NetApp
RackArmor
Dell EMC VMAX
QRadar above threshold
QRadar below threshold
Blank event message
Remedy INC response
AutoTicketing Disabled response
Planned Outage response
Incident App Failure response
ScienceLogic event API failure
First ticket failure
1-Error retry
2-Error retry
3-Error retry
4-Error retry
5-Error retry
6-Failure alert creation
```

---

# Current Refactoring Status

The original monolithic integration has been rearranged into smaller functions.

The intended production structure is:

```text
main.py
helpers.py
README.md
```

The refactoring improves readability by separating:

```text
Payload creation
Scenario handling
Service communication
Ticket processing
Retry handling
Execution flow
```

The business logic remains visible in `main.py`.

Generic value transformations remain in `helpers.py`.

Before production deployment, the rearranged `main.py` and `helpers.py` must be compared line-by-line against the original integration to confirm that all original operational behaviour has been retained.
