# SLSDK

A modular, reusable Python SDK for automating ScienceLogic SL1 event enrichment and external ticket lifecycle operations.

The SDK separates SL1 runtime access, database operations, repositories, business services, external clients, payload construction, and workflow orchestration using SOLID design principles.

---

## Architecture

```text
main.py
   │
   ▼
Application
   │
   ▼
Container
   │
   ▼
EventTicketWorkflow
   │
   ├── EventService
   │       │
   │       ▼
   │   EventRepository
   │
   ├── EnrichmentService
   │       │
   │       ├── DeviceService
   │       │       ▼
   │       │   DeviceRepository
   │       │
   │       ├── InterfaceService
   │       │       ▼
   │       │   InterfaceRepository
   │       │
   │       ├── ComponentService
   │       │       ▼
   │       │   ComponentRepository
   │       │
   │       └── CertificateService
   │               ▼
   │           CertificateRepository
   │
   ├── PayloadService
   │       ▼
   │   PayloadHelper
   │
   └── TicketService
           ▼
       BaseClient
           ▼
       RemedyClient
           ▼
       Remedy API
```

---

## Project Structure

```text
slsdk/
├── __init__.py
│
├── bootstrap/
│   ├── application.py
│   └── container.py
│
├── clients/
│   ├── base.py
│   └── remedy_client.py
│
├── config/
│   └── settings.py
│
├── core/
│   ├── context.py
│   └── exceptions.py
│
├── credentials/
│   ├── models.py
│   └── provider.py
│
├── database/
│   ├── connection.py
│   └── factory.py
│
├── helpers/
│   ├── datetime_helper.py
│   ├── message_parser.py
│   ├── payload_helper.py
│   └── string_helper.py
│
├── logging/
│   └── logger.py
│
├── models/
│   └── event.py
│
├── repositories/
│   ├── base.py
│   ├── certificate_repository.py
│   ├── component_repository.py
│   ├── device_repository.py
│   ├── event_repository.py
│   └── interface_repository.py
│
├── runtime/
│   └── sl1_runtime.py
│
├── services/
│   ├── certificate_service.py
│   ├── component_service.py
│   ├── device_service.py
│   ├── enrichment_service.py
│   ├── event_service.py
│   ├── interface_service.py
│   ├── payload_service.py
│   └── ticket_service.py
│
└── workflows/
    └── event_ticket_workflow.py

main.py
```

---

## Execution Flow

The application starts from:

```bash
python main.py <event_id>
```

Example:

```bash
python main.py 123456
```

The execution flow is:

```text
main.py
    │
    ▼
Application
    │
    ▼
Container
    │
    ▼
EventTicketWorkflow.execute(event_id)
    │
    ▼
EventService.to_model(event_id)
    │
    ▼
EventRepository.get_by_id(event_id)
    │
    ▼
Event Model
    │
    ▼
EnrichmentService.enrich(event)
    │
    ├── Device information
    ├── Interface information
    ├── Component information
    └── Certificate information
    │
    ▼
PayloadService.build(...)
    │
    ▼
Normalized Ticket Payload
    │
    ▼
TicketService.create_ticket(...)
    │
    ▼
RemedyClient.create(...)
    │
    ▼
Remedy API
```

---

## Core Layer

### `core/context.py`

Defines the execution context used by SL1 runtime operations.

The context represents runtime information associated with the current automation execution.

Example responsibilities:

* Event ID
* Device ID
* Organization ID
* Runtime metadata

The execution context prevents runtime-specific values from being passed individually across multiple modules.

---

### `core/exceptions.py`

Contains SDK-level exception definitions.

All reusable SDK exceptions should inherit from the base SDK exception.

Example:

```python
from slsdk.core.exceptions import SLSDKError
```

External integrations may define integration-specific exceptions derived from `SLSDKError`.

Example:

```python
class RemedyClientError(SLSDKError):
    pass
```

---

## Runtime Layer

### `runtime/sl1_runtime.py`

Provides an abstraction around the ScienceLogic SL1 execution environment.

The runtime layer isolates SL1-specific runtime behavior from the rest of the SDK.

This allows services and workflows to remain independent of the SL1 execution environment.

The runtime abstraction can also simplify testing outside ScienceLogic.

---

## Configuration

### `config/settings.py`

Central configuration object for the SDK.

Configuration values should be accessed through `Settings` rather than directly reading environment variables throughout the application.

Example:

```python
from slsdk.config.settings import Settings

settings = Settings()
```

Typical settings include:

```text
Database configuration
Remedy base URL
Remedy timeout
SSL verification
Credential configuration
Runtime configuration
```

Centralized configuration prevents configuration logic from leaking into services and repositories.

---

## Credentials

### `credentials/models.py`

Defines credential data structures.

Credentials are represented as structured objects rather than raw dictionaries.

Example concept:

