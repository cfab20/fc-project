import json
import time
import random
import sys
import zmq

PORT = 5556

def get_data_from_edge():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.bind("tcp://127.0.0.1:%s" % PORT)

    socket.subscribe("") # subscribe to all topics
    
    while True:
        topic, data = socket.recv_multipart()
        topic = topic.decode()
        data = json.loads(data)
        print("TOPIC: {}; DATA: {}".format(topic, data))
        time.sleep(0.001)

get_data_from_edge()
