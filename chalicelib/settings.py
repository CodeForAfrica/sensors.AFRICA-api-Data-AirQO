import os

from dotenv import load_dotenv

load_dotenv()

SENSORS_AFRICA_API = os.environ.get("SENSORS_AFRICA_API", "http://127.0.0.1:8000")
SENSORS_AFRICA_AUTH_TOKEN = os.environ['SENSORS_AFRICA_AUTH_TOKEN']
SENSORS_AFRICA_USER = os.environ['SENSORS_AFRICA_USER']
SENSORS_AFRICA_PASSWORD = os.environ['SENSORS_AFRICA_PASSWORD']
OWNER_ID = os.environ['OWNER_ID']
