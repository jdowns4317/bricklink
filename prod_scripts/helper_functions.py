import requests
from requests_oauthlib import OAuth1
import os
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

auth = OAuth1(
    os.getenv("BRICKLINK_CONSUMER_KEY"),
    os.getenv("BRICKLINK_CONSUMER_SECRET"),
    os.getenv("BRICKLINK_TOKEN_VALUE"),
    os.getenv("BRICKLINK_TOKEN_SECRET")
)

BASE_URL = 'https://api.bricklink.com/api/store/v1'

def throttle():
    time.sleep(0.1)

def get_sell_thru_rate(item_type, item_id, condition):
    url = f'{BASE_URL}/items/{item_type}/{item_id}/price'
    params = {
        'new_or_used': condition,  # 'N' for New, 'U' for Used
        'currency_code': 'USD',
        'guide_type': 'sold'
    }
    throttle()
    response = requests.get(url, auth=auth, params=params)

    if response.status_code != 200:
        print(f"Failed to get sell-thru rate for {item_id} ({condition}: {response.status_code}")
        return None

    data = response.json()
    items_sold = data['data']['unit_quantity']
    items_avaliable = data['data']['total_quantity']
    if items_avaliable == 0:
        return None
    return items_sold / items_avaliable


def get_price_guide(item_type, item_id, condition, country_code=None):
    """
    Gets price guide data from BrickLink for a given item.
    If country_code is provided, only listings from that country are returned.
    """
    url = f'{BASE_URL}/items/{item_type}/{item_id}/price'
    params = {
        'new_or_used': condition,  # 'N' for New, 'U' for Used
        'currency_code': 'USD',
        'guide_type': 'stock'
    }
    if country_code:
        params['country_code'] = country_code
    throttle()
    response = requests.get(url, auth=auth, params=params)

    if response.status_code != 200:
        print(f"Failed to get data for {item_id} ({condition}, country={country_code}): {response.status_code}")
        return None

    data = response.json()
    listings = data.get('data', {}).get('price_detail', [])

    if listings: 
        print(f"Found {len(listings)} listings for {item_id} (country={country_code}, condition={condition})")
    else:
        print(f"No listings found for {item_id} (country={country_code}, condition={condition})")
        return


    # Sort listings numerically by unit_price (as float)
    listings_sorted = sorted(listings, key=lambda x: float(x['unit_price']))

    return listings_sorted

def get_lowest_prices(item_id, condition):
    """
    Fetch the lowest prices for a minifigure by condition (New or Used),
    and return the cheapest price in the US and abroad.
    
    Args:
        item_id (str): e.g. "sw123"
        condition (str): "N" or "U" for New or Used
    
    Returns:
        dict: { 'US': float or None, 'INTL': float or None }
    """
    # Get US price
    us_listings = get_price_guide('MINIFIG', item_id, condition, country_code='US')
    us_price = None
    if us_listings:
        us_price = float(us_listings[0]['unit_price'])

    # Get International price (any country except US)
    intl_listings = get_price_guide('MINIFIG', item_id, condition)
    intl_price = None
    intl_quantity = None
    if intl_listings:
        # Find the first listing that is NOT from the US
        for listing in intl_listings:
            if listing.get('seller_country_code', '') != 'US':
                intl_price = float(listing['unit_price'])
                intl_quantity = int(intl_listings[0]['quantity'])
                break

    return {'US': us_price, 'INTL': intl_price, 'INTL Quantity': intl_quantity}

def identify_price_arbitrage(item_id, condition, discount_rate, sell_thru_rate, min_intl_quantity=1):
    """
    Identify arbitrage opportunities based on the lowest prices.
    
    Args:
        item_id (str): e.g. "sw123"
        condition (str): "N" or "U" for New or Used
    
    Returns:
        dict: Arbitrage opportunity data if found, else None
    """
    prices = get_lowest_prices(item_id, condition)
    # print(f"Prices for {item_id} ({condition}): {prices}")
    us_price = prices.get('US')
    intl_price = prices.get('INTL')
    intl_quantity = prices.get('INTL Quantity')

    calc_sell_thru_rate = get_sell_thru_rate('MINIFIG', item_id, condition)

    if us_price is None or intl_price is None or calc_sell_thru_rate is None:
        return None

    # Arbitrage condition: international price <= 60% of US price
    if intl_price <= discount_rate * us_price and calc_sell_thru_rate >= sell_thru_rate and intl_quantity >= min_intl_quantity:
        return {
            'ItemID': item_id,
            'Condition': condition,
            'Intl Price': intl_price,
            'US Price': us_price,
            'Intl Quantity': intl_quantity,
            'Sell Thru Rate': calc_sell_thru_rate,
            'Timestamp': datetime.utcnow().isoformat()
        }
    
    return None