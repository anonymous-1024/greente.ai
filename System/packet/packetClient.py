import threading
import socket
import random
import time
import math
import sys

threadsNum = 12
port = 3333
# ipList = ['10.0.0.101', '10.0.0.102', '10.0.0.104', '10.0.0.105']


class sendUdpThread(threading.Thread):
    """
    Send normal packet multithread via UDP
    """

    def __init__(self, dstHost):
        """
        Initialization

        :param dstHost: a destination host IP address list
        """
        threading.Thread.__init__(self)
        self.dstHost = dstHost

    def sendUdp(self, dstip, t0, typew, argu, duration):
        """
        Send UDP packet using kinds of methods and kinds of arguments

        :param dstip: destination IP address
        :param others: arguments for method
        """
        socketLink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        t1 = time.time()
        if typew == 'uniform':
            while (time.time() - t1) < duration:
                k = argu / t0
                socketLink.sendto(b'dddddddd', (dstip, port))
                # time.sleep(0.001 / k)
                time.sleep(0.0005)
                # time.sleep(0.1)
        if typew == 'uniform2':
            # speeds = [200, 400, 600, 800, 1000]
            # speeds = [100, 500, 900, 1300, 1700]
            speeds = [100, 500, 900, 1300, 1700]
            speed = random.sample(speeds, 1)[0]
            randFactor = random.randint(-50, 50)
            speed += randFactor
            while (time.time() - t1) < duration:
                socketLink.sendto(b'dddddddd', (dstip, port))
                durTime = 1.0/speed
                time.sleep(durTime)
        elif typew == 'sin':
            while (time.time() - t1) < duration:
                socketLink.sendto(b'dddddddd', (dstip, port))
                time.sleep(2 * t0 / (1 + math.sin(argu * time.time())))
        elif typew == 'poisson':
            while (time.time() - t1) < duration:
                socketLink.sendto(b'dddddddd', (dstip, port))
                # dt = random.expovariate(0.12)
                dt = random.expovariate(0.4)
                time.sleep(0.001 * dt)
        else:
            print('invalid type of sending udp')

    def voidfun(self, duration):
        """
        Nothing to do
        """
        time.sleep(duration)

    def run(self):
        """
        Random choose a host and send normal UDP packet 
        """
        funChoice = 1
        while True:
            dstip = random.choice(self.dstHost)
            # funChoice = random.randint(0, 2)
            # if funChoice != 0:
            print('start func')
                # print('send udp to ' + dstip)

                # self.sendUdp(dstip=dstip, t0=10, typew='uniform',
                #              argu=50, duration=10000)

                # new packet send pattern
            self.sendUdp(dstip=dstip, t0=10, typew='uniform2',
                            argu=50, duration=20)

                # self.sendUdp(dstip=dstip, t0=10, typew='poisson',
                #  argu=50, duration=10000)

                # self.sendUdp(dstip=dstip, t0=10, typew='poisson',
                #              argu=50, duration=2)
                # funChoice = 0
            # else:
            #     print('void func')
            #     self.voidfun(duration=4)
            #     funChoice = 1


if __name__ == '__main__':
    print('program start')
    ipList = sys.argv[1:]
    hostNum = len(ipList)
    threadsIpList = []
    # ipList is divided equally into threadsIpList.
    # Length of threadsIpList is threadsNum. Element of threadsIpList is List.
    # The remainder of ipList is assigned to front of threadsIpList.
    if hostNum <= threadsNum:
        for x in ipList:
            ip = []
            ip.append(x)
            threadsIpList.append(ip)
        for i in range(threadsNum - hostNum):
            threadsIpList.append(None)
    else:
        avg = hostNum / threadsNum
        remain = hostNum % threadsNum
        for x in range(threadsNum):
            ip = ipList[x * avg:(x + 1) * avg]
            threadsIpList.append(ip)
        for i in range(remain):
            threadsIpList[i].append(ipList[threadsNum * avg + i])

    threadList = []
    for dstHost in threadsIpList:
        if dstHost is not None:
            t = sendUdpThread(dstHost)
            threadList.append(t)
    for t in threadList:
        print('start a thread')
        t.start()
    for t in threadList:
        t.join()
