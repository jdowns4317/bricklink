import requests
from requests_oauthlib import OAuth1
import time
import os

auth = OAuth1(
    os.getenv("BRICKLINK_CONSUMER_KEY"),
    os.getenv("BRICKLINK_CONSUMER_SECRET"),
    os.getenv("BRICKLINK_TOKEN_VALUE"),
    os.getenv("BRICKLINK_TOKEN_SECRET")
)

minifig_ids = ["sw0001", "sw0002"]

BASE_URL = 'https://api.bricklink.com/api/store/v1'

def get_minifig_data(minifig_id):
    url = f'{BASE_URL}/items/MINIFIG/{minifig_id}'
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Error fetching {minifig_id}: {response.status_code}")
        return None

if __name__ == "__main__":
    for fig_id in minifig_ids:
        data = get_minifig_data(fig_id)
        print(data)