```python
Credentials(
    username="user",
    password="password",
)
```

Token-based authentication can also be supported.

---

### `credentials/provider.py`

Responsible for retrieving credentials.

Example:

```python
provider = CredentialProvider(settings)

credentials = provider.get_remedy_credentials()
```

Services and clients do not need to know where credentials originate.

Credential sources can later be replaced with:

```text
Environment variables
SL1 credential vault
HashiCorp Vault
AWS Secrets Manager
Azure Key Vault
Custom secret providers
```

without modifying the Remedy client.

---

## Database Layer

### `database/connection.py`

Defines the database connection abstraction.

Database-specific connection behavior is isolated from repositories.

Repositories depend on the connection interface instead of creating database connections themselves.

---

### `database/factory.py`

Creates the configured database connection.

Example:

```python
connection = DatabaseFactory.create(settings)
```

The factory centralizes database connection creation.

This allows database implementations to change without modifying repositories.

---

## Repository Layer

Repositories are responsible only for data access.

Repositories must not contain workflow or ticketing business logic.

The repository structure is:

```text
BaseRepository
    │
    ├── DeviceRepository
    ├── InterfaceRepository
    ├── ComponentRepository
    ├── CertificateRepository
    └── EventRepository
```

---

### `repositories/base.py`

Base repository abstraction.

Provides shared database access behavior for repository implementations.

---

### `repositories/device_repository.py`

Retrieves SL1 device information.

Used by:

```text
DeviceService
```

Typical operations:

```text
Get device by ID
Retrieve device metadata
```

---

### `repositories/interface_repository.py`

Retrieves interface information.

Used by:

```text
InterfaceService
```

Typical operations:

```text
Get interface by ID
Get interfaces by device ID
```

---

### `repositories/component_repository.py`

Retrieves component information.

Used by:

```text
ComponentService
```

Typical operations:

```text
Get component by ID
Get components by device ID
```

---

### `repositories/certificate_repository.py`

Retrieves certificate information.

Used by:

```text
CertificateService
```

Typical operations:

```text
Get certificate by ID
Get certificates by device ID
```

---

### `repositories/event_repository.py`

Retrieves SL1 event information.

Used by:

```text
EventService
```

Typical operations:

```text
Get event by ID
Get active events by device ID
```

---

## Models

### `models/event.py`

Defines the normalized event model.

The Event model provides a structured representation of SL1 event data.

Instead of passing raw database rows through the application:

```text
Database Row
    ▼
Event Model
    ▼
Services
    ▼
Workflow
```

The model creates a stable boundary between the repository and service layers.

---

## Helper Layer

Helpers contain stateless reusable utility operations.

Helpers must not contain workflow or database logic.

---

### `helpers/string_helper.py`

Reusable string operations.

Typical responsibilities:

```text
String normalization
Whitespace cleanup
Safe conversion
Text formatting
```

---

### `helpers/datetime_helper.py`

Reusable datetime operations.

Typical responsibilities:

```text
Datetime parsing
Datetime formatting
Timezone normalization
Safe datetime conversion
```

---

### `helpers/message_parser.py`

Parses structured information from SL1 event messages.

This module isolates message parsing logic from services and workflows.

Example flow:

```text
SL1 Event Message
        │
        ▼
MessageParser
        │
        ▼
Structured Data
```

Parsing logic can evolve independently from ticket workflow logic.

---

### `helpers/payload_helper.py`

Provides reusable payload manipulation operations.

Available operations include:

```text
Remove None values
Remove empty values
Merge payloads
Convert payload to JSON
Parse JSON payload
Read nested values
Set nested values
```

Example:

```python
from slsdk.helpers.payload_helper import PayloadHelper

payload = PayloadHelper.merge(
    defaults,
    event_data,
    overrides,
)
```

Merge priority is:

```text
defaults
    ▼
event_data
    ▼
overrides
```

Later payloads overwrite earlier values.

---

## Service Layer

Services contain business operations.

Services depend on repositories or clients through dependency injection.

Services do not create their dependencies.

---

### `services/device_service.py`

Provides device-related operations.

Example:

```python
device = device_service.get_device(device_id)
```

Additional operations include:

```text
Get device name
Get device IP
Get device class
Get organization ID
Check device existence
```

---

### `services/interface_service.py`

Provides interface-related operations.

Available operations include:

```text
Get interface
Get interfaces by device
Get interface name
Get interface alias
Get interface IP
Check interface existence
```

---

### `services/component_service.py`

Provides component-related operations.

Available operations include:

```text
Get component
Get components by device
Get component name
Get component type
Get component device ID
Check component existence
```

---

### `services/certificate_service.py`

Provides certificate-related operations.

Available operations include:

```text
Get certificate
Get certificates by device
Get certificate name
Get certificate expiry
Get certificate issuer
Check certificate existence
```

