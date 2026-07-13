## Importing The Required Modules. ##
import requests
import json
import time
import datetime
import pytz
import base64
import re
import subprocess
import ssl
import logging
import string
import html

from silo.apps.sl1_data_model import get_cred_array_from_id
from silo.apps.storage import dbc_cursor

from suds.client import Client

new_log_file_name = log_file_name
if str(EM7_VALUES['%n']).split(":")[2] not in ["NewTicket","ImmediateTicket"]:
    new_log_file_name = '/data/logs/SLRemedyIntegration/v1/ProdRemedy/UpdateTicket.log'    

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
log_formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(lineno)s,%(message)s')
log_file_handler = logging.FileHandler(new_log_file_name)
log_file_handler.setFormatter(log_formatter)
logger.addHandler(log_file_handler)

event_id = EM7_VALUES['%e']
event_message = EM7_VALUES['%M']
event_policy = str(EM7_VALUES['%_event_policy_name'])
device_ID = EM7_VALUES['%x']
ext_ticket_ref = str(EM7_VALUES['%_ext_ticket_ref'])
user_note = str(EM7_VALUES['%_user_note'])
dbc = dbc_cursor(legacy=True)
ticket_status = False
retry_interval = 0

non_ascii_event_message = set(string.printable)

stats = {"EID":str(event_id),
         "Device_ID":str(EM7_VALUES['%x']),
         "Device_Name":str(EM7_VALUES['%X']),
         "date_first":str(EM7_VALUES['%D']),
         "date_last":str(EM7_VALUES['%d']),
         "date_del":str(EM7_VALUES['%5']),
         "ext_ticket_ref":"",
         "AST":str(datetime.datetime.now()),
         "AET":"",
         "TRQT":"",
         "TRRT":""}

class get_remedy_payload:
    def create_ticket(self):
        #logger.info("[EID:"+ event_id+"]: Entered Create ticket payload")
        ## Payload from SL to Remedy for Create ticket action ##
        event_details={}
        #event_details["ext_ticket_ref"] = str(EM7_VALUES['%_ext_ticket_ref'])
        event_details["resource_name"] = str(EM7_VALUES['%X'])
        event_details["subresource_name"] = str(EM7_VALUES['%Y'])
        event_details["date_last"] = datetime.datetime.strftime(pytz.timezone("UTC").localize(datetime.datetime.strptime(str(EM7_VALUES['%d']), "%Y-%m-%d %H:%M:%S")).astimezone(pytz.timezone("America/New_York")), "%m/%d/%Y %I:%M:%S %p")
        event_details["severity"] = str(EM7_VALUES['%s'])
        event_details["date_first"] = datetime.datetime.strftime(pytz.timezone("UTC").localize(datetime.datetime.strptime(str(EM7_VALUES['%D']), "%Y-%m-%d %H:%M:%S")).astimezone(pytz.timezone("America/New_York")), "%m/%d/%Y %I:%M:%S %p")
        event_details["device_ip"] = str(EM7_VALUES['%a'])
        event_details["device_name"] = str(EM7_VALUES['%X'])
        event_details["device_class"] = str(EM7_VALUES['%W'])
        event_details["device_subclass"] = str(EM7_VALUES['%_class_name'])
        event_details["device_id"] = str(EM7_VALUES['%x'])
        event_details["counter"] = str(EM7_VALUES['%c'])
        event_details["EID"] = str(int(event_id)*(-1))
        event_details["user_notes"] = str(EM7_VALUES['%_user_note'])
        pc_resolution = str(EM7_VALUES['%R'])
        if pc_resolution:
            pc_resolution = ''.join((filter(lambda x: x in non_ascii_event_message, str(pc_resolution))))
            pc_resolution = (html.unescape(re.sub(r'<[^>]*>', '', (re.sub(r'<(br|p|BR|P|H|h|div|DIV|LI|li)\s*[^>]*>', '\n', pc_resolution))))).strip()
            if len(pc_resolution) > 4096:
                pc_resolution = pc_resolution[0:4096]
            event_details["user_notes"] = str(EM7_VALUES['%_user_note']) + pc_resolution
        event_details["source"] = str(EM7_VALUES['%z'])
        event_details["org_id"] = str(EM7_VALUES['%o'])
        event_details["org_name"] = str(EM7_VALUES['%O'])
        event_details["message"] = ''.join(filter(lambda x: x in non_ascii_event_message, str(EM7_VALUES['%M'])))
        event_details["evt_policy_name"] = str(EM7_VALUES['%_event_policy_name'])
        event_details["evt_policy_id"] = str(EM7_VALUES['%3'])
        event_details["evt_policy_severity"] = str(EM7_VALUES['%s'])
        event_details["user_del"] = str(EM7_VALUES['%4'])
        event_details["date_active"] = datetime.datetime.strftime(pytz.timezone("UTC").localize(datetime.datetime.strptime(str(EM7_VALUES['%6']), "%Y-%m-%d %H:%M:%S")).astimezone(pytz.timezone("America/New_York")), "%m/%d/%Y %I:%M:%S %p")
        event_details["msg_val"] = ""
        try:
            event_details["threshold"] = int(float(EM7_VALUES['%T']))
        except (ValueError, TypeError):
            event_details["threshold"] = 0
        event_details["label"] = str(EM7_VALUES['%Y'])
        event_details["device_parent"] = str(EM7_VALUES['%_parent_name'])
        event_details["device_child"] = ""
        event_details["correlation_reason"] = ""
        event_details["org_city"] = ""
        event_details["org_state"] = ""
        event_details["org_address"] = ""
        event_details["date_del"]= ""
        event_details["date_ack"] = ""
        event_details["user_ack"] = ""
        event_details["vendor_name"] = ""
        event_details["vendor_case_id"] = ""
        AutomationDetails=str(EM7_VALUES['%n']).split(":")
        event_details["application_type"] = str(AutomationDetails[3].strip())
        logger.info("[EID:"+ event_id+"]: Default payload to create a ticket in remedy" + str(event_details))
        return event_details
    def update_ticket(self):
        ## Payload from SL to Remedy for Update ticket action ##
        updated_event_details={}
        updated_event_details['EID']=event_id
        if int(event_id) >= 12632565:
            updated_event_details['EID']=str(int(event_id) *(-1))
        updated_event_details['severity']=str(EM7_VALUES['%s'])
        updated_event_details['message']=''.join(filter(lambda x: x in non_ascii_event_message, str(EM7_VALUES['%M'])))
        updated_event_details['date_last']= datetime.datetime.strftime(pytz.timezone("UTC").localize(datetime.datetime.strptime(str(EM7_VALUES['%d']), "%Y-%m-%d %H:%M:%S")).astimezone(pytz.timezone("America/New_York")), "%m/%d/%Y %I:%M:%S %p")
        updated_event_details["date_del"]= " "
        updated_event_details['date_active']= datetime.datetime.strftime(pytz.timezone("UTC").localize(datetime.datetime.strptime(str(EM7_VALUES['%6']), "%Y-%m-%d %H:%M:%S")).astimezone(pytz.timezone("America/New_York")), "%m/%d/%Y %I:%M:%S %p")
        updated_event_details['date_ack']= " "
        updated_event_details['correlation_reason']= " "
        updated_event_details['user_ack']= "svc_remedy"
        updated_event_details['user_del']= str(EM7_VALUES['%4'])
        updated_event_details['user_notes'] = " "
        updated_event_details['counter']= str(EM7_VALUES['%c'])
        updated_event_details['msg_val']= str(EM7_VALUES['%V'])
        if "ClearTicket" in str(EM7_VALUES['%n']):
            if "INC" in str(EM7_VALUES['%_ext_ticket_ref']) and ("Resolved" not in str(EM7_VALUES['%_user_note']) and "Closed" not in str(EM7_VALUES['%_user_note'])):
                updated_event_details['severity'] = 0
                logger.info("[EDI:" + str(event_id) +"]: Event payload to update an incident in remedy for cleared event in SL" + str(updated_event_details))       
                return updated_event_details
        else:    
            logger.info("[EID:" + event_id + "]: Checking if the event updated in last:"+str(modification_interval) + "sec. Event date_last:" + str(EM7_VALUES['%d']))
            TimeDiff = int(time.time()) - int(modification_interval)
            logger.info("[EID:" + event_id + "]: " + str(time.mktime(time.strptime(str(EM7_VALUES['%d']),'%Y-%m-%d %H:%M:%S'))))
            if int(time.mktime(time.strptime(str(EM7_VALUES['%d']),'%Y-%m-%d %H:%M:%S'))) > int(TimeDiff):
                logger.info("[EID:" + event_id + "]: time diff is : " + str(TimeDiff))
                if "INC" in str(EM7_VALUES['%_ext_ticket_ref']):
                    logger.info("[EID:" + event_id + "]: Found the incident number:"+ str(EM7_VALUES['%_ext_ticket_ref']))
                    logger.info("[EDI:" + str(event_id) +"]: Event payload to update an incident in remedy" + str(updated_event_details))       
                    return updated_event_details
                else:
                    logger.info("[EID:" + event_id + "]:No incident number exists" + str(str(EM7_VALUES['%_ext_ticket_ref'])))
                    return False
            else:
                logger.info("[EID:" + event_id + "]: Event did not updated in last :"+str(modification_interval) + "sec. Event date_last:" + str(EM7_VALUES['%d']))
                return False

