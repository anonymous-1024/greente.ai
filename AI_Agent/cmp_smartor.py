import numpy as np
import config
import csv
import graph
import httpConec2 as hC
import random
topo,hosts,nodes,hostnum,links=config.topo
print "host num:",hostnum
print "nodes num:",nodes

def get_act_list(env,graf):
    acts_on=[]
    acts_off=[]
    n=len(env)
    for i in range(n):
        nol_i=0
        for j in range(n):
            if env[i][j]>=config.maxQues:
                act=graf.getOffNeighbor(i)
                if act!=-1 and (act+1 not in acts_on):
                    acts_on.append(act+1)
            else:
                nol_i+=1
        if nol_i==n and graf.color[i]==1:
            acts_off.append(-i-1)
    return acts_on,acts_off
                           
atest=graph.graf(nodes,links,initopo=topo,inihost=hosts)
atest.initial()
atest.printTopo() 
time_step=100
power_record=[]
overlink_record=[]
record_vs=[]
with open(config.record_smart_file,"w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["action","overLoad","powerOn","values"])
rsp=hC.sendTopo(atest.E,atest.host)
act=False
for steps in range(time_step):
    env=hC.sendact(act)
    #obs=atest.linkFilter(env) 
    obs=np.reshape(atest.linkFilter(env),[1,links])
    print("send action:",act," get observation f:",obs)
    vs,ol=atest.eval_Ques(obs)
    with open(config.record_smart_file,"a") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([act,ol,atest.getLiveNum(),vs])
    acts_on,acts_off=get_act_list(env,atest)
    random.shuffle(acts_on)
    random.shuffle(acts_off)
    print("act list is:",acts_on,acts_off)
    if acts_on!=[]:
        act=acts_on[0]
        atest.action(act)
    else:
        for actenum in acts_off:
            atest.action(actenum)
            if atest.check_connect():
                act=actenum
                break
            else:
                atest.action(-actenum)
        if acts_off==[] or (act not in acts_off) :
            act=False
