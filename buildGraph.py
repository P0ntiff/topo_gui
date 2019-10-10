import json
import requests
import time
import sys



class GraphBuilder:
    def __init__(self):
        self.floodlightPort = 8080
        self.floodlightBaseURL = 'http://localhost:' + str(self.floodlightPort) + '/wm/'
        self.controllerID = 'controller'
        self.switchBaseID = 'switch_'

    def queryNetworkElements(self, ignoreController=False):
        switchListRequest = requests.get(self.floodlightBaseURL + 'core/controller/switches/json')
        if switchListRequest.status_code != 200:
            print('Error making GET request for switches')
            return -1
        switchData = switchListRequest.json()

        devicesRequest = requests.get(self.floodlightBaseURL + 'device/')
        linksRequest = requests.get(self.floodlightBaseURL + 'topology/links/json')
        if (devicesRequest.status_code != 200) or (linksRequest.status_code != 200):
            print('Error making GET requests for device and link data')
            return -1
        deviceData = devicesRequest.json()
        linkData = linksRequest.json()

        self.buildNetworkElementsJSON(switchData, deviceData, linkData, ignoreController)

    def buildNetworkElementsJSON(self, switchData, deviceData, linkData, ignoreController=False):
        outputGraph = {
            'nodes': [],
            'edges': []
        }

        outputGraph = self.parseSwitchData(switchData, outputGraph, ignoreController)
        outputGraph = self.parseDeviceAndLinkData(deviceData, linkData, outputGraph)

        # add in some default positions for the layout code to work
        for node in outputGraph['nodes']:
            node['position'] = {'x': 1, 'y': 1}

        # publish to file
        with open('networkElements.json', 'w') as f:
            json.dump(outputGraph, f)

    
    def parseSwitchData(self, switchData, outputGraph, ignoreController=False):
        if not ignoreController:
            controllerNode = {'data' : {'id' : self.controllerID, 'name': 'Controller'}, 'classes': "controller"}
            outputGraph['nodes'].append(controllerNode)
        # build in switches with connections to controller
        switchList = [switch['dpid'] for switch in switchData]
        for switch in switchList:
            # assuming up to 10 dpid's for now
            switchID = self.switchBaseID + switch[-2:]
            switchName = 'Switch ' + switch[-2:]
            # append node
            node = {'data' : {'id' : switchID, 'name' : switchName}, 'classes': 'switch'}
            outputGraph['nodes'].append(node)
            # append edge
            if not ignoreController:
                edge = {'data': { 'id': self.controllerID + '_to_' + switchID, 'weight': 1, 'source': self.controllerID, 'target': switchID}}
                outputGraph['edges'].append(edge)

        return outputGraph

    def parseDeviceAndLinkData(self, deviceData, linkData, outputGraph):
        # hosts
        for device in deviceData:
            # assume that a recorded device with an IPv4 is a host (weak but need to get around fake hosts in TopoGuard+)
            # only care about hosts that are currently attached (ignore ex hosts)
            if len(device['ipv4']) > 0 and len(device['attachmentPoint']) > 0:
                ipAddr = device['ipv4'][0]
                hostID = 'host_' + ipAddr
                macAddr = device['mac']
                attachedSwitch = device['attachmentPoint'][0]['switchDPID'][-2:]
                attachedSwitchID = self.switchBaseID + attachedSwitch
                attachedSwitchPort = device['attachmentPoint'][0]['port']
                # add host as a node with these fields
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

        # inter-switch links
        for link in linkData:
            sourceSwitchID = self.switchBaseID + link['src-switch'][-2:]
            destSwitchID = self.switchBaseID + link['dst-switch'][-2:]
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

        return outputGraph

    def queryStats(self):
        statsRequest = requests.get(self.floodlightBaseURL + 'core/switch/all/aggregate/json')
        if statsRequest.status_code != 200:
            print('Error making GET request for stats data')
        statMap = statsRequest.json()
        self.buildStatsJSON(statMap)

    def buildStatsJSON(self, statMap):
        outputObject = {}

        for switch in statMap:
            packetCount = statMap[switch][0]['packetCount']
            byteCount = statMap[switch][0]['byteCount']
            flowCount = statMap[switch][0]['flowCount']
            switchID = self.switchBaseID + switch[-2:]

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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: buildGraph.py <poll-time-in-seconds> [<ignore-controller>]{true|false}')
        sys.exit()
    pollTime = int(sys.argv[1])
    ignoreController = False
    if len(sys.argv) == 3:
        if sys.argv[2].lower() == 'true':
            ignoreController = True
    gb = GraphBuilder()
    res = gb.queryNetworkElements(ignoreController=ignoreController)
    if res == -1:
        print('Could not connect to REST API to get topology data')
        sys.exit()
    counter = 0
    while True:
        print('Querying REST API. Count #' + str(counter))
        gb.queryNetworkElements(ignoreController=ignoreController)
        gb.queryStats()
        time.sleep(pollTime)
        counter += 1

