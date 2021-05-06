# Imports

# Time
from datetime import datetime

# Netconf Client
from ncclient import manager

# JSON
import json

# XML
import xml.etree.ElementTree as ElementTree # This handles loading
import lxml.etree as ET # This version allowed for merging due to encode errors

# FILTERS
INTERFACE_FILTER = '''<interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"></interface-configurations>'''

# Configuration
with open("config/config.json") as data:
    config = json.load(data)
    serverCfg = config['server']

# Connect to Netconf
# Based on https://github.com/ncclient/ncclient/blob/master/examples/juniper/get-interface-status.py
def connect(cfg):
    return manager.connect(
        host=cfg['host'],
        port=cfg['port'],
        username=cfg['username'],
        password=cfg['password'],
        device_params={'name': cfg['type']},
        hostkey_verify=False
    )


# Get interfaces and status from Netconf
# Based on https://github.com/ncclient/ncclient/blob/master/examples/juniper/get-interface-status.py
def get_interface_statuses(connection):
    for interface in connection.get_config(source='running', filter=('subtree', INTERFACE_FILTER)).data[0]:
        print(ElementTree.tostring(interface))
        interface_name = interface[1].text
        interface_status = interface[0].text
        yield (interface_name, interface_status)


# Execute command
def set_interface_description(connection, interface_name, description):
    # Builds the configuration elements required to set description
    mergedConfig = ET.Element("config")
    configuration = ET.SubElement(mergedConfig, "interface-configurations", nsmap={None: 'http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg'})
    interface_cfg = ET.SubElement(configuration, "interface-configuration")
    ET.SubElement(interface_cfg, "active").text = 'act'
    ET.SubElement(interface_cfg, "interface-name").text = interface_name
    ET.SubElement(interface_cfg, "description").text = description

    with connection.locked("candidate"):
        connection.edit_config(mergedConfig, default_operation="merge")
        connection.commit()


# Run program
print(f"Connecting to {serverCfg['host']}:{serverCfg['port']} defined with type: {serverCfg['type']}.")

with connect(serverCfg) as connection:

    print("Connected..")

    for interface_name, interface_status in get_interface_statuses(connection):
        set_interface_description(connection, interface_name, "LAST FETCH: %s" % int(datetime.now().timestamp()))
        print("Interface %s: %s" % (interface_name, True if interface_status == 'act' else False))

print("Program has ended...")