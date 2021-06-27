import json
import time
import random
import sys
import zmq
import threading
import datetime

from google.cloud import bigtable
from google.cloud.bigtable import column_family
from google.cloud.bigtable import row_filters
from google.cloud.bigtable.row_set import RowSet

PORT = 5556
HEARTBEAT_PORT = 5557

SENSOR_DATATYPES = ["position", "velocity", "temperature"]

def write_db(key, data):
    client = bigtable.Client(project="adsp-302713", admin=True)
    instance = client.instance("tf-instance")
    table = instance.table("sensor_values")

    timestamp = data["timestamp"]
    gcp_timestamp = datetime.datetime.now()
    curr_datatype = None 
    sensor_name = key

    for datatype in SENSOR_DATATYPES:
        if datatype in data:
            curr_datatype = datatype
            break
    sensor_data = data[curr_datatype]

    row_key = sensor_name + "#" + timestamp
    row = table.direct_row(row_key)
    if curr_datatype in ["position", "velocity"]:
        row.set_cell (
            curr_datatype, 
            "x", 
            str(data[curr_datatype]["x"]), 
            gcp_timestamp
        )
        row.set_cell (
            curr_datatype, 
            "y", 
            str(data[curr_datatype]["y"]), 
            gcp_timestamp
        )
        row.set_cell (
            curr_datatype, 
            "z", 
            str(data[curr_datatype]["z"]), 
            gcp_timestamp
        )
    elif curr_datatype in ["temperature"]:
        row.set_cell (
            curr_datatype,
            "temperature",
            str(data[curr_datatype]),
            gcp_timestamp
        )
    else:
        print("ERROR")

    row.commit()
    print('Successfully wrote row {}.'.format(row_key))

def read_prefix(project_id, instance_id, table_id, prefix):
    client = bigtable.Client(project=project_id, admin=True)
    instance = client.instance(instance_id)
    table = instance.table(table_id)

    end_key = prefix[:-1] + chr(ord(prefix[-1]) + 1)

    row_set = RowSet()
    row_set.add_row_range_from_keys(prefix.encode("utf-8"), end_key.encode("utf-8"))

    rows = table.read_rows(row_set=row_set)
    for row in rows:
        print_row(row)


def print_row(row):
    print("Reading data for {}:".format(row.row_key.decode('utf-8')))
    
    for cf, cols in sorted(row.cells.items()):
        print("Column Family {}".format(cf))
        for col, cells in sorted(cols.items()):
            for cell in cells:
                labels = " [{}]".format(",".join(cell.labels)) \
                    if len(cell.labels) else ""
                print(
                    "\t{}: {} @{}{}".format(col.decode('utf-8'),
                                            cell.value,
                                            cell.timestamp, labels))
    print("")


def check_heartbeat():
    while True:
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        try:
            socket.bind("tcp://*:%s" % HEARTBEAT_PORT)
        except zmq.error.ZMQError:
            pass
        data = socket.recv() 
        socket.send("general kenobi".encode())
        socket.close()
        time.sleep(0.001)
        

def get_data_from_edge():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.bind("tcp://*:%s" % PORT)

    socket.subscribe("") # subscribe to all topics
    
    while True:
        topic, data = socket.recv_multipart()
        topic = topic.decode()
        data = data.decode()
        
        data = json.loads(data)
        write_db(topic, data)
        print("TOPIC: {}; DATA: {}".format(topic, data))
        time.sleep(0.001)


heartbeat = threading.Thread(target=check_heartbeat)
heartbeat.start()

get_data_from_edge()

# write_simple("adsp-302713", "tf-instance", "sensor_values")
# read_prefix("adsp-302713", "tf-instance", "sensor_values", "robot_2#")
