import json
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

from chalicelib.settings import OWNER_ID
from chalicelib.utils import address_converter


def get_airqo_node_sensors_data(node_id):
    response = requests.get("https://thingspeak.com/channels/{}/feeds.json".format(node_id))
    if not response.ok:
        raise Exception(response.reason)
    return response.json()


def run(app):
    locations = get_sensors_africa_locations()
    nodes = get_sensors_africa_nodes()
    sensors = get_sensors_africa_sensors()
    sensor_types = get_sensors_africa_sensor_types()

    with open("chalicelib/channels.json") as data:
        channels = json.load(data)

        for channel in channels:
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
                airqo_node = post_node(node={"uid": channel["id"], 'owner': OWNER_ID, 'location': location})


            channel_data = get_airqo_node_sensors_data(channel["id"])
            # aiqo channel result has 4 sensors data that we need
            # field1- Sensor1 PM2.5_CF_1_ug/m3, 
            # field2 -Sensor1 PM10_CF_1_ug/m3, 
            # field3 - Sensor2PM2.5_CF_1_ug/m3, 
            # field4 - Sensor2 PM10_CF_1_ug/m3
            if channel_data:
                sensor_type = [s_type.get("id") for s_type in sensor_types if s_type.get("name") == "pms5003"]
                if sensor_type:
                    sensor_type = sensor_type[0]
                else:
                    sensor_type = post_sensor_type({ "uid": "PMS5003","name": "pms5003","manufacturer": "PlanTower" })
  
                value_type = ["P2", "P1", "P2", "P1"]
                for i in range (1, 5):
                    sensor_id = post_sensor({
                        "node": airqo_node,
                        "pin": str(i),
                        "descriptiion": "",
                        "sensor_type": sensor_type,
                        "public": True
                    })
                    
                    for feed in channel_data["feeds"]:
                        sensor_data_values = [{
                                "value": float(feed["field{}".format(str(i))]),
                                "value_type": value_type[i-1]
                            }]

                        post_sensor_data({ 
                            "sensordatavalues": sensor_data_values, 
                            "timestamp": feed["created_at"]
                            }, channel["id"], str(i))
            else:
                app.log.warn("Channel feed - %s missing", channel["id"])
