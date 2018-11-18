#!/usr/bin/env python2
# -*- coding:utf-8 -*-

from device import Switch, Host
from routeFinding import RouteFinding
from switchRuntime import SwitchRuntime
from topoMaker import TopoMaker
from dBParser import DBParser

import copy
import socket
import json
import time
import logging
import configparser

_ = float('inf')


class Ctrl(object):
    """
    The controller's main control flow class.
    """

    def __init__(self, switchGraph, hostList):
        """
        Constructor, use switch graph and host list generate or initialize some instance variables or algorithm, and calculate some variables
        varibles list
        switchGraph: a two-dimension graph to describe the origin network
        graph: a two-dimension graph to describe the current network situation
        vertexNum: the switch num in the network
        routeFinding: initial the route finding algorithm with switch graph
        hostList: the list of which switch has a host

        hosts: hosts in network
        switches: switches in network
        oldGraph: never used
        oldSwitchList: never used
        socketList: socket links to each host in network
        socketPort: the specific port num to generate the link hosts in netwrok
        nowActId: the number of actions from AI
        dbInfo: the database connection information
        dbParser: initial the database parser with switch number and database connection information

        qdepth: the queue depth in network
        qrate: the queue rate in network
        qratesmall: (temporatory) a smaller queue rate in netwrok

        :param switchGraph:  a two-dimension graph to describe a network
        :param hostList: a one-dimension list to describe which switch in network has a host connection
        """
        self.getConfig()

        self.switchGraph = copy.deepcopy(switchGraph)
        self.graph = switchGraph
        self.vertexNum = len(switchGraph)
        self.hostList = hostList
        self.switchList = [1] * self.vertexNum
        self.hosts = []
        self.switches = []
        self.oldGraph = []
        self.oldSwitchList = []
        self.socketList = []
        self.nowActId = 0
        self.dbParser = DBParser(self.vertexNum, self.dbInfo, self.switches)

        logging.info('Init switchGraph ' + '#'.join(z for z in map(
            lambda x: ','.join(str(y) for y in x), self.graph)))
        logging.info('Init hostList ' + ','.join(str(host)
                                                 for host in hostList))

    def getConfig(self):

        configs = configparser.ConfigParser()
        configs.read('config.ini')

        def getSpecSection(section):
            def readSection(option):
                return configs.get(section, option)
            return readSection

        _gdb = getSpecSection('mysql')
        self.dbInfo = {
            'host': _gdb('host'),
            'passwd': _gdb('passwd'),
            'user': _gdb('user'),
            'db': _gdb('db'),
            'port': int(_gdb('port')),
            'charset': _gdb('charset'),
        }

        _gsocket = getSpecSection('socket')
        self.socketPort = int(_gsocket('port'))

        _gqueue = getSpecSection('queue')
        self.qdepth = int(_gqueue('qdepth'))
        self.qrate = int(_gqueue('qrate'))

        _gswitches = getSpecSection('switches')

    def getSwitchByName(self, name):
        """
        Get a switch in switch list by its name

        :param name: switch name, such as s1
        :returns: a switch instance
        """
        return self.switches[int(name[1:])]

    def getHostByName(self, name):
        """
        Get a host in host list by its name

        :param name: host name, such as h1
        :returns: a host instance
        """
        return self.hosts[int(name[1:])]

    def genMac(self, id):
        """
        Generate a MAC address by device id 

        only support host id and must form 0 to 255 now

        :param id: device id
        :returns: a MAC address calculated by device id
        """
        # only support id form 0 to 255 now
        macPrefix = '00:01:00:00:00:'
        hexId = hex(id)[2:].upper()
        if len(hexId) == 1:
            hexId = '0' + hexId
        mac = macPrefix + hexId
        return mac

    def genIp(self, id, isOvs=False):
        """
        Generate a IP address by device id 

        only support host id and must form 0 to 255 now

        :param id: device id
        :param isOvs: indicate the device is OpenVSwitch or P4 host
        :returns: a IP address calculated by device id
        """
        # only support id form 0 to 255 now
        if isOvs:
            ipPrefix = '192.168.8.'
        else:
            ipPrefix = '10.0.0.'
        ip = ipPrefix + str(id + 100)
        return ip

    def genDevice(self):
        """
        Generate logical device instance and add thrift link to host
        """
        for i in range(self.vertexNum):
            thriftPort = 9090 + i
            self.switches.append(
                Switch('s' + str(i), thriftPort, SwitchRuntime(thriftPort=thriftPort)))
            if self.hostList[i] == 1:
                self.hosts.append(
                    Host('h' + str(i), self.genMac(i), self.genIp(i), self.genIp(i, True)))
            else:
                self.hosts.append(None)

    def genLinks(self):
        """
        Generate logical links to devices
        """
        for i in range(self.vertexNum):
            for j in range(i + 1, self.vertexNum):
                if self.graph[i][j] != _:
                    self.switches[i].addLink('s' + str(j))
                    self.switches[j].addLink('s' + str(i))

        for i in range(self.vertexNum):
            if self.hostList[i] == 1:
                self.hosts[i].addLink('s' + str(i))
                self.switches[i].addLink('h' + str(i))

    def genArpTable(self):
        """
        Generate arp table and add to each switches logically 
        """
        arpList = [('doarp', 'arpreply', ('00:00:00:00:00:00', host.ipAddress), host.macAddress)
                   for host in self.hosts if host is not None]
        for i in range(self.vertexNum):
            self.switches[i].tables = self.switches[i].tables + arpList

    def getDevPortByName(self, deviceName, nextDeviceName):
        """
        Get a device port on one device which is linked to another specified device

        :param deviceName: the device name to calculate the port
        :param nextDeviceName the name of device which the port linked to
        """
        devices = None
        deviceType = deviceName[0:1]
        deviceId = int(deviceName[1:])
        if deviceType == 's':
            devices = self.switches
        elif deviceType == 'h':
            devices = self.hosts
        if devices:
            device = devices[deviceId]
            for port in device.ports:
                if port.deviceName == nextDeviceName:
                    return port.portNum
        return None

    def genRouteInfoViaPort(self, portsList):
        """
        Generate source route info string by a list of ports on each switch

        :param portsList: a route port list for source routeing
        :returns: a info string for source routing
        """
        portStr = ''
        for port in portsList:
            binPort = bin(port)[2:]
            for i in range(4 - len(binPort) % 4):
                binPort = str(0) + binPort
            portStr = portStr + binPort
        portStr = hex(int(portStr, 2))
        return portStr

    def genSwitchTransTable(self):
        """
        Generate route table on switch for normal packet (maybe a little bit complex)
        """

        print('switch list', self.switchList)
        routeFinding = RouteFinding(self.graph)

        class Node(object):
            """
            Node for a build tree
            """

            def __init__(self, nodeId):
                self.nodeId = nodeId
                self.childNodes = []
                self.childNodeIds = []

            def addChild(self, nodeId, nodeInstance):
                self.childNodeIds.append(nodeId)
                self.childNodes.append(nodeInstance)

            def getChildrenById(self, nodeId):
                if nodeId in self.childNodeIds:
                    nodePos = self.childNodeIds.index(nodeId)
                    return self.childNodes[nodePos]
                return None

            def getNodeId(self):
                return self.nodeId

            def getChildNum(self):
                return len(self.childNodeIds)

            def __str__(self):
                return str(self.nodeId)

        def addRouteByNode(node):
            """
            Add ecmp routes by recursion
            :param node: a Node instance in the build tree
            """
            childNodes = node.childNodes
            portsList = [self.getDevPortByName('s' + str(node.nodeId), 's' + str(childNode.nodeId))
                         for childNode in childNodes]
            if portsList:
                portStr = self.genRouteInfoViaPort(portsList)
                routeNum = len(portsList)
                tableItem = ('dotrans', 'l2setmetadataecmp',
                             (sourceHost.macAddress, destHost.macAddress), (routeNum, portStr))
                self.switches[node.nodeId].tables.append(tableItem)
            for childNode in childNodes:
                addRouteByNode(childNode)

        for i in range(len(self.hostList)):
            if self.hostList[i] == 1 and self.switchList[i] == 1:
                # print('route source', i)
                # routes = routeFinding.findRoutes(i)
                routes = routeFinding.findMultiRoutes(i)
                sourceSwitch = self.switches[i]
                sourceHost = self.hosts[i]
                for j in range(len(self.hostList)):
                    if self.hostList[j] == 1 and self.switchList[j] == 1 and i != j:
                        # print('route dest',j)
                        route = routes[j]
                        destSwitch = self.switches[j]
                        destHost = self.hosts[j]
                        print(sourceSwitch.name, destSwitch.name, route)

                        rootNode = Node(i)
                        nowNode = rootNode
                        for path in route:
                            for nodeId in path:
                                if nodeId != i:
                                    nextNode = nowNode.getChildrenById(nodeId)
                                    if nextNode:
                                        nowNode = nextNode
                                    else:
                                        childNode = Node(nodeId)
                                        nowNode.addChild(nodeId, childNode)
                                        nowNode = childNode
                            nowNode = rootNode

                        addRouteByNode(rootNode)

    def genHostTransTable(self):
        """
        Generate route table to last host for normal packet
        """
        for i, destHost in enumerate(self.hosts):
            if destHost:
                port = self.getDevPortByName('s' + str(i), 'h' + str(i))
                for srcHost in self.hosts:
                    if srcHost:
                        portStr = self.genRouteInfoViaPort([port, ])
                        tableItem = ('dotrans', 'l2setmetadataecmp',
                                     (srcHost.macAddress, destHost.macAddress), (1, portStr))
                        self.switches[i].tables.append(tableItem)

    def genDeviceNoTable(self):
        """
        Generate device number table to switches 

        the device number is used to indicate the switch itself
        """
        for id, switch in enumerate(self.switches):
            tableItem = ('setmetadata', 'setdeviceno', '', id)
            switch.tables.append(tableItem)

    def getTableInfo(self):
        """
        Get all tables in all switches
        :returns: a table list for all tables
        """
        tables = []
        for switch in self.switches:
            tables.append(switch.tables)
        return tables

    def genTables(self, doClear=False):
        """
        Generate trans table with route list and push arplist to all switches and send information to front end
        :param doClear: clear old tables in all switches logically or not
        """
        if doClear:
            for switch in self.switches:
                switch.tables = []
        self.genArpTable()
        self.genSwitchTransTable()
        self.genHostTransTable()
        self.genDeviceNoTable()

    def downTables(self, doClear=False):
        """
        Down all tables to all the switched in the true network
        :param doClear: clear old tables in all switches truely or not
        """
        for switch in self.switches:
            # print(switch.runtime.TABLES)
            # print(switch.name)
            if doClear:
                switch.runtime.table_clear('dotrans')
            for table in switch.tables:
                # print(table)
                tableName = table[0]
                actionName = table[1]
                keys = table[2]
                values = table[3]
                switch.runtime.table_add(tableName, actionName, keys, values)

    def makeTopo(self):
        """
        Build the true netwrok using the informatin in controller and change queue depth/rate in switches 
        """
        switchPath = 'simple_switch'
        jsonPath = 'p4app/app.json'
        self.topoMaker = TopoMaker(switchPath, jsonPath, self)
        self.topoMaker.cleanMn()
        self.topoMaker.genMnTopo()
        for i, switch in enumerate(self.switches):
            # if i == 8 or i == 9:
                # switch.runtime.makeThriftLink(self.qdepth, self.qratesmall)
            # else:
                # switch.runtime.makeThriftLink(self.qdepth, self.qrate)
            switch.runtime.makeThriftLink(self.qdepth, self.qrate)

    def genHostLink(self, host):
        """
        Make socket link to a specific host in the true network
        :param host: the host to make socket link
        """
        try:
            print(host.ovsIpAddress, self.socketPort, 'connecting')
            socketLink = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socketLink.connect((host.ovsIpAddress, self.socketPort))
            return socketLink
        except:
            print('socket gen failed', host.name)
            return None

    def genSocketLinkToHosts(self):
        """
        Make socket links to all hosts in the network
        """
        self.socketList = []
        print('start connect')
        for host in self.hosts:
            if host:
                print('connecting ', host.ovsIpAddress)
                socketLink = self.genHostLink(host)
                print(host.ovsIpAddress, 'connected')
                # socketLink.connect(('192.168.150.101', self.socketPort))
                self.socketList.append(socketLink)
            else:
                self.socketList.append(None)
        # socketLink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # socketLink.connect(('192.168.150.110', self.socketPort))
        # self.socketList.append(socketLink)
        # for i in range(5):
        #     self.socketList.append(None)

    def sendInfoViaSocket(self, hostId, sendType, info):
        """
        Send information to host in true network with the socket establish before
        :param hostId: the host to send information
        :param sendType: the information type
        :param info: the information content
        :returns: the send status (success=>True/failed=>False)
        """
        def sendInfo(sendType, info):
            socketLink.send(json.dumps({
                'type': sendType,
                'info': info
            }))

        socketLink = self.socketList[hostId]
        if socketLink:
            try:
                sendInfo(sendType, info)
            except:
                time.sleep(5)
                socketLink = self.genHostLink(self.hosts[hostId])
                sendInfo(sendType, info)
                pass
            return True
        return False

    def sendTestInfo(self):
        """
        Send info to test the conntection between controller and hosts
        """
        for hostId, host in enumerate(self.hosts):
            if host:
                ret = self.sendInfoViaSocket(hostId, 'Test', None)
                print(hostId, ret)
                socketLink = self.socketList[hostId]

    def traversePaths(self, paths, sendTimes=3):
        """
        Traverse all path using source routing to get all information in network use INT
        generate traverse info and send it to host by socket link
        :param paths: traverse path from AI
        """
        startNodeDict = {}
        for path in paths:
            startNodeDict[path[0]] = {
                'portsLists': [],
                'addressList': []
            }
        for path in paths:
            portsList = [self.getDevPortByName(
                's' + str(path[i]), 's' + str(path[i + 1])) for i in range(len(path) - 1)]
            portsList.append(self.getDevPortByName(
                's' + str(path[len(path) - 1]), 'h' + str(path[len(path) - 1])))
            # print('path', path)
            # print('portsList', portsList)
            address = self.hosts[path[len(path) - 1]].ipAddress
            startNode = path[0]
            startNodeDict[startNode]['portsLists'].append(portsList)
            startNodeDict[startNode]['addressList'].append(address)
        for key, sendObj in startNodeDict.items():
            # print('portslists', key, sendObj['portsLists'])
            self.sendInfoViaSocket(key, 'TraversePath', {
                'portsLists': sendObj['portsLists'],
                'addressList': sendObj['addressList'],
                'actId': self.nowActId,
                'sendTimes': sendTimes
            })

    def start(self):
        """
        Use the given topo and hosts start the experiment envirnoment

        generate devices, links, tables
        then generate the mininet network, link host with socket,
        then send information to front end

        :returns: True
        """
        self.genDevice()
        self.genLinks()
        self.genTables()
        self.makeTopo()
        self.downTables()
        # self.genSocketLinkToHosts()
        # self.dbParser.traunce_db()
        return True

    def updateGraphByAction(self, action):
        """
        Update the topology in network by switch ID

        :param action: action switch ID(positive means open a switch, negative means close a switch, zero means no action, id is larger than actual 1)
        :returns: Boolen (True means an action had done, False means no action been done)
        """
        close = False
        if action == 0:
            return False
        elif action < 0:
            action = -action
            # xiaoyujie's start id is 1
            self.switchList[action - 1] = 0
            close = True
        else:
            self.switchList[action - 1] = 1

        for i in range(self.vertexNum):
            if i != action - 1:
                if close:
                    self.graph[i][action - 1] = _
                    self.graph[action - 1][i] = _
                else:
                    self.graph[i][action - 1] = self.switchGraph[i][action - 1]
                    self.graph[action - 1][i] = self.switchGraph[action - 1][i]

        return True

    def update(self, action=None, paths=None, counter=False, times=None):
        """
        Receive parameters from AI, then update topology and traverse all INT path, last, get the rewardMatrix and send it to AI and front end

        :param action: action switch ID
        :param paths: path switch ID lists (the switches who need to do INT)
        :returns: rewardMatrix (the matrix contains link queue depth per route)
        """
        # self.oldGraph.append(self.graph)
        # self.oldSwitchList.append(self.switchList)
        self.nowActId = self.nowActId + 1
        print('now act id ', self.nowActId)
        logging.info('Update action ' + str(action))
        rewardMatrix = None
        # print('action', action)
        if action:
            if self.updateGraphByAction(action):
                self.genTables(True)
                self.downTables(True)
        time.sleep(1)
        if counter:
            counterList = [[0 for i in range(len(self.switches))]
                           for i in range(len(self.switches))]
            packetCount = self.getPacketCount()[1]
            for sid, switch in enumerate(self.switches):
                if self.switchList[sid] == 0:
                    continue
                for pid, port in enumerate(switch.ports):
                    if port.deviceName[0:1] == 's':
                        switchId = int(port.deviceName[1:])
                        if self.switchList[switchId] == 0:
                            continue
                        counterList[switchId][sid] = packetCount[sid][pid]
            rewardMatrix = counterList
            print(rewardMatrix)

        if paths:
            if times:
                self.traversePaths(paths, times)
            else:
                self.traversePaths(paths)
            logging.info(
                'Update paths ' + '#'.join(z for z in map(lambda x: ','.join(str(y) for y in x), paths)))
            time.sleep(10)
            rewardMatrix = self.dbParser.parser(self.nowActId)
            logging.info('Update rewardMatrix ' + '#'.join(z for z in map(
                lambda x: ','.join(str(y) for y in x), rewardMatrix)))

        for i, row in enumerate(rewardMatrix):
            for j, reward in enumerate(row):
                if reward > congThreshold:
                    congInfo += 1
                if self.graph[i][j] == 1:
                    runLinkNum += 1

        return rewardMatrix

    def reset(self):
        """
        Reset the network status

        is used to start the next round of training after a round of training
        it will send restart message to front end

        :returns: True
        """
        self.graph = copy.deepcopy(self.switchGraph)
        self.switchList = [1] * self.vertexNum
        self.genTables(True)
        self.downTables(True)

        return True

    def convertGraphInf(self):
        """
        Convert 'Inf' represented in Python to -1, for JavaScript can't resolve Inf in Python

        :returns: a converted topology graph
        """
        convertedGraph = map(lambda graphRow: map(
            lambda x: x if x != _ else -1, graphRow), self.graph)
        return convertedGraph

    def getPacketCount(self):
        ingressCounterList = []
        egressCounterList = []
        for switch in self.switches:
            switch.runtime.counter_reset('ingress_counter')
            switch.runtime.counter_reset('egress_counter')
        time.sleep(4)
        for switch in self.switches:
            switchIngressCounter = []
            switchEgressCounter = []
            for portId in range(switch.portSum):
                switchIngressCounter.append(switch.runtime.counter_read(
                    'ingress_counter', portId+1).packets)
                switchEgressCounter.append(switch.runtime.counter_read(
                    'egress_counter', portId+1).packets)
            ingressCounterList.append(switchIngressCounter)
            egressCounterList.append(switchEgressCounter)
        return ingressCounterList, egressCounterList


if __name__ == '__main__':
    graph = [
        [0, 1, 1, _, _, _],
        [1, 0, 1, 1, _, _],
        [1, 1, 0, 1, 1, _],
        [_, 1, 1, 0, 1, 1],
        [_, _, 1, 1, 0, 1],
        [_, _, _, 1, 1, 0],
    ]
    # only support one host per switch
    hostList = [1, 1, 1, 0, 1, 1]
    # print(graph)
    # print(json.dumps(graph))
    # print(json.dumps(hostList))
    app = Ctrl(graph, hostList)
    # app.start()
    # app.update(-3)
    # paths = [[0, 1, 2, 3], [0, 2, 1, 3]]
    # paths = None
    # app.update(-1, paths)
    # app.update(-2)
    # app.update(-4)
    # app.update(-5)
    # app.update(1, paths)
    app.convertGraphInf()
    print('end')
