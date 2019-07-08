# Power-Aware Traffic Engineering with Deep Reinforcement Learning

Power-aware traffic engineering via coordinated sleeping is often formulated into MIP problems, which are generally NP-Hard thus the computation time does not scale for large networks, causing delayed control decision making for highly dynamic networks. Motivated by recent advances in deep reinforcement learning (RL), we consider building intelligent systems that learn to adaptively change router's power state according to traffic dynamics. The forward propagation property of neural networks can greatly speedup power on/off decision making. Typically, conducting RL requires a learning agent to iteratively explore and perform the ``good'' actions based on the feedbacks from the environment. However, state-of-the-art monitoring techniques fail to achieve timely network-wide feedbacks. By coupling recent techniques of SDN (for performing actions to the environment) and INT (for collecting environment feedbacks), we craft GreenTE.ai, a closed-loop control system. Based on the system, we propose novel techniques to enhance the learning ability. Compared with classic approaches, our proposal is generalized, time-efficient and environment-adaptive. It generates a reasonable power saving action within 276ms considering both energy efficiency and network load balancing.

GreenTE.ai's training process is built upon a closed-loop traffic control system, where the actions of powering on/off selected routers are equally translated into network topology changes and route updates by modifying flow tables, while the real-time network environment feedbacks (i.e., link congestion status) are collected via In-band Network-Wide Telemetry (INWT), a novel network-wide monitoring mechanism based on the recently proposed In-band Network Telemetry (INT).

The architecture of the proposed closed-loop control/training system consists of an RL agent, a centralized controller and switches/hosts in the data plane. The RL agent embeds the intelligence for automatically managing the power states of data plane devices. The controller is responsible for translating actions from the RL agent into network operations and feeding the resulting network-wide traffic status as well as the calculated reward back to the agent. The data plane implements traffic generation, traffic forwarding and network-wide telemetry functionalities. The system follows the classic client-server model to mimic the interaction between the agent and the environment. The RL agent and the controller act as the client and the server, respectively. The communication between the two sides is based on HTTP with a JSON format. More specifically, the actions from the agent are carried by HTTP Requests while the rewards from the environment are encapsulated in HTTP Responses.

The RL agent consists of four main functional modules including Neural Network, Graph Representation, Training Logic and Communication Channel. The Neural Network consists of multiple computation layers and can be regarded as a sophisticated mathematical function that maps a given input (e.g., current environment state) to a desired output (e.g., device on/off action). The Graph Representation maintains the same network topology as well as device power states with the data plane. This topology image is mainly used to verify the correctness of the generated actions, preventing AI from generating device on/off actions that will break the connectivity of the underlying network graph. The Training Logic is responsible for conducting the closed-loop training step by step and updating the Neural Network in batch. The Communication Channel maintains an HTTP connection with the controller for exchanging messages during the closed-loop training.

There are a number of services residing on the controller. Among them, Network Topology Maintainer parses the power on/off actions sent from the RL agent and keeps the topology up to date; Mininet Network Generator is responsible for data plane initialization (we do not build a real hardware-based network testbed; instead, we leverage Linux network namespace to virtualize a number of hosts and switches in the data plane); OSPF-ECMP Calculator conducts route updates after topology changes and modifies flow tables via Flow Table Installer; SR-INT Path Planner adds source routing information into INT probes to guide the probes to monitor every edge of the network graph (for collecting complete feedbacks from the environment); a database is also maintained to collect the network-wide telemetry data, which will be further calculated by a reward function.

The data plane consists of end hosts, software P4 switches (BMv2), and an Open vSwitch (OVS). Among them, the end hosts are responsible for (a) generating background traffic for training and testing, (b) generating INT probes for link status monitoring and (c) collecting/parsing INT probes and writing telemetry results into the database; the P4 switches forward the background traffic as well as the INT probes (we leverage the protocol-independent forwarding capability of the P4 switches to enable ECMP-like load balancing and customized processing of the INT probes); the OVS is used to reserve a separate communication channel between the controller and the data plane for safely passing control messages. In this way, the collected telemetry data can have a dedicated backhaul communication channel to the database. Actually, all the data plane components are controlled in an out-of-band mode to keep the critical control messages uninterrupted by the background traffic. For example, the controller speaks with BMv2 using Apache Thrift to enforce forwarding rules; the controller sends calculated INT probing paths to the end hosts and reads telemetry results from the database via sockets (all the end hosts are connected with OVS).

# Demo GUI

![GUI of GreenTE.ai](https://github.com/graytower/greente_ai/blob/master/telemetry%2Bpowersaving.PNG)

# System

It contains P4 controller(`System/controller/`), P4 program(`System/p4app/`), and INT packet sender&receiver(`System/packet/`).

### app.py

The entry of the project. It start a flask server,receive instruction from AI agent, and call controller module（`System/controller/ctrl.py`）.

## p4app

Include p4 source code, implemented source-based INT functrion.

header.p4, parser.p4, app.p4: p4 source code

### header.p4

Including Headers and Metadatas

### parser.p4

Including parser, deparser and checksum calculator.

### app.p4

The main part of the p4 program. Including SR/INT/ARPProxy/UDP/ECMP tables.

### app.json

The json file that compiled from app.p4 by p4c compiler.

## packet:

Send & receive INT packet module which run in the hosts and the database config.

Send & receive background pakcets to each host in network.

### int_data.sql

The SQL Table which is used to initalize the database.

### receiveint.c

Used to receive int packet, and parse them, then put them into database.

### sendint.py

Use the given traverse path generate the INT packet and encode SR info.

### packetClient.py

Send background packet from each host to each host with a certain strategy.

## controller

Generate Mininet network, send SR & INT command to hosts and get result from database.

### ctrl.py

The main controller. Use topoGraph and hostList generate netwrok, then use path to traverse the netwrok and collect INT info.

### dbParser.py

The module which is used in app.py to get INT info from database.

### device.py

The module which is used in app.py to generate the virtual devices(Hosts/Switches).

### p4_mininet.py

The module which is used in mininiet to generate P4 devices.

### switchRuntime.py

The module which is used in app.py to down tables using thrift RPC.

### topoMaker.py

The module which is used in app.py to generate network topo.

# DFS-based path planning algorithm

## dfls.py

_DFLS()_ is INT path planning algorithm based on DFS.

_createTopo()_ can create topologies randomly.

# AI Agent

## config.py

Training parameters configuration. Such as the model path, fresh train, training hyper-parameters, the file path of record, etc.

## p4-ai-new.py

The main train file.

The entrance to run the training, and communicate with p4 controller and collect data. The training result models are stored in the path in configuration file.

## p4_ai_local.py

The main static train file.

The entrance to run the training, and not commuciate with the P4 controller.

## RLAgent.py

The definition of the decision class.

## graph.py

The definition of graph class.

## httpConnec2.py

Comunication interface file.

## cmp_smartor.py

Compare with heuristic algorithm.

## cmp_random.py

Compare with random algorithm.

## genTopo.py

Generate topology.

# How to run controller

## Dependences

- p4c
- behavior-model
- python dependences (like flask, thrift, etc)
- mysql

If you installed the dependencies and configured the database successfully, then you can run the system with commands below

```
cd System/controller/
python app.py
```

Then you can run open another console, and run `python AI/Agent/P4_AI_new.py`.
