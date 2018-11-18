#!/usr/bin/env python2
# -*- coding:utf-8 -*-

from flask import Flask, jsonify, request
import logging
import os

from controller.ctrl import Ctrl
from controller.utils.utils import Utils


app = Flask(__name__)

ctx = app.app_context()
ctx.push()

Flask.ctrl = None


@app.route('/')
def index():
    """
    A sample index page
    """
    return 'hello, this is house little gray project'


@app.route('/init', methods=['POST'])
def init():
    """
    Initalize the controller and start the network

    :param graph: the network topology
    :param hosts: the hosts linked to switch
    :returns: JSONify success
    """
    para = request.get_json()
    print(para)
    graph = para['graph']
    Utils.graphConverter(graph)
    hostList = para['hosts']
    Flask.ctrl = Ctrl(graph, hostList)
    ret = Flask.ctrl.start()
    return jsonify({'success': ret})


@app.route('/update', methods=['POST'])
def update():
    """
    Update the switch status

    :param action: open/close a switch
    :param traversePath: the paths for traverse INT packet
    :returns: JSONify success and reward matrix
    """
    para = request.get_json()
    print(para)
    action = para['action']
    if 'traversePath' in para:
        traversePath = para['traversePath']
    else:
        traversePath = False
    if 'counter' in para:
        counter = para['counter']
    else:
        counter = False
    if 'times' in para:
        times = para['times']
    else:
        times = None
    ret = Flask.ctrl.update(
        action=action, paths=traversePath, counter=counter, times=times)
    return jsonify({
        'success': True,
        'rewardMatrix': ret
    })


@app.route('/reset', methods=['GET'])
def reset():
    """
    Reset the switch staus in the network

    :returns: JSONify success
    """
    ret = Flask.ctrl.reset()
    # ret = Flask.ctrl.start()
    return jsonify({
        'success': ret
    })


@app.route('/get_counter', methods=['GET'])
def getCounter():
    print('get counters')
    counters = Flask.ctrl.getPacketCount()
    return jsonify({
        'ingressCounter': counters[0],
        'egressCounter': counters[1]
    })


@app.route('/test', methods=['GET'])
def doTest():
    """
    Just a test method
    """
    Flask.ctrl.sendTestInfo()
    return jsonify({'success': True})


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
        filename='controller/logs/controller.log',
        filemode='a')

    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
