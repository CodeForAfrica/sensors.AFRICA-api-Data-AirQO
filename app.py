import json
import settings
import requests

from chalice import Chalice
from settings import SENSORS_AFRICA_API, SENSORS_AFRICA_API_KEY, OWNER_ID
from utils import address_converter

app = Chalice(app_name='sensors-africa-airqo')
app.debug = True

@app.route('/')
def index():
    return {'hello': 'world'}

def post_node(node):
    response = requests.post(f"{SENSORS_AFRICA_API}/nodes/",
    data=node,
    headers={"Authorization": f"Token {SENSORS_AFRICA_API_KEY}"})
    return

def post_location(location):
    response = requests.post(f"{SENSORS_AFRICA_API}/locations/",
    data=location,
    headers={"Authorization": f"Token {SENSORS_AFRICA_API_KEY}"})
    if response.ok:
        return response.json()['id']

def post_sensor(sensor):
    response = requests.post(f"{SENSORS_AFRICA_API}/sensors/",
    data=sensor,
    headers={"Authorization": f"Token {SENSORS_AFRICA_API_KEY}"})
    return

def post_sensor_type(sensor_type):
    response = requests.post(f"{SENSORS_AFRICA_API}/sensor_types/",
    data=sensor_type,
    headers={"Authorization": f"Token {SENSORS_AFRICA_API_KEY}"})
    if response.ok:
        return response.json()['id']

def get_sensors_africa_nodes():
    response = requests.get(f"{SENSORS_AFRICA_API}/nodes/")
    if response.ok:
        return [res['node']['uid'] for res in response.json()]
    return []

def get_sensors_africa_locations():
    response = requests.get(f"{SENSORS_AFRICA_API}/locations/", headers={"Authorization": f"Token {SENSORS_AFRICA_API_KEY}"})
    if response.ok:
        """
            Using latitude, longitude as a key and location id as value to help us find already existing location latter without having to ping the server
            Using round ensures latitude, longitude value will be the same as lat_log in the run method.
        """
        formated_response = [{f'{round(float(location["latitude"]), 3)}, {round(float(location["longitude"]), 3)}':
                            f'{location["id"]}'} for location in response.json() if location["latitude"] and location["longitude"]]

        return formated_response
    return []


def get_airqo_node_sensors(node_id):
    response = requests.get("https://thingspeak.com/channels/{}/feeds.json".format(node_id))
    if response.ok:
        result = response.json()
        post_sensor({
            "node": node_id,
            "pin": "-",
            "sensor_type": "PMS5003",
            "public": True 
        })

    return []

nodes = get_sensors_africa_nodes()
locations = get_sensors_africa_locations()

with open("./channels.json") as data:
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

        post_node(node={"uid": channel["id"], 'owner': OWNER_ID, 'location': location})