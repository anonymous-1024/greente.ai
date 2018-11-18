import random
import Queue
import copy
import config
from email.utils import rfc2231_continuation
class graf():
    def __init__(self,nodes,links,initopo=[[]],inihost=[]):
        self.n=nodes
        self.maxQue=config.maxQues
        self.links=links
        self.color=[0 for i in range(self.n)]
        self.Q=[[0 for i in range(self.n)] for j in range(self.n)]
        self.E=initopo
        self.host=inihost
        if len(inihost)==0:
            self.E=[[0 for i in range(self.n)] for j in range(self.n)]
            self.host=[0 for i in range(self.n)]
    def randTopo(self):
        for i in range(self.n-1):
            self.E[i][i+1]=1
            self.E[i+1][i]=1
        i=0
        sn=self.n
        slinks=self.links
        while i<slinks-sn+1:
            r=random.randint(0,sn-1)
            c=random.randint(0,sn-1)
            if c!=r:
                self.E[r][c]=1
                self.E[c][r]=1
                i+=1  
        self.links=0
        for row in self.E:
            for linkele in row:
                self.links+=linkele
        print "random topology generated,total links:",self.links
    def pre_eval_action(self,a):
        if a<-self.n or a>self.n:
            print "interface error!"
            return 'Error',0
        if a==0:
            return 'D',0
        if (a<0 and self.color[-1-a]==0) or (a>0 and self.color[a-1]==1):
            return 'C',-10
        if a<0 and self.host[-a-1]==1:
            print"What the F**k",a
            return 'B',-20
        self.action(a)
        if self.check_connect():
            return 'A',0
        else:
            self.action(-a)
            return 'N',-10
    def action(self,a):
        if a<0:
            self.color[-a-1]=0
            for i in range(self.n):
                self.Q[-a-1][i]=0
                self.Q[i][-a-1]=0
        if a>0:
            self.color[a-1]=1
            for i in range(self.n):
                if self.color[i]==1:
                    self.Q[a-1][i]=self.E[a-1][i]
                    self.Q[i][a-1]=self.E[i][a-1]
    def getLiveNum(self):
        r=0
        for ele in self.color:
            if ele==1:
                r+=1
        return r
    def eval_Ques(self,Ques):
        n_live=self.getLiveNum()
        overLoad_links=0
        ols=0
        for qs in Ques[0]:
            if qs>=self.maxQue:
                ols+=1
                overLoad_links+=(qs-self.maxQue)/1000 +1
        vs=-n_live-config.overload_punish*overLoad_links
        #print "value of curr Ques:",r
        return vs,ols
    def initial(self):
        for i in range(1,self.n+1):
            self.action(i)
    def setHost(self,a):
        for ele in a:
            if ele<self.n:
                self.host[ele]=1
    def addhost(self,listh):
        for ele in listh:
            if ele>0 and ele<=self.n:
                self.host[ele-1]=1
    def printTopo(self):
        print "E:"
        print self.E
        print "Q:"
        print self.Q
        print "color"
        print self.color
        print "hosts:"
        print self.host
    def getFstNode(self):
        for j in range(self.n):
            if self.color[j]==1 and self.host[j]==1:
                return j        
        return 0
    def getOffNeighbor(self,i):
        for j in range(self.n):
            if self.E[i][j]==1 and self.color[j]==0:
                return j
        return -1
    def check_connect(self):
        for i in range(self.n):
            if self.host[i]==1 and self.color[i]==0:
                return False
        j=0;
        colors=copy.copy(self.color)
        q=Queue.Queue()
        while(colors[j]==0):
            j+=1
        if j>=self.n:return False
        q.put(j)
        while not q.empty():
            num=q.get()
            colors[num]=2
            for i in range(self.n):
                if self.Q[num][i]==1 and colors[i]!=2:
                    q.put(i)
        if 1 in colors:
            return False
        return True   
    def linkFilter(self,Ques):
        if len(self.E)!=len(Ques):
            print "http communication Error"
            return 0
        else:
            result=[]
            for i in range(len(Ques)):
                for j in range(len(Ques[i])):
                    if self.E[i][j]==1:
                        if self.Q[i][j]==0:
                            if Ques[i][j]!=0:
                                print"topology nonsynchronous Error"
                            result.append(-10)
                        else:
                            result.append(Ques[i][j])
        return result               
                
    def getpath(self):
        routQ=copy.deepcopy(self.Q)
        routcolor=[0 for i in range(self.n)]
        pathlist=[]
        i=self.getFstNode()
        subpath=[]
        while i!=-1:
            subpath.append(i)
            routcolor[i]=1
            i=self.g_next_node(i,self.n,routQ,routcolor)
            if(i==-1):
                break
            if len(subpath)>5 and self.host[i]==1 and i!=subpath[0]:
                subpath.append(i)
                pathlist.append(subpath)
                #print subpath
                subpath=[]
        '''
        if len(subpath)>1:      
            if subpath[0]==subpath[-1]:
                for i in range(len(subpath)-1):
                        routQ[subpath[i]][subpath[i+1]]=1
            else:      
                rear=subpath[len(subpath)-1]
                if self.host[rear]!=1:
                    subpath+=self.find_Host(rear,subpath[0])
                for i in range(len(subpath)-1):
                    routQ[subpath[i]][subpath[i+1]]=0
                pathlist.append(subpath)
        '''
        for k in range(len(subpath)-1):
                        routQ[subpath[k]][subpath[k+1]]=1
        for i in range(len(routQ)):
            for j in range(len(routQ[i])):
                if routQ[i][j]!=0:
                    propath=list(reversed(self.find_Host(i,j)))+[i,j]
                    bupath=propath+self.find_Host(j,propath[0])
                    pathlist.append(bupath)
                    for k in range(len(bupath)-1):
                        routQ[bupath[k]][bupath[k+1]]=0   
                    if routQ[j][i]!=0:
                        bupath=list(reversed(bupath))
                        pathlist.append(bupath)
                        for k in range(len(bupath)-1):
                            routQ[bupath[k]][bupath[k+1]]=0                 
        print routQ
        return pathlist
    def find_Host(self,a,sourcehost):
        if self.host[a]==1: 
            return []
        q=Queue.Queue()
        colors=copy.copy(self.color)
        for i in range(self.n):
            if self.Q[a][i]==1:
                if self.host[i]==1 and i!=sourcehost:
                    return [i]
                else:
                    colors[i]=2
                    q.put([i])
        while not q.empty():
            paths=q.get()
            rear=paths[-1]
            for i in range(self.n):
                if self.Q[rear][i]==1:
                    if self.host[i]==1 and i!=sourcehost:
                        paths.append(i)
                        return paths
                    else:
                        if colors[i]!=2:
                            colors[i]=2
                            q.put(paths+[i])
        return 0                
    def g_next_node(self,i,n,b,color):
        j=i+1
        for c in range(n):
            if color[c]==0 and b[i][c]==1:
                b[i][c]=0
                return c
        while j<n:
            if b[i][j]==1 :
                b[i][j]=0
                return j
            j+=1
        j=i-1
        while j>=0:
            if  b[i][j]==1:
                b[i][j]=0
                return j
            j-=1
        return -1   
'''    
atest=graf(30,50)
atest.randTopo()
atest.action(3)
atest.action(7)
atest.action(9)
print atest.color
print atest.check_connect()
atest.initial()
print atest.color
print atest.check_connect()
atest.printTopo()
atest.setHost([0,15,25,49])
atest.action(-6)
atest.action(-1)
print atest.color
print atest.find_Host(6)
print atest.getpath()
print atest.Q
        
''' 

            