Imports

Global configuration
EM7_VALUES
stats
dbc
logger

Payload functions
    build_create_payload
    build_update_payload

Scenario functions
    handle_availability_scenario
    handle_cdb_scenario
    handle_interface_scenario
    handle_sql_database_scenario
    handle_sql_instance_scenario
    handle_sql_server_scenario
    handle_mysql_scenario
    handle_cluster_scenario
    handle_ssl_certificate_scenario
    handle_vesta_forward_trap
    handle_vesta_msci_trap
    handle_ilo_scenario
    handle_oob_scenario
    handle_netapp_scenario
    handle_rackarmor_scenario
    handle_vmax_scenario
    handle_qradar_scenario
    scenarios_handling

Service functions
    get_credential
    get_credential_details
    call_sl_api
    call_remedy_web_service
    create_remedy_ticket
    update_remedy_ticket

Ticket response functions
    build_incident_event_data
    build_non_ticketable_response_data
    build_incident_app_failure_data
    build_event_data_from_remedy_response
    update_sl1_event
    handle_remedy_create_response

Ticket functions
    handle_create_ticket
    handle_update_ticket
    ticket_handling

Exception/retry functions
    get_error_marker
    get_error_retry_number
    get_error_timestamp
    is_retry_interval_reached
    build_error_marker
    build_first_error_user_note
    replace_error_marker
    update_retry_user_note
    register_first_ticket_failure
    record_retry_waiting
    retry_ticket_handling
    move_to_next_error_level
    build_final_failure_event_data
    build_final_failure_alert
    send_final_failure_alert
    handle_final_ticket_failure
    handle_existing_retry_failure
    exception_handling

Execution functions
    log_runbook_variables
    get_event_message
    is_event_message_blank
    handle_blank_event_message
    get_current_event_ticket_details
    run_ticket_process
    is_ticket_process_successful
    get_ticket_process_error
    handle_ticket_process_failure
    update_final_stats
    log_stats
    handle_main_failure
    process_event
    main

main()