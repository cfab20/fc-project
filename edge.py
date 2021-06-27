import time
import random
import sys
import zmq
import json
import datetime
import threading
import os

DEVICES_PORT = 5555
CLOUD_PORT = 5556
CLOUD_HEARTBEAT_PORT = 5557
CLOUD_IP = "localhost"


class Edge:

    def __init__(self):
        self.device_data = {}
        self.send_to_cloud_interval = 5 # buffer time in sec
        self.data_to_cloud = []
        self.sending_to_cloud = False
        self.cached_data_file = "cached_data.txt"

    def save_data_to_file(self, data):
        with open(self.cached_data_file, 'w') as file:
            file.write(json.dumps(data))
    
    def append_cached_data(self, data):
        cached_data = None
        with open(self.cached_data_file, 'r') as file:
            cached_data = json.load(file)
        for key, value in cached_data.items():
            if key in data:
                data[key] += value 

        open(self.cached_data_file, 'w').close()
        return data
    
    def cached_data_size(self):
        return os.stat(self.cached_data_file).st_size 
       
    def get_device_data(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.bind("tcp://*:%s" % DEVICES_PORT)

        socket.subscribe("") # subscribe to all topics

        start = datetime.datetime.now()
        while True:
            if (datetime.datetime.now() - start).total_seconds() > self.send_to_cloud_interval and not self.sending_to_cloud:
                res = self.check_heartbeat()
                start = datetime.datetime.now()

                if res:
                    # TODO check for cached data and append to self.device_data
                    if self.cached_data_size() > 0:
                        self.device_data = self.append_cached_data(self.device_data)
                        print("Appended Cached Data")

                    self.data_to_cloud.append(self.device_data)
                    start = datetime.datetime.now()
                    self.sending_to_cloud = True
                    self.device_data = {}
                else:
                    print("save data locally")
                    self.save_data_to_file(self.device_data)
                    # TODO save data to local files -> max 10 MB

            topic, data = socket.recv_multipart()
            topic = topic.decode()
            data = json.loads(data)

            if topic not in self.device_data:
                self.device_data[topic] = []
            self.device_data[topic].append(data)

            # print("TOPIC: {}; DATA: {}".format(topic, data))
            time.sleep(0.001)

    def check_heartbeat(self):
        time_out = 1000  # ms
        context2 = zmq.Context()
        socket2 = context2.socket(zmq.REQ)
        socket2.connect("tcp://" + CLOUD_IP + ":%s" % CLOUD_HEARTBEAT_PORT)
        socket2.setsockopt(zmq.LINGER, 0)
        socket2.setsockopt(zmq.RCVTIMEO, time_out)
        res = False
        try:
            heartbeat_msg = "hi there".encode()
            socket2.send(heartbeat_msg)
            socket2.recv()
            res = True
        except zmq.error.Again:
            print('cloud not available')
            socket2.close()
        return res


    def send_data_to_cloud(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.connect("tcp://" + CLOUD_IP + ":%s" % CLOUD_PORT)

        while True:
            while self.sending_to_cloud:                  
                print("SENDING TO CLOUD")                    
                for batch in self.data_to_cloud:
                    for key, values in batch.items():
                        for value in values:
                            multipart_msg = [key.encode(), json.dumps(value).encode()]
                            socket.send_multipart(multipart_msg)                            

                self.data_to_cloud = []
                self.sending_to_cloud = False
            time.sleep(0.001)
    
    def run(self):
#        th_from_devices = threading.Thread(target=self.get_device_data)
        th_to_cloud = threading.Thread(target=self.send_data_to_cloud)

 #       th_from_devices.start()
        th_to_cloud.start()

edge = Edge()
edge.run()
edge.get_device_data()
# edge.check_heartbeat()

    