def scenarios_handling(event_details):
    try:
        logger.info("[EID:" + event_id + "]: Entered into the scenarios loop")

        #### Device Availability and Latency Events Handling ####
        if int(EM7_VALUES['%3']) == int(availability_ep_id):
            logger.info("[EID:" + event_id + "]: Device Availability and Latency Events Handling.....")
            check_availability_latency_alert_sql = 'SELECT ea.id FROM master_events.events_active ea WHERE ea.etype = ' + str(availability_latency_ep_id) +' AND ea.Xid = '+str(EM7_VALUES['%x'])
            if int(dbc.execute(check_availability_latency_alert_sql)) == 1:
                logger.info("[EID:" + event_id + "]: There is Device Availability and Latency Event on this Device. Ignoring ticketing for this event by  Acknowledging it with svc_nonticketable user.")
                data = {'user_ack': str(ack_user_non_tktable_alert)}
                stats['ext_ticket_ref'] = "Availability-NonTickable"
                Update_Event_SQL = "update master_events.events_active ea set user_ack =" + str(ack_user_non_tktable_alert) +" where ea.id = " + str(event_id) + ";"
                logger.info("[EID:" + event_id + "]: Update Event SQL query is " + str(Update_Event_SQL))
                Response = dbc.execute(Update_Event_SQL)
                if str(Response) == "1":
                    logger.info("[EID:" + event_id + "]: Successfully acknowledged event with svc_nonticketable user.")
                else:
                    logger.error("[EID:" + event_id + "]: Failed to acknowledge event with svc_nonticketable user")
                    logger.error("[EID:" + event_id + "]: " + str(Response))
                return False   
            else:
                event_details =  event_details

        #### Ticketing redirected to SL CDB Events Handling #### 
        if str(EM7_VALUES['%3']) in ep_create_ticket_SLDB.strip('][').split(','):
            event_details["message"] = str(EM7_VALUES['%X'])+":"+str(event_details["message"])
            logger.info("[EID:" + event_id + "]: Ticketing redirected to SL CDB Events Handling......")
            if int(EM7_VALUES['%3']) == 7419:
                logger.info("[EID:" + event_id + "]: Collection objectes diabled events Handling......") 
                datefirst = datetime.datetime.strptime(str(EM7_VALUES['%D']), "%Y-%m-%d %H:%M:%S")
                logger.info("[EID:" + event_id + "]: " + str(datefirst))
                current_time = datetime.datetime.now()
                if datefirst <= current_time - datetime.timedelta(hours=72):
                    event_details["device_ip"] = str(cdb_device_ip)
                    event_details["resource_name"] = str(cdb_device_name)
                    event_details["device_name"] = str(cdb_device_name)
                    return event_details
                else:
                    logger.info("[EID:" + event_id + "]: The Event create date is " + str(datefirst) + " and it is not 72 hours old event.")  
                    return False
            else:
                event_details["device_ip"] = str(cdb_device_ip)
                event_details["resource_name"] = str(cdb_device_name)
                event_details["device_name"] = str(cdb_device_name)
                return event_details
        
        ### Interfaces Events Handling ###
        elif int(EM7_VALUES['%2']) == 7:
            logger.info("[EID:" + event_id + "]: Interfaces Events Handling.....")
            SubResourecName = False
            interfaceID = EM7_VALUES['%y']
            if str(interfaceID) == '0':
                tag_Id_SQL = "select if_id, name from master_dev.device_interfaces where name = '" + str(EM7_VALUES['%Y']).strip() + "' and did = " + str(EM7_VALUES['%x'])
                logger.info("[EID:" + event_id + "]: tag_id_SQLQuery: " + str(tag_Id_SQL))
                dbc.execute(tag_Id_SQL)
                Interface_Details = dbc.fetchall()
                logger.info("[EID:" + event_id +"]:" + str(Interface_Details))
                # logger.info("[EID:" + event_id +"]:" + str(type(Interface_Details)))
                interfaceID = Interface_Details[0][0]
                SubResourecName = True
                event_details["subresource_name"] = Interface_Details[0][1]
            logger.info("[EID:" + event_id + "]: Interface Event with ifId:" + str(interfaceID) + ", ifName:" + str(EM7_VALUES['%Y']) + ". Checking if interface has AUTO TICKET tag")
            tagSql = 'SELECT tag_name FROM master_dev.device_interface_tags_map ditm JOIN master_dev.device_interface_tags dit ON dit.tag_id = ditm.tag_id WHERE ditm.if_id = ' + str(interfaceID)
            dbc.execute(tagSql)
            tags_list = dbc.fetchall()
            tags_list = [tag for tags in tags_list for tag in tags]
            if "AUTO TICKET" in tags_list:
                logger.info("[EID:" + event_id + "]: AUTO TICKET tag found. Extracting interface name to send to Remedy")
                port_des_SQL = "select if_id, ifDescr from master_dev.device_interfaces where if_id = " + str(interfaceID)
                logger.info("[EID:" + event_id + "]: port_des_SQL: " + str(port_des_SQL))
                dbc.execute(port_des_SQL)
                Interface_Details = dbc.fetchall()
                logger.info("[EID:" + event_id +"]:" + str(Interface_Details))
                event_details["application_type"] = "NetworkPort"
                #event_details["resource_name"] = str(EM7_VALUES['%X']) + "." + str(EM7_VALUES['%Y'])
                #event_details["subresource_name"] = Interface_Details[0][1]
                if not SubResourecName:
                    event_details["subresource_name"] = Interface_Details[0][1]
                return event_details
            else:
                logger.info(
                    "[EID:" + event_id + "]: AUTO TICKET or NetName tags not found. Acknowledging the alert with svc_nonticketable user")
                data = {'user_ack': str(ack_user_non_tktable_alert)}
                stats['ext_ticket_ref'] = "Interface-NonTickable"
                Update_Event_SQL = "update master_events.events_active ea set user_ack =" + str(ack_user_non_tktable_alert) +" where ea.id = " + str(
                event_id) + ";"
                logger.info("[EID:" + event_id + "]: Update Event SQL query is " + str(Update_Event_SQL))
                Response = dbc.execute(Update_Event_SQL)
                if str(Response) == "1":
                    logger.info("[EID:" + event_id + "]: Successfully acknowledged event with svc_nonticketable user.")
                else:
                    logger.error("[EID:" + event_id + "]: Failed to acknowledge event with svc_nonticketable user")
                    logger.error("[EID:" + event_id + "]: " + str(Response))
                return False
        #### NICE Component Events Handling ####
        elif str(EM7_VALUES['%a']) == '' and str(EM7_VALUES['%O']) == 'Public Safety NICE Support':
            logger.info("[EID:" + event_id + "]: NICE Component Events Handling.......")
            device_ip_sql = 'SELECT ld.ip FROM master_dev.legend_device ld where ld.id = (SELECT cdm.root_did FROM master_dev.component_dev_map cdm WHERE cdm.component_did = {})'.format(EM7_VALUES['%x'])
            event_details["device_ip"] = dbc.autofetch_value(device_ip_sql)
            event_details["resource_name"] = str(EM7_VALUES['%_root_name'])
            event_details["device_name"] = str(EM7_VALUES['%_root_name'])
            event_details["application_type"] = "Device"
            return event_details
        #### PDCAD Component Events Handling ####
        elif str(EM7_VALUES['%a']) == '' and str(EM7_VALUES['%O']) == 'Public Safety PDCAD':
            logger.info("[EID:" + event_id + "]: PDCAD Component Events Handling.......")
            device_ip_sql = 'SELECT ld.ip FROM master_dev.legend_device ld where ld.id = (SELECT cdm.root_did FROM master_dev.component_dev_map cdm WHERE cdm.component_did = {})'.format(EM7_VALUES['%x'])
            event_details["device_ip"] = dbc.autofetch_value(device_ip_sql)
            event_details["resource_name"] = str(EM7_VALUES['%_root_name'])
            event_details["device_name"] = str(EM7_VALUES['%_root_name'])
            event_details["application_type"] = "Device"
            return event_details    
        elif "SQL Server Database" in str(EM7_VALUES['%_class_name']):
            logger.info("[EID:" + event_id + "]: SQL Event with Class: " + str(EM7_VALUES['%_class_name']) + " Device: " + str(EM7_VALUES['%X']) + " Parent: " + str(EM7_VALUES['%_parent_name'])+ str(EM7_VALUES['%_parent_id'])+ " Root: " + str(EM7_VALUES['%_root_name']))
            comp_id = EM7_VALUES['%x']
            comp_dn = dbc.autofetch_value("SELECT dn FROM master_dev.component_dev_map WHERE component_did={}".format(comp_id))
            logger.info("[EID:" + event_id + "]: Component_DN: "+ comp_dn)
            event_details["resource_name"] = str(EM7_VALUES['%_root_name'].split('.')[0])
            event_details["device_name"] = str(EM7_VALUES['%X'])
            event_details["subresource_name"] = str(EM7_VALUES['%_parent_name'])
            event_details["message"] = "DB_Name : " + str(EM7_VALUES['%X']) + " : " +event_details["message"]
            event_details["application_type"] = "DB_Database"
            if comp_dn:
                event_details["subresource_name"] = str(comp_dn.split("\\")[0]) + ":" + str(EM7_VALUES['%_parent_name'])
            return event_details
    
        elif "SQL Server Instance" in str(EM7_VALUES['%_class_name']):
            logger.info("[EID:" + event_id + "]: SQL Event with Class: " + str(EM7_VALUES['%_class_name']) + " Device: " + str(EM7_VALUES['%X']) + " Parent: " + str(EM7_VALUES['%_parent_name']) + " Root: " + str(EM7_VALUES['%_root_name']))
            comp_id = EM7_VALUES['%x']
            comp_dn = dbc.autofetch_value("SELECT dn FROM master_dev.component_dev_map WHERE component_did={}".format(comp_id))
            logger.info("[EID:" + event_id + "]: Component_DN: "+ str(comp_dn))
            event_details["resource_name"] = str(EM7_VALUES['%_root_name'].split('.')[0])
            event_details["device_name"] = str(EM7_VALUES['%X'])
            event_details["subresource_name"] = str(EM7_VALUES['%X'])
            if comp_dn:
                 event_details["subresource_name"] = str(comp_dn.split("\\")[0]) + ":" +str(EM7_VALUES['%X'])
            event_details["application_type"] = "DB_Instance"
            return event_details   

        elif "SQL Server" == str(EM7_VALUES['%_class_name']):
            logger.info("[EID:" + event_id + "]: SQL Event with Class: " + str(EM7_VALUES['%_class_name']) + " Device: " + str(EM7_VALUES['%X']) + " Parent: " + str(EM7_VALUES['%_parent_name']) + " Root: " + str(EM7_VALUES['%_root_name']))
            comp_id = EM7_VALUES['%x']
            comp_dn = ""
            InstanceName = ""
            logger.info("[EID:" + event_id + "]: No Instance name available in event information")
            SQLQueryToPullInstance_Comdn = "SELECT ld.device,cdm.dn FROM master_dev.component_dev_map cdm join master_dev.legend_device ld on ld.id = cdm.component_did WHERE cdm.parent_did = {}".format(comp_id)
            if dbc.execute(SQLQueryToPullInstance_Comdn) != 0:
                Instance_Comdn_res = dbc.fetchall()
                InstanceName = Instance_Comdn_res[0][0]
                comp_dn = Instance_Comdn_res[0][1]
                logger.info("[EID:" + event_id + "]: InstanceName: "+ str(InstanceName))
                logger.info("[EID:" + event_id + "]: Component_DN: "+ str(comp_dn))
            else:  
                InstanceName = event_details["device_name"]              
            
            event_details["resource_name"] = str(EM7_VALUES['%_root_name'].split('.')[0])
            event_details["device_name"] = InstanceName
            event_details["subresource_name"] = InstanceName
            if comp_dn:
                event_details["subresource_name"] = str(comp_dn.split("\\")[0]) + ":" + InstanceName
            event_details["application_type"] = "DB_Instance"
            return event_details
        ##### Mysql Componet events Handling ######
        elif str(EM7_VALUES['%_class_name']) in ["MySQL Server", "MySQL Instance"]:
            logger.info("[EID:" + event_id + "]: Mysql Componet events Handling.....")
            event_details["resource_name"] = str(EM7_VALUES['%_root_name'])
            event_details["device_name"] = str(EM7_VALUES['%_root_name'])
            return event_details
        #### Windows Cluster componets events Handling #####
        elif str(EM7_VALUES['%_class_name']) in ["Cluster Networks","Cluster Nodes","Cluster Roles and Services","Cluster Network","Cluster Node","Cluster Role / Service"]:
            logger.info("[EID:" + event_id + "]: Windows Cluster componets events Handling.......")
            event_details["resource_name"] = str(EM7_VALUES['%_root_name'])
            event_details["device_name"] = str(EM7_VALUES['%_root_name'])
            event_details["subresource_name"] = "0"
            event_details["application_type"] = "Cluster"
            return event_details
        #### F5 Load Balencer componet events Handling #####
        elif str(EM7_VALUES['%_class_name']) in ["BIG-IP Local Traffic Manager","BIG-IP LTM Virtual Server","BIG-IP LTM Pool","BIG-IP LTM Pool Member","BIG-IP LTM Node"]:
            logger.info("[EID:" + event_id + "]: F5 Load Balencer componet events Handling.....")
            device_ip_sql = 'SELECT ld.ip FROM master_dev.legend_device ld where ld.id = (SELECT cdm.root_did FROM master_dev.component_dev_map cdm WHERE cdm.component_did = {})'.format(EM7_VALUES['%x'])
            event_details["device_ip"] = dbc.autofetch_value(device_ip_sql)
            event_details["resource_name"] = str(EM7_VALUES['%_root_name'])
            event_details["device_name"] = str(EM7_VALUES['%_root_name'])
            return event_details
        #### SSL Certificate expiry Event Handling #####
        elif str(EM7_VALUES['%_event_policy_name']) == "SSL: Certificate has expired: AutoTicket":
            logger.info("[EID:" + event_id + "]: SSL Certificate expiry Event Handling......")
            certificate_info_sql = "SELECT certificate FROM master_dev.device_certificates dc WHERE dc.did = {}".format(device_ID)
            dbc.execute(certificate_info_sql)
            certificate_info = dbc.fetchall()
            new_ssl_event_message = event_details["message"] + " Certificate Information: "+str([certificate[0] for certificate in certificate_info])
            event_details["message"] = new_ssl_event_message
            return event_details
        #### Vesta ExternalActivityForwardTrap Handling ####
        elif "vstExternalActivityForwardTrap" in str(EM7_VALUES['%_event_policy_name']) and "ecpprb08" not in str(EM7_VALUES['%X']):
            logger.info("[EID:" + event_id + "]: Vesta ExternalActivityForwardTrap Handling......")
            case_number = str(event_details["message"].split(":")[0].split("#")[1])
            vesta_device_ip = str(event_details["message"].split("]")[0].strip("["))
            logger.info("[EventID:" + event_id+"]: Vesta ExternalActivityForwardTrap Handling Motorola Case Number: " + case_number)
            update_message = str(event_details["message"]).split("]")
            event_details["message"] = ("".join(update_message[1:])).strip(" ")
            event_details["vendor_case_id"] = case_number
            event_details["vendor_name"] = "Vesta Solutions"
            event_details["device_ip"] = vesta_device_ip
            logger.info("[EventID:" + event_id+"]: Vesta Payload: " + str(event_details))
            return event_details
        #### vstExternalActivityMSCITrap Handling #### 
        elif "vstExternalActivityMSCITrap" in str(EM7_VALUES['%_event_policy_name']):
            logger.info("[EID:" + event_id + "]: vstExternalActivityMSCITrap Handling.....")
            motorola_event_id = str(EM7_VALUES['%Y']).split(":")[0]
            vesta_device_ip = str(event_details["message"].split("]")[0].strip("["))
            logger.info("[EventID:" + event_id+"]: Vesta ExternalActivityMSCITrap Handling Motorola Event ID: " + motorola_event_id)
            #update_message = str(event_details["message"]).split("]", 1)
            event_details["vendor_case_id"] = motorola_event_id
            event_details["vendor_name"] = "MSCI Vesta Solutions"
            event_details["device_ip"] = vesta_device_ip
            #event_details["message"] = str(re.search(r'MSCI_EID.*', str(EM7_VALUES['%M'])).group())
            event_details["message"] = str(re.search(r'MSCI_EID.*', str(event_details["message"])).group())
            if "MSCI_TRAP_Source" in str(EM7_VALUES['%X']):
                #event_details["resource_name"] = vesta_device_ip
                #event_details["device_name"] = vesta_device_ip
                event_details["user_notes"]  = str(vesta_device_ip) + " - Asset doesn't exist in Public Safety ScienceLogic"
            logger.info("[EventID:" + event_id+"]: Vesta ExternalActivityMSCITrap Payload: " + str(event_details))
            return event_details
        #### SOS Webhook Events Handling #### 
        #elif "SFTY: SOS: Webhook" in str(EM7_VALUES['%_event_policy_name']) and "PSAC-EAS-SLWebhook" == str(EM7_VALUES['%X']):
        #    logger.info("[EID:" + event_id + "]: SOS Webhook Events Handling.....")
        #    EAS_device_Name = str(event_details["message"]).split(";")[0]
        #    event_details["user_notes"]  = str(EAS_device_Name) + " - Asset doesn't exist in Public Safety ScienceLogic"
        #    logger.info("[EventID:" + event_id+"]: SOS WebHook Payload: " + str(event_details))
        #    return event_details
        #### ILO Events Handling ####
        elif "-ILO." in str(EM7_VALUES['%X']) or "-ilo." in str(EM7_VALUES['%X']) or "-iLO." in str(EM7_VALUES['%X']) :
            logger.info("[EID:" + event_id + "]: ILO Events Handling.......")
            event_details["resource_name"] = str(EM7_VALUES['%X']).strip("-ILO.").strip("-ilo.").strip("-iLO.")
            event_details["device_name"] = str(EM7_VALUES['%X']).strip("-ILO.").strip("-ilo.").strip("-iLO.")
            return event_details 
        #### OOB Events Handling ####
        elif str(EM7_VALUES['%X']).startswith(("OOB","oob","Oob")) :
            logger.info("[EID:" + event_id + "]: OOB Events Handling......")
            event_details["resource_name"] = str(EM7_VALUES['%X']).lstrip("OOB").lstrip("oob").lstrip("Oob")
            event_details["device_name"] = str(EM7_VALUES['%X']).lstrip("OOB").lstrip("oob").lstrip("Oob")
            return event_details
        ###### NetApp Events Handling ######
        elif "NetApp" in str(EM7_VALUES['%_event_policy_name']) or "NetAPP" in str(EM7_VALUES['%_event_policy_name']):
            logger.info("[EID:" + event_id + "]: NetApp Events Handling......")
            if str(EM7_VALUES['%_root_name']) != '':
                device_ip_sql = 'SELECT ld.ip FROM master_dev.legend_device ld where ld.id = (SELECT cdm.root_did FROM master_dev.component_dev_map cdm WHERE cdm.component_did = {})'.format(EM7_VALUES['%x'])
                event_details["device_ip"] = dbc.autofetch_value(device_ip_sql)
                event_details["resource_name"] = str(EM7_VALUES['%_root_name'])
                event_details["device_name"] = str(EM7_VALUES['%_root_name'])
                event_details["subresource_name"] = str(EM7_VALUES['%X'])
                event_details["message"] = str(EM7_VALUES['%X']) + " : " +event_details["message"]
            event_details["application_type"] = "Cluster"
            return event_details
        #### RackArmor Camera Handling #### 
        elif "RackArmor" in str(EM7_VALUES['%_event_policy_name']):
            logger.info("[EID:" + event_id + "]: RackArmor Camera Handling......")
            event_details["device_ip"] = event_details["message"].split('(')[1].split(')')[0]
            event_details["resource_name"] = event_details["message"].split('(')[0].split('-')[1].strip()
            event_details["device_name"] = event_details["message"].split('(')[0].split('-')[1].strip()
            return event_details
        ### Dell Vmax Event Handling ###
        elif 'SFTY: Dell EMC: VMAX Unisphere' in EM7_VALUES['%_event_policy_name']: 
            logger.info("[EID:" + event_id + "]: Dell EMC Vmax events handling.....")
            device_ip_sql = 'SELECT ld.ip FROM master_dev.legend_device ld where ld.id = (SELECT cdm.root_did FROM master_dev.component_dev_map cdm WHERE cdm.component_did = {})'.format(EM7_VALUES['%x'])
            event_details["device_ip"] = dbc.autofetch_value(device_ip_sql)
            event_details["resource_name"] = str(EM7_VALUES['%_root_name'])
            event_details["device_name"] = str(EM7_VALUES['%_root_name'])
            event_details["message"] = str(EM7_VALUES['%X']) + " : " +str(EM7_VALUES['%_parent_name']) + " : " +event_details["message"]
            return event_details
        ### Qradar Event Handling ###
        elif "QRadar" in EM7_VALUES['%_event_policy_name']:
            logger.info("[EID:" + event_id + "]: QRadar Events Handling......")
            qr_magnitude_reg = re.search("QR_Offense_magnitude:(\w+)", str(event_details["message"]))
            qr_magnitude_val = int(qr_magnitude_reg.groups()[0])
            qr_severity_reg = re.search("QR_Offense_Severity:(\w+)", str(event_details["message"]))
            qr_severity_val = int(qr_severity_reg.groups()[0])
            logger.info("[EID:" + event_id + "]: QRadar Magnitude Value is " + str(qr_magnitude_val))
            if qr_magnitude_val > int(qradar_magnitude_ticketing_threshold):
                return event_details
            else:
                logger.info("[EID:" + event_id + "]: The Mignitude value of this offense is not matching with tickeitng criteria. Ignoring ticketing for this event by  Acknowledging it with svc_nonticketable user.")
                data = {'user_ack': str(ack_user_non_tktable_alert)}
                stats['ext_ticket_ref'] = "Qradar-NonTickable"
                Update_Event_SQL = "update master_events.events_active ea set user_ack =" + str(ack_user_non_tktable_alert) +" where ea.id = " + str(event_id) + ";"
                logger.info("[EID:" + event_id + "]: Update Event SQL query is " + str(Update_Event_SQL))
                Response = dbc.execute(Update_Event_SQL)
                if str(Response) == "1":
                    logger.info("[EID:" + event_id + "]: Successfully acknowledged event with svc_nonticketable user.")
                else:
                    logger.error("[EID:" + event_id + "]: Failed to acknowledge event with svc_nonticketable user")
                    logger.error("[EID:" + event_id + "]: " + str(Response))
                return False 
        else:
            return event_details
    except Exception as error:
        logger.error("[EventID:" + event_id+"]: " + str(error))
        EM7_RESULT = {"success": False,"is_response": "scenarios_handling function error {}".format(str(error)),}