---

### `services/event_service.py`

Provides event-related operations.

The service converts repository event data into the Event model.

Example:

```python
event = event_service.to_model(event_id)
```

Available operations include:

```text
Get event
Get active events by device
Get event message
Get event severity
Get event device ID
Convert event payload to Event model
Check event existence
```

---

### `services/enrichment_service.py`

Combines event data with related SL1 resource information.

Example flow:

```text
Event
  │
  ├── DeviceService
  ├── InterfaceService
  ├── ComponentService
  └── CertificateService
  │
  ▼
Enriched Event Data
```

Example enriched structure:

```json
{
    "event_id": 123456,
    "device_id": 1001,
    "message": "Example event",
    "device": {
        "device_name": "server01"
    },
    "interface": {
        "interface_name": "eth0"
    },
    "component": null,
    "certificate": null
}
```

The enrichment service does not know anything about Remedy.

This keeps SL1 data enrichment independent from external ticket systems.

---

### `services/payload_service.py`

Builds normalized outbound payloads.

Payload creation follows:

```text
Defaults
    │
    ▼
Event Data
    │
    ▼
Overrides
    │
    ▼
Remove None Values
    │
    ▼
Optional Empty Value Removal
    │
    ▼
Outbound Payload
```

Example:

```python
payload = payload_service.build(
    event_data,
    defaults={
        "source": "ScienceLogic",
    },
    overrides={
        "priority": "High",
    },
)
```

---

### `services/ticket_service.py`

Coordinates external ticket lifecycle operations.

Available operations:

```text
Create ticket
Get ticket
Update ticket
Close ticket
```

The ticket service depends on `BaseClient`.

It does not directly depend on Remedy.

Example:

```python
ticket_service = TicketService(client)
```

Any client implementing `BaseClient` can be used.

---

## Client Layer

The client layer handles external integrations.

---

### `clients/base.py`

Defines the external ticket client contract.

Required operations:

```python
create(payload)

get(resource_id)

update(resource_id, payload)

close(resource_id, payload)
```

External ticket integrations must implement this contract.

Example future integrations:

```text
RemedyClient
ServiceNowClient
JiraClient
CustomTicketClient
```

The ticket workflow does not need to change when the external ticket platform changes.

---

### `clients/remedy_client.py`

Implements Remedy HTTP API operations.

Responsibilities include:

```text
HTTP session management
Authentication
Request execution
Timeout handling
SSL verification
HTTP error handling
JSON response validation
```

Supported operations:

```text
POST   /tickets
GET    /tickets/{ticket_id}
PUT    /tickets/{ticket_id}
POST   /tickets/{ticket_id}/close
```

The exact Remedy endpoint paths can be adjusted based on the deployed Remedy API.

Authentication supports:

```text
Bearer token
Username and password
```

Example:

```python
client = RemedyClient(
    base_url=settings.remedy_base_url,
    credentials=credentials,
)
```

---

## Workflow Layer

### `workflows/event_ticket_workflow.py`

The workflow coordinates the complete event-to-ticket process.

The workflow contains orchestration logic only.

Execution:

```python
workflow.execute(event_id)
```

Internal flow:

```text
1. Retrieve Event
2. Convert Event to Model
3. Enrich Event
4. Build Payload
5. Create Ticket
6. Return Ticket Response
```

Workflow implementation:

```text
EventService
      │
      ▼
EnrichmentService
      │
      ▼
PayloadService
      │
      ▼
TicketService
```

The workflow does not directly access:

```text
Database
HTTP
Credentials
Environment variables
SL1 runtime internals
```

These responsibilities belong to dedicated layers.

---

## Bootstrap Layer

The bootstrap layer creates and connects dependencies.

---

### `bootstrap/container.py`

Acts as the dependency composition root.

The container builds:

```text
Database Connection
Repositories
Services
External Clients
Workflow
```

Dependency construction flow:

```text
Settings
   │
   ▼
DatabaseFactory
   │
   ▼
Repositories
   │
   ▼
Services
   │
   ▼
EnrichmentService
   │
   ▼
CredentialProvider
   │
   ▼
RemedyClient
   │
   ▼
TicketService
   │
   ▼
EventTicketWorkflow
```

The container is the only module responsible for connecting concrete implementations.

This prevents dependency construction from being distributed across the application.

---

### `bootstrap/application.py`

Provides the primary SDK application entry point.

Example:

```python
from slsdk import Application

application = Application()

result = application.run_event_ticket_workflow(
    event_id=123456,
)
```

Defaults can be provided:

```python
result = application.run_event_ticket_workflow(
    event_id=123456,
    defaults={
        "source": "ScienceLogic",
        "assignment_group": "Monitoring",
    },
)
```

Overrides can also be provided:

```python
result = application.run_event_ticket_workflow(
    event_id=123456,
    overrides={
        "priority": "Critical",
    },
)
```

