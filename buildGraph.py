import json
import requests
import time


FLOODLIGHT_PORT = 8080
FLOODlIGHT_BASE_URL = 'http://localhost:' + str(FLOODLIGHT_PORT) + '/wm/'


CONTROLLER_ID = 'controller'



def querySwitches():
    switchListRequest = requests.get(FLOODlIGHT_BASE_URL + 'core/controller/switches/json')
    if switchListRequest.status_code == 200:
        switches = switchListRequest.json()
        switchList = [switch['dpid'] for switch in switches]
        buildSwitchesJSON(switchList)
        return 1
    else:
        print('Error making GET request')
        print(switchListRequest.text)
        return -1

def buildSwitchesJSON(switchList):
    outputGraph = {
        'nodes': [],
        'edges': []
    }
    controllerNode = {'data' : {'id' : CONTROLLER_ID, 'name': 'Controller'}, 'classes': "controller"}
    outputGraph['nodes'].append(controllerNode)

    # build in switches with connections to controller
    for switch in switchList:
        # assuming up to 10 dpid's for now
        switchID = 'switch_' + switch[-2:]
        switchName = 'Switch ' + switch[-2:]
        # append node
        node = {'data' : {'id' : switchID, 'name' : switchName}, 'classes': 'switch'}
        outputGraph['nodes'].append(node)

        # append edge
        edge = {'data': { 'id': CONTROLLER_ID + '_to_' + switchID, 'weight': 1, 'source': CONTROLLER_ID, 'target': switchID}}
        outputGraph['edges'].append(edge)

    # add in some default positions for the layout code to work
    for node in outputGraph['nodes']:
        node['position'] = {'x': 1, 'y': 1}

    # publish to file
    with open('networkGraph.json', 'w') as f:
        json.dump(outputGraph, f)


def queryStats():
    statsRequest = requests.get(FLOODlIGHT_BASE_URL + 'core/switch/all/aggregate/json')

    if statsRequest.status_code == 200:
        statMap = statsRequest.json()
        buildStatsJSON(statMap)
    else:
        print('Error making GET request')
        print(statsRequest.text)


def buildStatsJSON(statMap):
    outputObject = {}

    for switch in statMap:
        packetCount = statMap[switch][0]['packetCount']
        byteCount = statMap[switch][0]['byteCount']
        flowCount = statMap[switch][0]['flowCount']
        switchID = 'switch_' + switch[-2:]

        # ouptut node with stats
        node = {'data' : 
                    {'id' : switchID, 
                    'packetCount' : packetCount, 
                    'byteCount' : byteCount, 
                    'flowCount' : flowCount}}
        outputObject[switchID] = node

    # publish to file
    with open('networkStats.json', 'w') as f:
        json.dump(outputObject, f)


def queryHostsAndLinks():
    devicesRequest = requests.get(FLOODlIGHT_BASE_URL + 'device/')
    linksRequest = requests.get(FLOODlIGHT_BASE_URL + 'topology/links/json')

    if (devicesRequest.status_code == 200) and (linksRequest.status_code == 200):
        deviceData = devicesRequest.json()
        linkData = linksRequest.json()
        buildHostsAndLinksJSON(deviceData, linkData)
    else:
        print('Error making GET request')
        print(devicesRequest.text)
        print(linksRequest.text)

def buildHostsAndLinksJSON(deviceData, linkData):
    outputGraph = {
        'nodes': [],
        'edges': []
    }
    # hosts
    for device in deviceData:
        # assume that a recorded device with an IPv4 is a host (weak but need to get around fake hosts in TopoGuard+)
        if len(device['ipv4']) > 0:
            ipAddr = device['ipv4'][0]
            hostID = 'host_' + ipAddr
            macAddr = device['mac']
            if 'attachmentPoint' not in device:
                print('Attachment point not recorded for device ' + ipAddr)
                return
            attachedSwitch = device['attachmentPoint'][0]['switchDPID'][-2:]
            attachedSwitchID = 'switch_' + attachedSwitch
            attachedSwitchPort = device['attachmentPoint'][0]['port']

            # output host as a node with these fields
            # append node
            node = {'data' : 
                        {'id' : hostID, 
                        'name' : ipAddr}, 
                    'classes': 'host'}
            outputGraph['nodes'].append(node)

            # append edge from host to attached switch 
            edge = {'data': 
                        {'id': attachedSwitchID + '_to_' + hostID, 
                         'weight': 1,
                         'source': attachedSwitchID, 
                         'target': hostID,
                         'sourceSwitchPort': attachedSwitchPort},
                    'classes': 'host-switch-link'}
            outputGraph['edges'].append(edge)

    # add in some default positions for the layout code to work
    for node in outputGraph['nodes']:
        node['position'] = {'x': 1, 'y': 1}

    # inter-switch links
    for link in linkData:
        sourceSwitchID = 'switch_' + link['src-switch'][-2:]
        destSwitchID = 'switch_' + link['dst-switch'][-2:]
        sourceSwitchPort = link['src-port']
        destSwitchPort = link['dst-port']

        # append edge from switch to other switch 
        edge = {'data': 
                    {'id': sourceSwitchID + '_to_' + destSwitchID, 
                        'weight': 1,
                        'source': sourceSwitchID, 
                        'target': destSwitchID,
                        'sourceSwitchPort': sourceSwitchPort,
                        'destSwitchPort': destSwitchPort},
                'classes': 'switch-switch-link'}
        outputGraph['edges'].append(edge)

    # publish to file
    with open('networkHostsAndLinks.json', 'w') as f:
        json.dump(outputGraph, f)



res = querySwitches()
if res == -1:
    sys.exit()


queryStats()


queryHostsAndLinks()

# counter = 0
# while counter < 50:
#     print('Querying REST API. Count #' + str(counter))
#     queryStats()
#     time.sleep(1)
#     counter += 1



# time.sleep(2)
