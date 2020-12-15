import json
import requests

import settings
import utils

def post_node(node):
    response = requests.post(f"{settings.SENSORS_AFRICA_API}/v2/nodes/",
    data=node,
    headers={"Authorization": f"Token {Ssettings.ENSORS_AFRICA_AUTH_TOKEN}"})
    if response.ok:
        return response.json()['id']

def post_location(location):
    response = requests.post(f"{settings.SENSORS_AFRICA_API}/v2/locations/",
    data=location,
    headers={"Authorization": f"Token {settings.SENSORS_AFRICA_AUTH_TOKEN}"})
    if response.ok:
        return response.json()['id']

def post_sensor(sensor):
    response = requests.post(f"{settings.SENSORS_AFRICA_API}/v2/sensors/",
    data=sensor,
    headers={"Authorization": f"Token {settings.SENSORS_AFRICA_AUTH_TOKEN}"})
    return

def post_sensor_type(sensor_type):
    response = requests.post(f"{settings.SENSORS_AFRICA_API}/v2/sensor_types/",
    data=sensor_type,
    headers={"Authorization": f"Token {settings.SENSORS_AFRICA_AUTH_TOKEN}"})
    if response.ok:
        return response.json()['id']

def get_sensors_africa_nodes():
    response = requests.get(f"{settings.SENSORS_AFRICA_API}/v1/node/", auth=(settings.SENSORS_AFRICA_USER, settings.SENSORS_AFRICA_PASSWORD))
    if response.ok:
        return response.json()
    return []

def get_sensors_africa_locations():
    response = requests.get(f"{settings.SENSORS_AFRICA_API}/v2/locations/", headers={"Authorization": f"Token {settings.SENSORS_AFRICA_AUTH_TOKEN}"})
    if response.ok:
        """
            Using latitude, longitude as a key and location id as value to help us find already existing location latter without having to ping the server
            Using round ensures latitude, longitude value will be the same as lat_log in the run method.
        """
        formated_response = [{f'{round(float(location["latitude"]), 3)}, {round(float(location["longitude"]), 3)}':
                            f'{location["id"]}'} for location in response.json() if location["latitude"] and location["longitude"]]

        return formated_response
    return []


def get_airqo_node_sensors_data(node_id):
    response = requests.get("https://thingspeak.com/channels/{}/feeds.json".format(node_id))
    if response.ok:
        result = response.json()

    return []

#def run();
nodes = get_sensors_africa_nodes()
locations = get_sensors_africa_locations()

with open("./channels.json") as data:
    channels = json.load(data)

    for channel in channels:
        lat_log = f'{channel["latitude"]}, {channel["longitude"]}'
        address = utils.address_converter(lat_log)
        
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
            airqo_node = post_node(node={"uid": channel["id"], 'owner': settings.OWNER_ID, 'location': location})

        # aiqo channel result has 4 sensors data that we need
        # field1- Sensor1 PM2.5_CF_1_ug/m3, 
        # field2 -Sensor1 PM2.5_CF_1_ug/m3, 
        # field3 - Sensor2PM2.5_CF_1_ug/m3, 
        # field4 - Sensor2 PM10_CF_1_ug/m3
        for i in range (1, 5):
            post_sensor({
                "node": airqo_node,
                "pin": str(i),
                "descriptiion": "",
                "sensor_type": 1,
                "public": True
            })