---

## SDK Usage

The SDK exposes the primary application classes through:

```python
import slsdk
```

Available public objects:

```python
from slsdk import (
    Application,
    Event,
    ExecutionContext,
    Settings,
)
```

Example:

```python
from slsdk import Application

application = Application()

ticket = application.run_event_ticket_workflow(
    event_id=123456,
)

print(ticket)
```

---

## Custom Ticket Client

A custom ticket client can be implemented by extending `BaseClient`.

Example:

```python
from typing import Any, Mapping

from slsdk.clients.base import BaseClient


class CustomTicketClient(BaseClient):

    def create(
        self,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "ticket_id": "CUSTOM-1001",
        }

    def get(
        self,
        resource_id: str,
    ) -> dict[str, Any] | None:
        return {
            "ticket_id": resource_id,
        }

    def update(
        self,
        resource_id: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "ticket_id": resource_id,
            "updated": True,
        }

    def close(
        self,
        resource_id: str,
        payload: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "ticket_id": resource_id,
            "closed": True,
        }
```

The custom client can then be injected into `TicketService`.

```python
from slsdk.services.ticket_service import TicketService

client = CustomTicketClient()

ticket_service = TicketService(client)
```

---

## SOLID Design

### Single Responsibility Principle

Each module has one primary responsibility.

```text
Repository      → Data access
Service         → Business operation
Client          → External integration
Workflow        → Orchestration
Helper          → Stateless utility
Container       → Dependency composition
Application     → SDK entry point
```

---

### Open/Closed Principle

The SDK can be extended without modifying existing workflow logic.

Example:

```text
BaseClient
    │
    ├── RemedyClient
    ├── ServiceNowClient
    ├── JiraClient
    └── CustomClient
```

---

### Liskov Substitution Principle

Any implementation of `BaseClient` can replace `RemedyClient`.

`TicketService` operates against the client contract.

---

### Interface Segregation Principle

Modules depend only on focused interfaces and services.

Repositories expose data access operations.

Clients expose ticket lifecycle operations.

Services expose domain operations.

---

### Dependency Inversion Principle

High-level workflow modules depend on service abstractions and injected dependencies.

Example:

```text
EventTicketWorkflow
        │
        ▼
TicketService
        │
        ▼
BaseClient
        │
        ▼
RemedyClient
```

The workflow does not directly depend on the Remedy implementation.

---

## Logging

Executable and orchestration modules include meaningful logging.

Logging covers:

```text
Application startup
Workflow startup
Repository-driven service operations
Event enrichment
Payload construction
Ticket creation
Ticket update
Ticket closure
HTTP failures
Workflow failures
Application failures
```

Example log flow:

```text
Starting SLSDK execution
Starting SLSDK application
Starting event ticket workflow
Fetching event
Event found
Starting event enrichment
Fetching device
Event enrichment completed
Building outbound payload
Outbound payload built
Creating ticket
Creating Remedy ticket
Remedy ticket created
Ticket creation completed
Event ticket workflow completed
SLSDK application execution completed
SLSDK execution completed successfully
```

Sensitive credential values must never be logged.

---

## Error Handling

SDK-level errors derive from:

```python
SLSDKError
```

External integration errors can define specialized exceptions.

Example:

```python
RemedyClientError
```

HTTP failures are converted into client-specific SDK exceptions.

The application entry point logs unhandled execution failures and returns a non-zero exit status.

---

## Testing Strategy

The architecture allows individual layers to be tested independently.

Example workflow test:

```python
workflow = EventTicketWorkflow(
    event_service=fake_event_service,
    enrichment_service=fake_enrichment_service,
    payload_service=fake_payload_service,
    ticket_service=fake_ticket_service,
)

result = workflow.execute(123456)
```

No real database or Remedy API is required.

Repositories can be tested against database fixtures.

Services can be tested using fake repositories.

Clients can be tested using mocked HTTP sessions.

Workflows can be tested using fake services.

---

## Extension Strategy

New SL1 resource enrichment can be added using:

```text
Repository
    ▼
Service
    ▼
EnrichmentService
```

Example:

```text
OrganizationRepository
    ▼
OrganizationService
    ▼
EnrichmentService
```

New ticket systems can be added using:

```text
BaseClient
    ▼
New Client Implementation
    ▼
TicketService
```

New workflows can reuse existing services.

Example:

```text
EventUpdateWorkflow
EventCloseWorkflow
EventCorrelationWorkflow
CertificateTicketWorkflow
InterfaceTicketWorkflow
```

---

## Design Goal

The SDK is designed around one primary principle:

```text
ScienceLogic data retrieval,
business logic,
ticket integration,
and workflow orchestration
must remain independent.
```

This allows each part of the automation to evolve independently while keeping the complete system reusable, testable, and maintainable.
