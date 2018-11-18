import numpy as np
import tensorflow as tf
import config
import csv
import graph
import RLAgent
import httpConec as hC
import matplotlib.pyplot as plt
from matplotlib.pyplot import draw
def xishu(a):
    i=10
    r=[]
    while i<len(a)-10:
        r.append(np.mean(a[i-10:i+10]))
        i+=5
    r.append(np.mean(a[i:]))
    return r
def draws(a):
    plt_xs=range(len(a))
    plt.plot(plt_xs,a)
    plt.show()

topo,hosts,nodes,hostnum,links=config.topo
print hostnum
print nodes
ag=RLAgent.PGNAgent(links,(nodes-hostnum)*2+1)
atest=graph.graf(nodes,links,initopo=topo,inihost=hosts)
atest.initial()
atest.printTopo() 

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
plt_re=[]
plt_ae=[]
plt_ANPE,plt_ENPE,plt_RNPE=[],[],[]

env=atest.Q
gradBuffer=ag.sess.run(ag.tvars)
done=0
ANPB,ENPB,RNPB=0,0,0
ANPE,ENPE,RNPE=0,0,0
saver = tf.train.Saver()
model_path = config.model_path_local

if not config.fresh_train:
    load_path = saver.restore(ag.sess, model_path)
else:
    with open(config.record_batch_file_local,"w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ANPB","ENPB","RNPB"])
    with open(config.record_episode_file_local,"w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["ANPE","ENPE","RNPE","actions_per_ep","reward_per_ep"])
while episode_number<total_episodes:
    env=atest.Q
    obs=np.reshape(atest.linkFilter(env),[1,ag.nx])
    batch_avg=[]
    reward_in_ep=[]
    action_type=''
    action_nums=0
    while action_type!='D':
    #while batch_number<10:
        action_nums+=1
        xs.append(obs)
        pre_val,ols=atest.eval_Ques(obs)
        act=ag.rollaction(obs)[0][0]
        #act=act if np.random.uniform()<float(episode_number)/total_episodes else np.random.randint(0,ag.ny-1)
        act=act if np.random.uniform()<epslon else np.random.randint(0,ag.ny-1)
        ys.append(act)
        act-=(nodes-hostnum)
        action_type,imm_reward=atest.pre_eval_action(act)
        if action_type=='A':
            ANPB+=1
            ANPE+=1
            atest.action(act)
            if atest.check_connect():
                ENPB+=1
                ENPE+=1
                env=atest.Q 
                obs=np.reshape(atest.linkFilter(env),[1,ag.nx])  # update enviroment(observation)
                vs,ols=atest.eval_Ques(obs)
                reward=vs-pre_val
                if reward>0:
                    RNPE+=1
                    RNPB+=1
            else:
                atest.action(-act)
                reward=config.disconnect_punish
            rs.append(reward)
            reward_in_ep.append(reward)
        else:
            rs.append(imm_reward)
            reward_in_ep.append(imm_reward)
        if  len(rs)>=batch_size:
            batch_avg.append(np.mean(rs))
            batch_sum+=1
            plt_ANPB.append(ANPB)
            plt_ENPB.append(ENPB)
            plt_RNPB.append(RNPB)
            with open(config.record_batch_file_local,"a") as csvfile:
                writer = csv.writer(csvfile)
                #writer.writerow(["ANPB","ENPB","RNPB"])
                writer.writerow([ANPB,ENPB,RNPB])
            ANPB,ENPB,RNPB=0,0,0
            epx = np.vstack(xs)
            epy = np.vstack(ys)
            epr = np.vstack(rs)
            plt_rb.append(np.mean(epr))    
            xs,ys,rs=[],[],[]
            
            tgrad=ag.calGrad(epx, epy, epr)
            if config.show_batch:
                print("upgrade with batch ",len(batch_avg)," ,in episode ",episode_number,"avg_reward=",batch_avg[-1])
            for ix,grad in enumerate(tgrad):
                gradBuffer[ix] += grad  
                ag.applyGrad(gradBuffer)
                for ix,grad in enumerate(gradBuffer):
                    gradBuffer[ix] = grad * 0
            save_path = saver.save(ag.sess, model_path)
    plt_ANPE.append(ANPE)
    plt_ENPE.append(ENPE)
    plt_RNPE.append(RNPE)
    plt_ae.append(action_nums)
    if len(reward_in_ep)>0:
        plt_re.append(np.mean(reward_in_ep))
    else: 
        plt_re.append(0)
    if config.show_episode:
        print"end of episode-- ",episode_number,"  average reward=",plt_re[-1]
    with open(config.record_episode_file_local,"a") as csvfile:
        writer = csv.writer(csvfile)
        #writer.writerow(["ANPE","ENPE","RNPE","actions_per_ep","reward_per_ep"])
        writer.writerow([ANPE,ENPE,RNPE,action_nums,np.mean(reward_in_ep)])
    ANPE,ENPE,RNPE=0,0,0
    episode_number+=1
    atest.initial()
    
draws(plt_ANPB)
draws(plt_ENPB)
draws(plt_RNPB)

draws(plt_ANPE)
draws(plt_ENPE)
draws(plt_RNPE)

draws(xishu(plt_ae))
draws(xishu(plt_rb))
draws(xishu(plt_re))
'''
with open("large4.csv","w") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["ANPB","ENPB","RNPB","ANPE","ENPE","RNPE","be","rb","re"])
    writer.writerows([plt_ANPB,plt_ENPB,plt_RNPB,plt_ANPE,plt_ENPE,plt_RNPE,plt_ae,plt_rb,plt_re])
with open("largexs4.csv","w") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["ANPB","ENPB","RNPB","ANPE","ENPE","RNPE","be","rb","re"])
    writer.writerows([xishu(plt_ANPB),xishu(plt_ENPB),xishu(plt_RNPB),xishu(plt_ANPE),xishu(plt_ENPE),xishu(plt_RNPE),xishu(plt_be),xishu(plt_rb),xishu(plt_re)])
'''
action_type='X'
env=atest.Q
obs=np.reshape(atest.linkFilter(env),[1,ag.nx])
action_num=0
print" ------start your action!------"
while action_type!='D' and action_num<10:      
        xs.append(obs)
        pre_val=atest.eval_Ques(obs)
        act=ag.rollaction(obs)[0][0]
        ys.append(act)
        act-=nodes-hostnum
        action_num+=1
        print("action",action_num,':',act)
        action_type,imm_reward=atest.pre_eval_action(act)
        if action_type=='A':
            atest.action(act)
            if atest.check_connect():
                env=atest.Q
                obs=np.reshape(atest.linkFilter(env),[1,ag.nx])  # update enviroment(observation)
                reward=atest.eval_Ques(obs)-pre_val
                rs.append(reward)
                if reward>0:
                    RNPB+=1
            else:
                atest.action(-act)
                reward=-2
                rs.append(reward)
        else:
            rs.append(imm_reward)