def call_sl_api(end_point,data):
    try:
        ## SL Credentials from credential ID defined in Action ##
        sl_cred = get_cred_array_from_id(dbc,int(sl_db_credential_id))                        
        sl_url = sl_cred.get("curl_url")
        sl_username = sl_cred.get("cred_user")
        sl_password = sl_cred.get("cred_pwd")
    
        ## calling SL API services ##
        sl_api_url = sl_url + "/api/" + end_point
        sl_api_response=requests.post(sl_api_url,
                                data=json.dumps(data),
                                headers={"Content-Type": "application/json"},
                                auth=(sl_username,sl_password),
                                verify=False)
        return sl_api_response
    except Exception as error:
        logger.error("[EventID:" + event_id+"]: " + str(error))
        EM7_RESULT = {"success": False,"is_response": "call_sl_api function error {}".format(str(error)),}

def call_remedy_web_service():
    try:   
        ## Remedy Credentials from credential ID defined in action ##
        remedy_cred = get_cred_array_from_id(dbc,int(remedy_create_update_ticket_webservice_credential_id))
        logger.info("[EID:"+ event_id+"]: " + str(remedy_cred))
        remedy_ticket_url = remedy_cred.get('curl_url')
        remedy_username = remedy_cred.get('cred_user')
        remedy_password = remedy_cred.get('cred_pwd')
        
        stats['TRRT']= str(datetime.datetime.now())
        
        ## Calling Remedy Ticket Web Service. ##
        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context  
        
        remedy_operations = Client(str(remedy_ticket_url), cache=None)
        remedy_auth = remedy_operations.factory.create("AuthenticationInfo")
        remedy_auth.userName = remedy_username
        remedy_auth.password = remedy_password
        remedy_operations.set_options(soapheaders=(remedy_auth))
        logger.info("[EID:"+ event_id+"]: " + str(remedy_operations))
        return remedy_operations        
    except Exception as error:
        logger.error("[EventID:" + event_id+"]: " + str(error))
        EM7_RESULT = {"success": False,"is_response": "call_remedy_web_service function error {}".format(str(error)),}
        
