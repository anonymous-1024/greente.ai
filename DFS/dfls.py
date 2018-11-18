#!/usr/bin/python
import random
import sys   
sys.setrecursionlimit(1000000)

SNUM_MAX=501   #switch_num is [3, SNUM_MAX-1] 
TEST_MAX=10

class Mytopo:

	def __init__(self, switch_num):
		self.snum = switch_num
		self.pathCount = 0
		self.linkState = [[0 for i in range(self.snum)] for i in range(self.snum)]
		self.visited = [0 for i in range(self.snum)]

	def clrPara(self):
		for i in range(self.snum):
			for j in range(i+1, self.snum):
				self.linkState[i][j] = 0
				self.linkState[j][i] = 0
			self.visited[i] = 0
		self.pathCount = 0

	def DFS(self, v):
		self.visited[v] = 1
		for j in range(self.snum):
			if self.linkState[v][j] == 1 and self.visited[j] == 0:
				self.DFS(j)

	def createTopo(self):
		self.clrPara()
		#create topo randomly
		for i in range(self.snum):
			for j in range(i+1, self.snum):
				link = random.randint(0,1)
				self.linkState[i][j] = link
				self.linkState[j][i] = link
		#check the network connectivity using DFS
		specNode = []
		for i in range(self.snum):
			if self.visited[i] == 0:
				self.DFS(i)
				specNode.append(i)
		#if the network is unconnected, connect each specialNode
		for i in range(len(specNode)-1):
			self.linkState[specNode[i]][specNode[i+1]] = 1
			self.linkState[specNode[i+1]][specNode[i]] = 1

		#print the topo
		# print self.linkState

	def DFLS(self, v, isNewPath):
		if isNewPath == 1:
			# print " "
			# print v, " "
			self.pathCount += 1
			isNewPath = 0
		# else:
		# 	print v, " "

		for j in range(self.snum):
			if self.linkState[v][j] == 1:
				self.linkState[v][j] = 0
				self.linkState[j][v] = 0
				isNewPath = self.DFLS(j, isNewPath)
		return 1


for switch_num in range(3, SNUM_MAX):
	mytopo = Mytopo(switch_num)
	pathCount = 0
	pathCountAvg = 0
	for i in range(TEST_MAX):
		mytopo.createTopo()
		mytopo.DFLS(0, 1)
		pathCount = pathCount + mytopo.pathCount
	pathCountAvg = pathCount/TEST_MAX
	print "snum: ", mytopo.snum, "pathnum: ", pathCountAvg
