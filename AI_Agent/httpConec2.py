import requests
import json
import time
import config
# from check import rsp
ipp=config.p4_ip
reqs=requests.Session()
def sendact(action):
#     raw_input('pause action ...')
    if action==False:
        print"sending initial action=false"
    url="http://"+ipp+":80/update"
    payload={
        'action':action,
        'counter':True
        }
    payloadJson = json.dumps(payload)
    headers = {
    'content-type': "application/json"
    }
    def tryResp():
        try:
            response = requests.request("POST", url,data=payloadJson,headers=headers)
#             response = reqs.post(url,data=payloadJson,headers=headers)
            #print('response',response.content)
        except:
            print('network error...retry')
            time.sleep(2)
            response=tryResp()
        return response
    response=tryResp()
#     print('response2',response)

    rspobj=json.loads(response.content)['rewardMatrix']
    #print"ques from p4 platform:"
    #print rspobj
    return rspobj
    
def sendTopo(topo,host):
    url="http://"+ipp+":80/init"
    payload={
        'graph':topo,
        'hosts':host
        }
    headers = {
    'content-type': "application/json"
    }
    pldJson=json.dumps(payload)
    def tryResp():
        try:
            rsp=requests.request("POST",url,data=pldJson,headers=headers)
#             rsp = reqs.post(url,data=pldJson,headers=headers)
            
        except:
            print('network error...retry')
            time.sleep(2)
            rsp=tryResp()
        return rsp
    rsp=tryResp()   
    print"p4 platform in readiness."
    return rsp
def resetTopo():
    #raw_input('pause reset ...')
    url="http://"+ipp+":80/reset"
    def tryResp():
        try:
            rsp=requests.request("GET",url)
#             rsp= reqs.get(url)
        except:
            print('network error...retry')
            time.sleep(2)
            rsp=tryResp()
        return rsp
    rsp=tryResp()

    return rsp