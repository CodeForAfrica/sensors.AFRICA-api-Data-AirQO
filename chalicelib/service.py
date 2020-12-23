import boto3
import json
import pickle
import requests

from chalicelib.sensorafrica import (
    get_sensors_africa_locations,
    get_sensors_africa_nodes,
    get_sensors_africa_sensor_types,
    get_sensors_africa_sensors,
    post_location, 
    post_node,
    post_node,
    post_sensor,
    post_sensor_data,
    post_sensor_type, )

from chalicelib.settings import S3_BUCKET_NAME, S3_OBJECT_KEY, OWNER_ID
from chalicelib.utils import address_converter

from time import sleep

def get_airqo_node_sensors_data(node_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"}
    response = requests.get(url="https://thingspeak.com/channels/{}/feeds.json".format(node_id), headers=headers)
    if not response.ok:
        raise Exception(response.reason)
    return response.json()


def run(app):
    locations = get_sensors_africa_locations()
    nodes = get_sensors_africa_nodes()
    sensors = get_sensors_africa_sensors()
    sensor_types = get_sensors_africa_sensor_types()

    session = boto3.session.Session(region_name="eu-west-1")
    s3client = session.client("s3")

    try:
        response = s3client.get_object(Bucket=S3_BUCKET_NAME, Key=S3_OBJECT_KEY)
        body = response['Body'].read()
        channel_last_entry_dict = pickle.loads(body)
    except:
        channel_last_entry_dict = dict()
   
    with open("chalicelib/channels.json") as data:
        channels = json.load(data)

        for channel in channels:
            channel_data = get_airqo_node_sensors_data(channel["id"])

            #if channel id key does not exist in the map dict initiate it with 0
            if not channel["id"] in channel_last_entry_dict:
                channel_last_entry_dict[channel["id"]] = 0

            last_entry = channel_last_entry_dict[channel["id"]]

            if channel_data and channel_data["channel"]["last_entry_id"] > last_entry:
                lat_log = f'{channel["latitude"]}, {channel["longitude"]}'
                address = address_converter(lat_log)
                
                location = [loc.get(lat_log) for loc in locations if loc.get(lat_log)]
                if location:
                    location = location[0]
                else:
                    location = post_location({
                        "location": address.get("display_name"),
                        "latitude": channel["latitude"],
                        "longitude": channel["longitude"],
                        "country": address.get("country"),
                        "postalcode": address.get("postcode")
                    })

                #post node objects if it does not exist
                airqo_node = [node.get("id") for node in nodes if node.get('uid') == str(channel["id"])]
                if airqo_node:
                    airqo_node = airqo_node[0]
                else:
                    airqo_node = post_node(node={"uid": channel["id"], 'owner': int(OWNER_ID), 'location': location})

                # aiqo channel result has 4 sensors data that we need
                # field1- Sensor1 PM2.5_CF_1_ug/m3, 
                # field2 -Sensor1 PM10_CF_1_ug/m3, 
                # field3 - Sensor2PM2.5_CF_1_ug/m3, 
                # field4 - Sensor2 PM10_CF_1_ug/m3
                sensor_type = [s_type.get("id") for s_type in sensor_types if s_type.get("uid") == "PMS5003"]
                if sensor_type:
                    sensor_type = sensor_type[0]
                else:
                    sensor_type = post_sensor_type({ "uid": "pms5003","name": "PMS5003","manufacturer": "PlanTower" })
  
                value_type = ["P2", "P1", "P2", "P1"]
                for i in range (1, 5):
                    sensor_id = post_sensor({
                        "node": airqo_node,
                        "pin": str(i),
                        "descriptiion": "",
                        "sensor_type": sensor_type,
                        "public": False
                    })
                    
                    for feed in channel_data["feeds"]:
                        if feed["entry_id"] > last_entry:
                            sensor_data_values = [{
                                    "value": float(feed["field{}".format(str(i))]),
                                    "value_type": value_type[i-1]
                                }]

                            post_sensor_data({ 
                                "sensordatavalues": sensor_data_values, 
                                "timestamp": feed["created_at"]
                                }, channel["id"], str(i))
                
                #update pickle variable               
                channel_last_entry_dict[channel["id"]] = channel_data["channel"]["last_entry_id"]
                s3client.put_object(Body=pickle.dumps(channel_last_entry_dict), Bucket=S3_BUCKET_NAME, Key=S3_OBJECT_KEY)
            else:
                app.log.warn("Channel feed - %s missing or not updated", channel["id"])

            sleep(30)
