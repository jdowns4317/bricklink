import requests
from requests_oauthlib import OAuth1
import time

# TODO replace when done
CONSUMER_KEY = 'your_consumer_key'
CONSUMER_SECRET = 'your_consumer_secret'
TOKEN_VALUE = 'your_token_value'
TOKEN_SECRET = 'your_token_secret'

auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, TOKEN_VALUE, TOKEN_SECRET)

BASE_URL = 'https://api.bricklink.com/api/store/v1'

def get_all_minifigs():
    results = []
    page = 1
    page_size = 100
    total_pages = 1

    print("Fetching all minifigs...")

    while page <= total_pages:
        print(f"Fetching page {page}...")
        url = f'{BASE_URL}/items/M?page={page}&page_size={page_size}'
        response = requests.get(url, auth=auth)

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break

        data = response.json()

        if 'meta' in data and 'pages' in data['meta']:
            total_pages = data['meta']['pages']

        results.extend(data.get('data', []))
        page += 1

        time.sleep(0.2)

    print(f"Retrieved {len(results)} minifigs")
    return results

if __name__ == "__main__":
    minifigs = get_all_minifigs()
    
    for fig in minifigs[:5]:
        print(f"{fig['no']}: {fig['name']}")