def ticket_handling(ticket_status):
    try:
        if str(EM7_VALUES['%n']).split(":")[2] in ["NewTicket","ImmediateTicket"]:
            #logger.info("[EventID:" + event_id+"]: Newticket loop")
            create_payload = scenarios_handling(payload.create_ticket())
            if create_payload != False:
                logger.info("[EventID:" + event_id+"] Create Ticket payload after scenarios check is : " + str(create_payload))
                remedy_create_res = call_remedy_web_service().service.Create_Operation(**create_payload)
                stats['TRRT']= str(datetime.datetime.now())
                stats['ext_ticket_ref'] = remedy_create_res.ext_ticket_ref
                logger.info("[EID:"+ event_id+"]: Response received from Remedy Webservice: " + str(remedy_create_res))
                stats['ext_ticket_ref'] = str(remedy_create_res.ext_ticket_ref)
                event_data = {}
                if "INC" == remedy_create_res.ext_ticket_ref[0:3]:
                    force_ticket_url = force_ticket_uri
                    event_ext_ticket_ref= str(remedy_create_res.ext_ticket_ref)
                    HDCaseStatus = "No_case_status"
                    Assigned_Group = "No_assigned_group"
                    if "HDCaseStatus" in str(remedy_create_res):
                        HDCaseStatus = str(remedy_create_res.HDCaseStatus)
                    if "Assigned_Group" in str(remedy_create_res):
                        Assigned_Group = str(remedy_create_res.Assigned_Group)
                    event_user_note="["+ HDCaseStatus+ ":" + Assigned_Group +":"+event_ext_ticket_ref+"]" 
                    #event_user_note="["+str(remedy_create_res.HDCaseStatus) + ":" + str(remedy_create_res.Assigned_Group)+":"+str(remedy_create_res.ext_ticket_ref)+"]"
                    #event_user_note="["+str(remedy_create_res.Assigned_Group)+"]"
                    #event_user_note=str(remedy_create_res.Assigned_Group)+"\n"+str(remedy_create_res.ext_ticket_ref)
                    #event_user_note="["+str(remedy_create_res.Assigned_Group)+":"+str(remedy_create_res.ext_ticket_ref)+"]"
                    event_force_ticket_uri= str(force_ticket_url) + str(remedy_create_res.ext_ticket_ref) + '''"'''
                    event_data = {'user_ack':"/api/account/"+ str(ack_user_tktable_alert),'ext_ticket_ref':event_ext_ticket_ref ,'user_note':event_user_note,'force_ticket_uri':event_force_ticket_uri}
                    #event_data = {'user_ack':"/api/account/"+ str(ack_user_tktable_alert),'ext_ticket_ref':event_ext_ticket_ref ,'user_note':event_user_note}   
                    logger.info("[EID:"+ event_id+"]: Updating event with following incident Data"+ str(event_data))
                
                elif remedy_create_res.ext_ticket_ref in ["AutoTicketing Disabled","Planned Outage"]:
                    event_data = {'user_ack':"/api/account/"+ str(ack_user_tktable_alert), 'ext_ticket_ref':remedy_create_res.ext_ticket_ref}
                    logger.info("[EID:"+ event_id+"]: Updating event with following incident data"+ str(event_data))
                
                elif remedy_create_res.ext_ticket_ref in ["Incident App Failure"]:
                    event_ext_ticket_ref= str(remedy_create_res.ext_ticket_ref)
                    HDCaseStatus = "No_case_status"
                    Assigned_Group = "No_assigned_group"
                    if remedy_create_res.HDCaseStatus:
                        HDCaseStatus = str(remedy_create_res.HDCaseStatus)
                    if remedy_create_res.Assigned_Group:
                        Assigned_Group = str(remedy_create_res.Assigned_Group)
                    event_user_note="["+ HDCaseStatus+ ":" + Assigned_Group +":"+event_ext_ticket_ref+"]"  
                    event_data = {'user_ack':"/api/account/"+ str(ack_user_tktable_alert), 'ext_ticket_ref':event_ext_ticket_ref,'user_note':event_user_note}
                    #event_data = {'user_ack':"/api/account/"+ str(ack_user_tktable_alert), 'ext_ticket_ref':remedy_create_res.ext_ticket_ref}
                    logger.info("[EID:"+ event_id+"]: Updating event with following incident data"+ str(event_data))
                    alert_data = {"force_ytype": "0", "force_yid": "0", "force_yname": "",
                                      "message": "Incident App Failure on EID:" + str(event_id) +" with original Severity: " +str(EM7_VALUES['%S']) , "value": "",
                                      "threshold": "", "message_time": "", "aligned_resource": "/api/device/" + str(cdb_device_id)}
                    sl_alert_res = call_sl_api("alert",alert_data)
                    if sl_alert_res.status_code == 201:
                        logger.info("[EID:" + event_id + "]:6-Failure event is inserted successfully")
                    else:
                        logger.info("[EID:" + event_id + "]:Failed to insert 6-Failure event")
            
                sl_update_res = call_sl_api("event/"+str(event_id),event_data)
                if sl_update_res.status_code == 200:
                    logger.info("[EID:" + event_id + "]: Incident with incident number: " + remedy_create_res.ext_ticket_ref + " created in Remedy and successfully updated to event in ScienceLogic, acknowledged with svc_remedy user")
                    ticket_status = True
                
            
                else:
                    logger.error("[EID:" + event_id + "]: Incident with incident number " + str(remedy_create_res.ext_ticket_ref) + " created in Remedy but, got an error while updating event in ScienceLogic")
                    logger.error("[EID:" + event_id + "]: " + str(sl_update_res.json()))    
                    ticket_status = False
            else:
                logger.info("[EID:" + event_id + "]: This event idenfified as non ticketable event after scenarios check, ignoring ticketing on this event.")
                ticket_status = True            
            
        else:    
            #logger.info("[EventID:" + event_id+"]: Update Ticket")
            update_payload = payload.update_ticket()
            #stats['ext_ticket_ref'] = str(EM7_VALUES['%_ext_ticket_ref'])
            #logger.info("[EventID:" + event_id+"]: " + str(update_payload))
            stats['ext_ticket_ref'] = str(EM7_VALUES['%_ext_ticket_ref'])
            if update_payload:
                remedy_update_res = call_remedy_web_service().service.Modify_Operation(**update_payload)
                stats['TRRT']= str(datetime.datetime.now())
                logger.info("[EID:"+ event_id+"]: Response received from Remedy Webservice: " + str(remedy_update_res))
                if len(remedy_update_res) != 0:
                    logger.info("[EID:" + event_id + "]: Ticket:"+str(EM7_VALUES['%_ext_ticket_ref'])+ "is updated successfully in remedy")
                    ticket_status = True
                else:
                    logger.error("[EID:" + event_id + "]: " + str(remedy_update_res))
                    ticket_status = False                        
            else:
                ticket_status = True        
        return {"ticket_status": ticket_status, "result": "Success"}
    except Exception as error:
        logger.error("[EventID:" + event_id+"]: " + str(error))
        return {"ticket_status": ticket_status, "result": error}
        #exception_handling(event_id, ext_ticket_ref, user_note, error, ticket_status)
        EM7_RESULT = {"success": False,"is_response": "ticket_handling function error {}".format(str(error)),}    

