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

    def querySwitches(self):
        switchListRequest = requests.get(self.floodlightBaseURL + 'core/controller/switches/json')
        if switchListRequest.status_code == 200:
            switches = switchListRequest.json()
            switchList = [switch['dpid'] for switch in switches]
            self.buildSwitchesJSON(switchList)
            return 1
        else:
            print('Error making GET request')
            print(switchListRequest.text)
            return -1

    def buildSwitchesJSON(self, switchList):
        outputGraph = {
            'nodes': [],
            'edges': []
        }
        controllerNode = {'data' : {'id' : self.controllerID, 'name': 'Controller'}, 'classes': "controller"}
        outputGraph['nodes'].append(controllerNode)

        # build in switches with connections to controller
        for switch in switchList:
            # assuming up to 10 dpid's for now
            switchID = self.switchBaseID + switch[-2:]
            switchName = 'Switch ' + switch[-2:]
            # append node
            node = {'data' : {'id' : switchID, 'name' : switchName}, 'classes': 'switch'}
            outputGraph['nodes'].append(node)

            # append edge
            edge = {'data': { 'id': self.controllerID + '_to_' + switchID, 'weight': 1, 'source': self.controllerID, 'target': switchID}}
            outputGraph['edges'].append(edge)

        # add in some default positions for the layout code to work
        for node in outputGraph['nodes']:
            node['position'] = {'x': 1, 'y': 1}

        # publish to file
        with open('networkGraph.json', 'w') as f:
            json.dump(outputGraph, f)


    def queryStats(self):
        statsRequest = requests.get(self.floodlightBaseURL + 'core/switch/all/aggregate/json')

        if statsRequest.status_code == 200:
            statMap = statsRequest.json()
            self.buildStatsJSON(statMap)
        else:
            print('Error making GET request')
            print(statsRequest.text)


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


    def queryHostsAndLinks(self):
        devicesRequest = requests.get(self.floodlightBaseURL + 'device/')
        linksRequest = requests.get(self.floodlightBaseURL + 'topology/links/json')

        if (devicesRequest.status_code == 200) and (linksRequest.status_code == 200):
            deviceData = devicesRequest.json()
            linkData = linksRequest.json()
            self.buildHostsAndLinksJSON(deviceData, linkData)
        else:
            print('Error making GET request')
            print(devicesRequest.text)
            print(linksRequest.text)

    def buildHostsAndLinksJSON(self, deviceData, linkData):
        outputGraph = {
            'nodes': [],
            'edges': []
        }

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

        # publish to file
        with open('networkHostsAndLinks.json', 'w') as f:
            json.dump(outputGraph, f)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: buildGraph.py <poll-time-in-seconds>')
        sys.exit()
    pollTime = int(sys.argv[1])
    gb = GraphBuilder()
    res = gb.querySwitches()
    if res == -1:
        print('Could not connect to REST API to get switches')
        sys.exit()
    gb.queryHostsAndLinks()
    counter = 0
    while True:
        print('Querying REST API. Count #' + str(counter))
        gb.queryHostsAndLinks()
        gb.queryStats()
        time.sleep(pollTime)
        counter += 1

