import time
import random
import sys
import zmq
import json
import datetime
import threading

DEVICES_PORT = 5555
CLOUD_PORT = 5556


class Edge:

    def __init__(self):
        self.device_data = {}
        self.send_to_cloud_interval = 5 # buffer time in sec
        self.data_to_cloud = []
        self.sending_to_cloud = False

    def get_device_data(self):
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.bind("tcp://127.0.0.1:%s" % DEVICES_PORT)

        socket.subscribe("") # subscribe to all topics

        start = datetime.datetime.now()
        while True:
            if (datetime.datetime.now() - start).total_seconds() > self.send_to_cloud_interval and not self.sending_to_cloud:
                self.data_to_cloud.append(self.device_data)
                start = datetime.datetime.now()
                self.sending_to_cloud = True

            topic, data = socket.recv_multipart()
            topic = topic.decode()
            data = json.loads(data)

            if topic not in self.device_data:
                self.device_data[topic] = []
            self.device_data[topic].append(data)

            # print("TOPIC: {}; DATA: {}".format(topic, data))
            time.sleep(0.001)

    def send_data_to_cloud(self):
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.connect("tcp://127.0.0.1:%s" % CLOUD_PORT)

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
        th_from_devices = threading.Thread(target=self.get_device_data)
        th_to_cloud = threading.Thread(target=self.send_data_to_cloud)

        th_from_devices.start()
        th_to_cloud.start()

edge = Edge()
edge.run()

    