def exception_handling(event_id, ext_ticket_ref, user_note, error_msg, ticket_status):
    try:
        if "-Error" not in user_note:
            event_data = {'user_note': "[" + "1-Error:" + str(int(time.time())) + "] " + str(user_note)}
            logger.info("[EID:" + event_id + "]: Updating event with following data" + str(event_data))
            stats['ext_ticket_ref'] = "1-Error" + str(error_msg)
            sl_update_res = call_sl_api("event/"+str(event_id),event_data)
            if sl_update_res.status_code == 200:
                logger.info("[EID:" + event_id + "]: Failed to create ticket and user_note field is updated with " + str(event_data))
            else:
                logger.error("[EID:" + event_id + "]: " + str(sl_update_res))
                
        elif "1-Error" in user_note:
            matched_user_note = re.search(r'\d-Error:\d+', user_note).group()
            time_stamp = matched_user_note.split(":")[1]
            if int(time.time()) - int(float(time_stamp)) >= retry_interval:
                ticket_handling_res = ticket_handling(ticket_status)
                if not ticket_handling_res['ticket_status']:
                    UserNote = user_note.replace("[" + re.search(r'\d-Error:\d+', user_note).group() + "]",
                                             "[" + "2-Error:" + str(int(time.time())) + "]")
                    event_data = {'user_note': str(UserNote)}
                    stats['ext_ticket_ref'] = "2-Error " + str(error_msg)
                    logger.info("[EID:" + event_id + "]: Updating event with following data" + str(event_data))
                    sl_update_res = call_sl_api("event/"+str(event_id),event_data)
                    if sl_update_res.status_code == 200:
                        logger.info("[EID:" + event_id + "]: Failed to create ticket and user_note field is updated with " + str(event_data))
                    else:
                        logger.error("[EID:" + event_id + "]: " + str(sl_update_res))
            else:
                stats['ext_ticket_ref'] = "1-Error " + str(error_msg)
                logger.info("[EID:" + event_id + "]: Could not process for ticket creation as it does not reach the retry interval")
    
        elif "2-Error" in user_note:
            matched_user_note = re.search(r'\d-Error:\d+', user_note).group()
            time_stamp = matched_user_note.split(":")[1]
            if int(time.time()) - int(float(time_stamp)) >= retry_interval:
                ticket_handling_res = ticket_handling(ticket_status)
                if not ticket_handling_res['ticket_status']:
                    UserNote = user_note.replace("[" + re.search(r'\d-Error:\d+', user_note).group() + "]",
                                             "[" + "3-Error:" + str(int(time.time())) + "]")
                    event_data = {'user_note': str(UserNote)}
                    stats['ext_ticket_ref'] = "3-Error " + str(error_msg)
                    logger.info("[EID:" + event_id + "]: Updating event with following data" + str(event_data))
                    sl_update_res = call_sl_api("event/"+str(event_id),event_data)
                    if sl_update_res.status_code == 200:
                        logger.info("[EID:" + event_id + "]: Failed to create ticket and user_note field is updated with " + str(event_data))
                    else:
                        logger.error("[EID:" + event_id + "]: " + str(sl_update_res))
            else:
                stats['ext_ticket_ref'] = "2-Error " + str(error_msg)
                logger.info("[EID:" + event_id + "]: Could not process for ticket creation as it does not reach the retry interval")
   
        elif "3-Error" in user_note:
            matched_user_note = re.search(r'\d-Error:\d+', user_note).group()
            time_stamp = matched_user_note.split(":")[1]
            if int(time.time()) - int(float(time_stamp)) >= retry_interval:
                ticket_handling_res = ticket_handling(ticket_status)
                if not ticket_handling_res['ticket_status']:
                    UserNote = user_note.replace("[" + re.search(r'\d-Error:\d+', user_note).group() + "]",
                                             "[" + "4-Error:" + str(int(time.time())) + "]")
                    event_data = {'user_note': str(UserNote)}
                    stats['ext_ticket_ref'] = "4-Error " + str(error_msg)
                    logger.info("[EID:" + event_id + "]: Updating event with following data" + str(event_data))
                    sl_update_res = call_sl_api("event/"+str(event_id),event_data)
                    if sl_update_res.status_code == 200:
                        logger.info("[EID:" + event_id + "]: Failed to create ticket and user_note field is updated with " + str(event_data))
                    else:
                        logger.error("[EID:" + event_id + "]: " + str(sl_update_res))
            else:
                stats['ext_ticket_ref'] = "3-Error " + str(error_msg)
                logger.info("[EID:" + event_id + "]: Could not process for ticket creation as it does not reach the retry interval")

        elif "4-Error" in user_note:
            matched_user_note = re.search(r'\d-Error:\d+', user_note).group()
            time_stamp = matched_user_note.split(":")[1]
            if int(time.time()) - int(float(time_stamp)) >= retry_interval:
                ticket_handling_res = ticket_handling(ticket_status)
                if not ticket_handling_res['ticket_status']:
                    UserNote = user_note.replace("[" + re.search(r'\d-Error:\d+', user_note).group() + "]",
                                             "[" + "5-Error:" + str(int(time.time())) + "]")
                    event_data = {'user_note': str(UserNote)}
                    stats['ext_ticket_ref'] = "5-Error " + str(error_msg)
                    logger.info("[EID:" + event_id + "]: Updating event with following data" + str(event_data))
                    sl_update_res = call_sl_api("event/"+str(event_id),event_data)
                    if sl_update_res.status_code == 200:
                        logger.info("[EID:" + event_id + "]: Failed to create ticket and user_note field is updated with " + str(event_data))
                    else:
                        logger.error("[EID:" + event_id + "]: " + str(sl_update_res))
            else:
                stats['ext_ticket_ref'] = "4-Error " + str(error_msg)
                logger.info("[EID:" + event_id + "]: Could not process for ticket creation as it does not reach the retry interval")
          
        elif "5-Error" in user_note:
            matched_user_note = re.search(r'\d-Error:\d+', user_note).group()
            time_stamp = matched_user_note.split(":")[1]
            if int(time.time()) - int(float(time_stamp)) >= retry_interval:
                ticket_handling_res = ticket_handling(ticket_status)
                if not ticket_handling_res['ticket_status']:
                    #event_data = {'user_note': "6-Failure"}
                    event_data = {'user_ack':"/api/account/"+ str(ack_user_tktable_alert), 'user_note': "6-Failure"}
                    stats['ext_ticket_ref'] = "6-Failure " + str(error_msg)
                    logger.info("[EID:" + event_id + "]: Updating event with following data" + str(event_data))
                    sl_update_res = call_sl_api("event/"+str(event_id),event_data)
                    if sl_update_res.status_code == 200:
                        logger.info("[EID:" + event_id + "]: Failed to create ticket and user_note field is updated with " + str(event_data))
                        alert_data = {"force_ytype": "0", "force_yid": "0", "force_yname": "",
                                      "message": "Remedy Ticket Creation Failed: AutoTicket Creation Failed on EID:" + str(event_id) + "; ERROR:" + str(error_msg), "value": "",
                                      "threshold": "", "message_time": "", "aligned_resource": "/api/device/" + str(device_ID)}
                        sl_alert_res = call_sl_api("alert",alert_data)
                        if sl_alert_res.status_code == 201:
                            logger.info("[EID:" + event_id + "]:6-Failure event is inserted successfully")
                        else:
                            logger.info("[EID:" + event_id + "]:Failed to insert 6-Failure event")
            else:
                stats['ext_ticket_ref'] = "5-Error " + str(error_msg)
                logger.info("[EID:" + event_id + "]: Could not process for ticket creation as it does not reach the retry interval")          
                    
                
    except Exception as error:
        logger.error("[EventID:" + event_id+"]: " + str(error))
        EM7_RESULT = {"success": False,"is_response": "exception_handling function error {}".format(str(error)),}
        
