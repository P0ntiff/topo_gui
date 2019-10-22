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
        self.switchIDList = []
        self.switchPortToLinkMap = {}

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
        self.switchIDList = switchList
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
            edgeID = sourceSwitchID + '_to_' + destSwitchID
            self.switchPortToLinkMap[(sourceSwitchID, sourceSwitchPort)] = edgeID
            self.switchPortToLinkMap[(destSwitchID, destSwitchPort)] = edgeID
            # append edge from switch to other switch 
            edge = {'data': 
                        {'id': edgeID, 
                            'weight': 1,
                            'source': sourceSwitchID, 
                            'target': destSwitchID,
                            'sourceSwitchPort': sourceSwitchPort,
                            'destSwitchPort': destSwitchPort},
                    'classes': 'switch-switch-link'}
            outputGraph['edges'].append(edge)

        return outputGraph

    def queryLinkDataAndStats(self):
        # link delay and hpv raw data
        linkDataRequest = requests.get(self.floodlightBaseURL + 'linkverifier/links/json')
        if (linkDataRequest.status_code != 200):
            print('Error making GET requests for link data')
            return -1
        linkData = linkDataRequest.json()

        # link stats raw data
        linkStatsRequest = requests.get(self.floodlightBaseURL + 'core/switch/all/port/json')
        if linkStatsRequest.status_code != 200:
            print('Error making GET request for link stats')
        statData = linkStatsRequest.json()

        outputData = self.parseLinkDataAndStats(linkData, statData)

        # publish to file
        with open('networkLinkData.json', 'w') as f:
            json.dump(outputData, f)

    def parseLinkDataAndStats(self, linkData, statData):
        outputData = {}
        for link in linkData:
            srcSwitchDPID = link['src-switch']
            srcSwitchID = self.switchBaseID + srcSwitchDPID[-2:]
            srcSwitchPort = link['src-port']
            destSwitchDPID = link['dst-switch']
            destSwitchID = self.switchBaseID + destSwitchDPID[-2:]
            destSwitchPort = link['dst-port']
            delay = link['current-known-delay']
            lastHpvTime = link['last-hpv-received-time']
            timeStamp = link['time-stamp']
            hpvStatus = link['hpv-verified-status']
            statsStatus = link['stats-verified-status']
            edgeID = self.switchPortToLinkMap[(srcSwitchID, srcSwitchPort)]
            outputData[edgeID] = {'data': 
                                    {'id': edgeID, 
                                     'weight': 1,
                                     'source': srcSwitchID, 
                                     'target': destSwitchID,
                                     'sourceSwitchPort': srcSwitchPort,
                                     'destSwitchPort': destSwitchPort,
                                     'delay': delay,
                                     'lastHpvTime': lastHpvTime,
                                     'timeSinceLastHpv': timeStamp - lastHpvTime if lastHpvTime != 0 else -1,
                                     'hpvStatus': hpvStatus,
                                     'statsStatus': statsStatus},
                                'classes': 'switch-switch-link'}
            sourceSwitchStats = statData[srcSwitchDPID]
            # get stats for source switch port
            for switchPortData in sourceSwitchStats:
                if switchPortData['portNumber'] == srcSwitchPort:
                    srcTransmitBytes = switchPortData['transmitBytes']
                    srcReceiveBytes = switchPortData['receiveBytes']
                    outputData[edgeID]['data']['sourceTransmitBytes'] = srcTransmitBytes
                    outputData[edgeID]['data']['sourceReceiveBytes'] = srcReceiveBytes
            destSwitchStats = statData[destSwitchDPID]
            # get stats for dest switch port
            for destPortData in destSwitchStats:
                if destPortData['portNumber'] == destSwitchPort:
                    destTransmitBytes = destPortData['transmitBytes']
                    destReceiveBytes = destPortData['receiveBytes']
                    outputData[edgeID]['data']['destTransmitBytes'] = destTransmitBytes
                    outputData[edgeID]['data']['destReceiveBytes'] = destReceiveBytes

            # store the difference in transmitted vs received for both switch ports
            outputData[edgeID]['data']['sourceDifference'] = \
                outputData[edgeID]['data']['sourceTransmitBytes'] - \
                outputData[edgeID]['data']['destReceiveBytes']
            outputData[edgeID]['data']['destDifference'] = \
                outputData[edgeID]['data']['destTransmitBytes'] - \
                outputData[edgeID]['data']['sourceReceiveBytes']
        return outputData

    # def queryStats(self):
    #     statsRequest = requests.get(self.floodlightBaseURL + 'core/switch/all/aggregate/json')
    #     if statsRequest.status_code != 200:
    #         print('Error making GET request for stats data')
    #     statMap = statsRequest.json()
    #     self.buildStatsJSON(statMap)

    # def buildStatsJSON(self, statMap):
    #     outputObject = {}

    #     for switch in statMap:
    #         packetCount = statMap[switch][0]['packetCount']
    #         byteCount = statMap[switch][0]['byteCount']
    #         flowCount = statMap[switch][0]['flowCount']
    #         switchID = self.switchBaseID + switch[-2:]

    #         # ouptut node with stats
    #         node = {'data' : 
    #                     {'id' : switchID, 
    #                     'packetCount' : packetCount, 
    #                     'byteCount' : byteCount, 
    #                     'flowCount' : flowCount}}
    #         outputObject[switchID] = node

    #     # publish to file
    #     with open('networkStats.json', 'w') as f:
    #         json.dump(outputObject, f)


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
        gb.queryLinkDataAndStats()
        time.sleep(pollTime)
        counter += 1

