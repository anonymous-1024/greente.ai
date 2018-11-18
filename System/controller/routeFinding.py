# -*- coding:utf-8 -*-

import copy

_ = float('inf')


class RouteFinding(object):
    """
    Route finding algorism class
    """

    graph = []
    vertexNum = 0

    def __init__(self, graph):
        """
        Initial the instance

        :param graph: network topology graph
        """
        self.graph = graph
        self.vertexNum = len(graph)
        self.miniNum=1

    def dijkstra(self, source):
        """
        Dijkstria algroism from one source to all other switches

        :param source: the start switch id
        :returns: a distance list and a previous node list
        """
        # initalizations
        dist = [_] * self.vertexNum
        visited = [False] * self.vertexNum
        previous = [[]] * self.vertexNum

        dist[source] = 0
        Q = set([source])

        while len(Q) > 0:
            # u = dist.index(min((dist[q] for q in Q if visited[q] == False)))

            seq = -1
            smallest = _
            for q in Q:
                if visited[q] == False:
                    if dist[q] < smallest:
                        smallest = dist[q]
                        seq = q
            u = seq

            # print('dist:', dist)
            # print('Q:', Q)
            # print('u:', u)
            Q.remove(u)
            visited[u] = True

            for v in range(self.vertexNum):
                if self.graph[u][v] < _:
                    alt = dist[u] + self.graph[u][v]
                    # print('alt', alt)
                    # print('dist[v]', dist[v])
                    if alt < dist[v]:
                        dist[v] = alt
                        previous[v] = []
                        previous[v].append(u)
                    elif alt == dist[v]:
                        if len(previous[v]) == 0 or u != v:
                            previous[v].append(u)
                    if not visited[v]:
                        # print('add', v)
                        Q.add(v)

        return dist, previous

    def dijkstra2(self, source):
        """
        Dijkstria algroism from one source to all other switches

        :param source: the start switch id
        :returns: a distance list and a previous node list
        """

        # initalizations
        dist = [_] * self.vertexNum
        visited = [False] * self.vertexNum
        previous = [[]] * self.vertexNum

        dist[source] = 0
        Q = set([source])

        while len(Q) > 0:
            # u = dist.index(min((dist[q] for q in Q if visited[q] == False)))

            seq = -1
            smallest = _
            for q in Q:
                if visited[q] == False:
                    if dist[q] < smallest:
                        smallest = dist[q]
                        seq = q
            u = seq

            # print('dist:', dist)
            # print('Q:', Q)
            # print('u:', u)
            Q.remove(u)
            visited[u] = True

            for v in range(self.vertexNum):
                if self.graph[u][v] < _:
                    alt = dist[u] + self.graph[u][v]
                    # print('alt', alt)
                    # print('dist[v]', dist[v])
                    # if alt < dist[v]-self.miniNum:
                    if alt < dist[v]:
                        dist[v] = alt
                        previous[v] = []
                        previous[v].append(u)
                    elif alt <= dist[v]+self.miniNum:
                    # elif alt == dist[v]:
                        if len(previous[v]) == 0 or u != v:
                            previous[v].append(u)

                    if not visited[v]:
                        # print('add', v)
                        Q.add(v)
        return dist, previous

    def findAllDijkstra(self):
        """
        Use dijkstra algroism to get all distance and previous lists in the given topology
        
        :returns: all distance and previous lists
        """
        allDistance = []
        allPrevious = []
        for m in range(len(graph)):
            dis, pre = self.dijkstra(m)
            allDistance.append(dis)
            allPrevious.append(pre)
        return allDistance, allPrevious

    def findRoute(self, source):
        """
        Use previous list to rebuild the route in netwrok without ecmp
        
        :param source: the source id
        :returns: a route list
        """
        dis, prev = self.dijkstra(source)
        # print(dis, prev)
        routeList = []
        for i in range(self.vertexNum):
            p = prev[i][0]
            route = [p]
            while p != source:
                p = prev[p][0]
                route.append(p)
            route.reverse()
            route.append(i)
            routeList.append(route)
        # print('routeList', routeList)
        return routeList

    def addPath(self, prev, i, source, routeList, p,loopTimes=None):
        """
        Use recursion to calculate the ecmp route list
        """
        if loopTimes!=None:
            if loopTimes>self.vertexNum:
                return
            else:
                loopTimes+=1
        if p in routeList or i in routeList:
            return
        else:
            routeList.append(p)
        if p != source:
            for prevNode in prev[p]:
                routeListCp = copy.deepcopy(routeList)
                self.addPath(prev, i, source, routeListCp, prevNode,loopTimes)
        else:
            routeList.reverse()
            routeList.append(i)
            self.routesList[i].append(routeList)

    def findRoutes(self, source):
        """
        Use previous list to rebuild the route in network with ecmp
        
        :param source: the source id
        :returns: a route list
        """
        dis, prev = self.dijkstra(source)
        self.routesList = [[] for i in range(self.vertexNum)]
        for i in range(self.vertexNum):
            for prevNode in prev[i]:
                if i != source:
                    routeList = []
                    self.addPath(prev, i, source, routeList, prevNode)
        self.routesList[source].append([source])
        return self.routesList

    
    def findMultiRoutes(self, source):
        """
        Use previous list to rebuild the route in network with ecmp
        
        :param source: the source id
        :returns: a route list
        """
        dis, prev = self.dijkstra2(source)
        # print('dis',dis)
        # print('prev',prev)
        self.routesList = [[] for i in range(self.vertexNum)]
        # print('routeList',self.routesList)
        for i in range(self.vertexNum):
            for prevNode in prev[i]:
                if i != source:
                    routeList = []
                    self.addPath(prev, i, source, routeList, prevNode,1)
        self.routesList[source].append([source])
        return self.routesList


if __name__ == '__main__':
    # graph = [
    #     [0, 6, 3, _, _, _],
    #     [6, 0, 2, 5, _, _],
    #     [3, 2, 0, 3, 4, _],
    #     [_, 5, 3, 0, 2, 3],
    #     [_, _, 4, 2, 0, 5],
    #     [_, _, _, 3, 5, 0],
    # ]
    graph = [
            [0, 1, 1, _, _, _],
            [1, 0, 1, 1, _, _],
            [1, 1, 0, 1, 1, _],
            [_, 1, 1, 0, 1, 1],
            [_, _, 1, 1, 0, 1],
            [_, _, _, 1, 1, 0],
    ]
    # graph = [
    #         [0, 1, 1, 1, 1, _],
    #         [1, 0, 1, 1, 1, _],
    #         [1, 1, 0, 1, 1, _],
    #         [1, 1, 1, 0, 1, 1],
    #         [1, 1, 1, 1, 0, 1],
    #         [_, _, _, 1, 1, 0],
    # ]

    routeFind = RouteFinding(graph)
    # print(routeFind.findAll())
    # print(routeFind.dijkstra(0))
    # for i in range(len(graph)):
        # print(routeFind.findRoute(i))
        # print(routeFind.findRoutes(i))
        # print(routeFind.findMultiRoutes(i))
    # print(routeFind.findRoute(0))
    # print(routeFind.findRoutes(0))
    print(routeFind.findMultiRoutes(0))
