from slsdk.services.ticket_service import TicketService
from tests.fakes.fake_ticket_client import FakeTicketClient


def main() -> None:
    client = FakeTicketClient()
    ticket_service = TicketService(client)

    dummy_payload = {
        "event_id": 123456,
        "device_id": 1001,
        "device_name": "dummy-server-01",
        "ip_address": "192.168.1.100",
        "severity": "CRITICAL",
        "message": "CPU utilization exceeded 95%",
        "source": "ScienceLogic",
        "assignment_group": "Monitoring Team",
    }

    ticket = ticket_service.create_ticket(
        dummy_payload,
    )

    print("Ticket response:")
    print(ticket)


if __name__ == "__main__":
    main()