# Imports

# Time
from datetime import datetime

# Netconf Client
from ncclient import manager

# JSON
import json

# Configuration
with open("./config/config.json") as data:
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
        device_params={'name': 'junos'},
        hostkey_verify=False  # Disables verify over SSL
    )


# Get interfaces and status from Netconf
# Based on https://github.com/ncclient/ncclient/blob/master/examples/juniper/get-interface-status.py
def get_interface_statuses(connection):
    rpc = "<get-interface-information><terse/></get-interface-information>"
    response = connection.rpc(rpc)
    interface_name = response.xpath('//physical-interface/name')
    interface_status = response.xpath('//physical-interface/oper-status')

    result = []

    for name, status in zip(interface_name, interface_status):
        result.append([name.text.split('\n')[1], status.text.split('\n')[1]])

    return result


# Execute command
def send_netconf_command(connection, command):
    with connection.locked("candidate") as m:
        m.load_configuration(
            action='set',
            config=command
        )

        m.commit()


# Run program
print("Loading..")
print("Connecting..")

connection = connect(serverCfg)
interface_statuses = get_interface_statuses(connection)

print("Connected..")

for interface_name, interface_status in interface_statuses:
    print("Interface %s: %s" % (interface_name, interface_status))

send_netconf_command(connection, "set interfaces LAST FETCH: %s" % int(datetime.now().timestamp()))