try:
    logger.info("[EID:"+ event_id+"]: =======================================")
    logger.info("[EID:"+ event_id+"]: Started auto ticketing process with Python3.11.........")
    
    ## Run Book Variables data ##
    RBA_variables = {"event_id":  str(event_id),
             "Ext_ticket_ref": str(EM7_VALUES['%_ext_ticket_ref']),
             "Username": str(EM7_VALUES['%A']),
             "Automation action name": str(EM7_VALUES['%N']),
             "Asset serial": str(EM7_VALUES['%g']),
             "Device ID associated with the asset": str(EM7_VALUES['%h']),
             "Asset Location": str(EM7_VALUES['%i']),
             "Asset Room": str(EM7_VALUES['%k']),
             "Asset Floor": str(EM7_VALUES['%K']),
             "Asset plate": str(EM7_VALUES['%P']),
             "Asset panel": str(EM7_VALUES['%p']),
             "Asset zone": str(EM7_VALUES['%q']),
             "Asset punch": str(EM7_VALUES['%Q']),
             "Asset rack": str(EM7_VALUES['%U']),
             "Asset shelf": str(EM7_VALUES['%u']),
             "Asset tag": str(EM7_VALUES['%v']),
             "Asset model": str(EM7_VALUES['%w']),
             "Asset make": str(EM7_VALUES['%W']),
             "Automation policy note": str(EM7_VALUES['%m']),
             "Automation policy name": str(EM7_VALUES['%n']),
             "Alert ID for a Dynamic Application Alert": str(EM7_VALUES['%F']),
             "Identifier Pattern field in the event definition": str(EM7_VALUES['%I']),
             "Threshold function value in aDynamic Application Alert": str(EM7_VALUES['%T']),
             "Result function value in a Dynamic Application Alert": str(EM7_VALUES['%V']),
             "IP address": str(EM7_VALUES['%a']),
             "Device category": str(EM7_VALUES['%_category_id']),
             "Device category name":  str(EM7_VALUES['%_category_name']),
             "Device class ID": str(EM7_VALUES['%_class_id']),
             "Device class name": str(EM7_VALUES['%_class_name']),
             "parent deviceID": str(EM7_VALUES['%_parent_id']),
             "Parent name": str(EM7_VALUES['%_parent_name']),
             "ID of the root device": str(EM7_VALUES['%_root_id']),
             "Name of the root device":  str(EM7_VALUES['%_root_name']),
             "Entity type": str(EM7_VALUES['%1']),
             "Sub-entity type": str(EM7_VALUES['%2']),
             "user name that cleared the event": str(EM7_VALUES['%4']),
             "when event was deleted": str(EM7_VALUES['%5']),
             "event becoming active": str(EM7_VALUES['%6']),
             "Event severity": str(EM7_VALUES['%7']),
             "Event counter": str(EM7_VALUES['%c']),
             "last event occurrence": str(EM7_VALUES['%d']),
             "first event occurrence": str(EM7_VALUES['%D']),
             "URL link to event": str(EM7_VALUES['%H']),
             "Event message": str(EM7_VALUES['%M']),
             "severity_numeric": str(EM7_VALUES['%s']),
             "severity": str(EM7_VALUES['%S']),
             "userNote": str(EM7_VALUES['%_user_note']),
             "Entity ID": str(EM7_VALUES['%x']),
             "Entity name": str(EM7_VALUES['%X']),
             "Sub-entity ID": str(EM7_VALUES['%y']),
             "Sub-entity name": str(EM7_VALUES['%Y']),
             "Event source": str(EM7_VALUES['%Z']),
             "Event source_numeric": str(EM7_VALUES['%z']),
             "Event policy ID": str(EM7_VALUES['%3']),
             "External ID from event policy": str(EM7_VALUES['%E']),
             "stateful": str(EM7_VALUES['%f']),
             "Event_Category": str(EM7_VALUES['%G']),
             "Event_policy_cause_action_text" : str(EM7_VALUES['%R']),
             "event_policy" : str(EM7_VALUES['%_event_policy_name']),
             "org_billing_ID" : str(EM7_VALUES['%B']),
             "impacted_org" : str(EM7_VALUES['%b']),
             "Organization_CRM_ID" : str(EM7_VALUES['%C']),
             "Organization_ID" : str(EM7_VALUES['%o']),
             "Organization_name" : str(EM7_VALUES['%O']),
             "system" : str(EM7_VALUES['%r']),
             "Ticket" : str(EM7_VALUES['%7'])}
    logger.info("[EventID:" + event_id+"] RunBook Action Variables are: "+str(RBA_variables))
    payload = get_remedy_payload()
    logger.info("[EventID:" + event_id+"] Payload object is: " + str(payload))
    ticket_handling_res = ticket_handling(ticket_status)
    if str(EM7_VALUES['%M']) == "":
        alert_data = {"force_ytype": "0", "force_yid": "0", "force_yname": "",
                      "message": "Blank Event Message Check: EID: "+str(event_id)+";DeviceName: "+str(EM7_VALUES['%X'])+";EventPolicy: "+str(EM7_VALUES['%_event_policy_name']) , "value": "", "threshold": "", "message_time": "", "aligned_resource": "/api/device/" + str(cdb_device_id)}
        sl_alert_res = call_sl_api("alert",alert_data)
        if sl_alert_res.status_code == 201:
            logger.info("[EID:" + event_id + "]:Blank Event Message Notification inserted successfully")
        else:
            logger.info("[EID:" + event_id + "]:Failed to insert Blank Event Message Notification")
    if not ticket_handling_res['ticket_status']:
        exception_handling(event_id, ext_ticket_ref, user_note, ticket_handling_res['result'], ticket_status)
        
except Exception as error:
    logger.error("[EventID:" + event_id+"]: " + str(error))
    EM7_RESULT = {"success": False,"is_response": "Main function error {}".format(str(error)),}    

stats['AET']=str(datetime.datetime.now())

logger.info("[EID:" + event_id + "]: stats: " + stats['EID']+ "," +stats['Device_ID']+","+stats['Device_Name']+","+ stats['date_first'] + "," + stats['date_last'] + "," + stats['date_del'] + "," + stats['ext_ticket_ref'] + "," + stats['AST'] + "," + stats['AET'] + "," + stats['TRQT'] + "," + stats['TRRT'])     