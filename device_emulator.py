import json 
import zmq
import datetime
import random
import time
import threading

DEVICE_CONNCECTIONS_FILE = "device_connections.json"
PORT = 5555

def get_device_connections():
    data = None
    with open(DEVICE_CONNCECTIONS_FILE, "r") as f:
        data = json.load(f)
    return data

def get_data(schema):
    data = {}
    for data_type in schema.split(","):
        if data_type == "timestamp":
            data["timestamp"] = datetime.datetime.now()
        elif data_type == "temperature":
            data["temperature"] = random.randrange(-200, 400)
        elif data_type == "position":
            data["position"] = {
                "x": random.randrange(-1000, 1000),
                "y": random.randrange(-1000, 1000),
                "z": random.randrange(0, 10)
            }
        elif data_type == "velocity":
            data["velocity"] = {
                "x": random.randrange(-100, 100),
                "y": random.randrange(-100, 100),
                "z": random.randrange(0, 10)
            }
    return json.dumps(data).encode()


def start_device(topic, msgs_per_min, schema):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect("tcp://127.0.0.1:%s" % PORT)

    while True:
        json_data = get_data(schema)        
        multipart_msg = [str(topic).encode(), json_data]
        socket.send_multipart(multipart_msg)
        print("sent: {}".format(multipart_msg))
        time.sleep(60 / msgs_per_min)


def emulate():
    device_connections = get_device_connections()
    for device in device_connections["devices"]:
        topic = device["topic"]
        msgs_per_min = device["msgs-per-min"]
        schema = device["schema"]
        
        curr_thread = threading.Thread(target=start_device, args=(topic, msgs_per_min, schema))
        curr_thread.start()

emulate()

    
