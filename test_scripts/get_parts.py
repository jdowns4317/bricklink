import os
import time
import requests
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

load_dotenv()

# OAuth1 credentials
auth = OAuth1(
    os.getenv("BRICKLINK_CONSUMER_KEY"),
    os.getenv("BRICKLINK_CONSUMER_SECRET"),
    os.getenv("BRICKLINK_TOKEN_VALUE"),
    os.getenv("BRICKLINK_TOKEN_SECRET")
)

BASE_URL = 'https://api.bricklink.com/api/store/v1'
minifig_ids = ["sw0239"]



def get_minifig_parts(minifig_id):
    """
    Fetch and flatten the parts entries for the given minifigure.
    """
    url = f"{BASE_URL}/items/MINIFIG/{minifig_id}/subsets"
    params = {"break_minifigs": "true"}
    resp = requests.get(url, auth=auth, params=params)
    if resp.status_code != 200:
        print(f"Error fetching parts for {minifig_id}: HTTP {resp.status_code}")
        return []

    data = resp.json().get("data", [])
    if not data:
        print(f"No parts data returned for {minifig_id}")
        return []

    # Flatten all subset entries into one list
    all_entries = []
    for subset in data:
        entries = subset.get("entries", [])
        all_entries.extend(entries)

    return all_entries

if __name__ == "__main__":
    for fig_id in minifig_ids:
        print(f"\nParts for minifigure {fig_id}:")
        entries = get_minifig_parts(fig_id)
        for entry in entries:
            item = entry["item"]
            qty = entry["quantity"]
            color = entry.get("color_id")
            print(f" • {qty}× {item['no']} — {item['name']} (color_id={color})")
        time.sleep(0.1)
