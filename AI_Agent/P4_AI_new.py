import numpy as np
import tensorflow as tf
import config
import csv
import graph
import RLAgent
import httpConec2 as hC
import matplotlib.pyplot as plt
from matplotlib.pyplot import draw

topo,hosts,nodes,hostnum,links=config.topo
print "host num:",hostnum
print "nodes num:",nodes
ag=RLAgent.PGNAgent(links,(nodes-hostnum)*2+1)
atest=graph.graf(nodes,links,initopo=topo,inihost=hosts)
atest.initial()
atest.printTopo() 
stepnum=2000
batch_size=config.batchsize
batch_sum=0   
episode_number=0
valid_action=0
total_episodes=config.episodes
xs,ys,rs=[],[],[]
epslon=config.explore_rate
plt_ANPB=[]
plt_ENPB=[]
plt_RNPB=[]
plt_rb=[]
overlink_record=[]
rsp=hC.sendTopo(atest.E,atest.host)
gradBuffer=ag.sess.run(ag.tvars)
done=0
ANPB,ENPB,RNPB=0,0,0
saver = tf.train.Saver()
model_path = config.model_path
if not config.fresh_train:
    load_path = saver.restore(ag.sess, model_path)
else:
    with open("varingTest.csv","w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["action","overLoad","powerOn","values"])
def updateNN(xs,ys,rs):
    global ANPB,ENPB,RNPB
    with open(config.record_batch_file,"a") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([ANPB,ENPB,RNPB])
    ANPB,ENPB,RNPB=0,0,0
    epx = np.vstack(xs)
    epy = np.vstack(ys)
    epr = np.vstack(rs)
    plt_rb.append(np.mean(epr))    
    tgrad=ag.calGrad(epx, epy, epr)
    if config.show_batch:
        print("upgrade with batch ",len(plt_rb)," ,in episode ",episode_number,"avg_reward=",plt_rb[-1])  
    for ix,grad in enumerate(tgrad):
        gradBuffer[ix] += grad  
        ag.applyGrad(gradBuffer)
    for ix,grad in enumerate(gradBuffer):
        gradBuffer[ix] = grad * 0
    save_path = saver.save(ag.sess, model_path)
act=False
pre_vs,pre_ol=-atest.n,0
xs.append([[0 for i in range(links)]])
ys.append(0)
for steps in range(stepnum):
    ANPB+=1
    print("send action",steps," :",act)
    env=hC.sendact(act)
    obs=np.reshape(atest.linkFilter(env),[1,links])
    print(" get observation f:",obs)
    vs,ol=atest.eval_Ques(obs)
    rs.append(vs-pre_vs)
    if rs[-1]>0:
        RNPB+=1
    if len(xs)==batch_size:
            updateNN(xs, ys, rs)
            xs,ys,rs=[],[],[]
    with open("varingTest.csv","a") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([act,ol,atest.getLiveNum(),vs])
    xs.append(obs)
    pre_vs,pre_ol=vs,ol
    act=ag.rollaction(obs)[0][0] if np.random.uniform()<epslon else np.random.randint(0,ag.ny-1)
    ys.append(act)
    act-=(nodes-hostnum)
    action_type,imm_reward=atest.pre_eval_action(act)
    while action_type!='D' and action_type!='A':
        rs.append(-10)
        if len(xs)==batch_size:
            updateNN(xs, ys, rs)
            xs,ys,rs=[],[],[]
        xs.append(obs)
        act=ag.rollaction(obs)[0][0] if np.random.uniform()<epslon else np.random.randint(0,ag.ny-1)
        ys.append(act)
        act-=(nodes-hostnum)
        action_type,imm_reward=atest.pre_eval_action(act)
    
