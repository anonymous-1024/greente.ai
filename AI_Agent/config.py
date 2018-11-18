import genTopo

p4_ip = "127.0.0.1"
topo = genTopo.getShrotTopo()
# topo=genTopo.getDCtopo()

learning_rate = 0.0001
episodes = 512
batchsize = 32
maxQues = 7000
explore_rate = 0.9

record_batch_file = "traindata/record_batch_02.csv"
record_episode_file = "traindata/record_episode_02.csv"
model_path = "save/P4_AI/model2.ckpt"
fresh_train = True
# fresh_train=False
disconnect_punish = -2
overload_punish = 50
show_batch = False
show_episode = True

model_path_local = "/tmp/P4_AI/model2_local.ckpt"
record_batch_file_local = "traindata/record_batch_02_local.csv"
record_episode_file_local = "traindata/record_episode_02_local.csv"
record_smart_file = "traindata/record_smart.csv"
record_random_file = "traindata/record_random.csv"
runtime = 500
