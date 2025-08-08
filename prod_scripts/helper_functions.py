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

# Global API call counter
api_call_counter = 0

def reset_api_counter():
    global api_call_counter
    api_call_counter = 0

def get_api_call_count():
    global api_call_counter
    return api_call_counter

def throttle():
    global api_call_counter
    api_call_counter += 1
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
    six_months = data['data']['total_quantity']

    params = {
        'new_or_used': condition,  # 'N' for New, 'U' for Used
        'currency_code': 'USD',
        'guide_type': 'stock'
    }
    throttle()
    response = requests.get(url, auth=auth, params=params)

    if response.status_code != 200:
        print(f"Failed to get sell-thru rate for {item_id} ({condition}: {response.status_code}")
        return None

    data = response.json()
    full_stock = data['data']['total_quantity']

    if full_stock == 0:
        return None
    return six_months / full_stock


def get_price_guide(item_type, item_id, condition, country_code=None, color_id=None):
    """
    Gets price guide data from BrickLink for a given item.
    If country_code is provided, only listings from that country are returned.
    If color_id is provided, only listings for that color are returned.
    """
    url = f'{BASE_URL}/items/{item_type}/{item_id}/price'
    params = {
        'new_or_used': condition,  # 'N' for New, 'U' for Used
        'currency_code': 'USD',
        'guide_type': 'stock'
    }
    if country_code:
        params['country_code'] = country_code
    if color_id:
        params['color_id'] = color_id
    throttle()
    response = requests.get(url, auth=auth, params=params)

    if response.status_code != 200:
        print(f"Failed to get data for {item_id} ({condition}, country={country_code}): {response.status_code}")
        return None

    data = response.json()
    # get all tiers…
    all_tiers = data.get('data', {}).get('price_detail', [])
    # …but only keep those that actually ship to you
    listings = [tier for tier in all_tiers if tier.get('shipping_available')]

    if listings and item_type != "PART": 
        print(f"Found {len(listings)} listings for {item_id} (country={country_code}, condition={condition})")
    elif item_type != "PART":
        print(f"No listings found for {item_id} (country={country_code}, condition={condition})")
        return


    # Sort listings numerically by unit_price (as float)
    listings_sorted = sorted(listings, key=lambda x: float(x['unit_price']))

    return listings_sorted

def get_lowest_prices(item_id, condition, min_intl_quantity=1, min_price=0):
    """
    Fetch the lowest prices for a minifigure by condition (New or Used),
    and return the cheapest price in the US and abroad that meets all requirements.
    
    Args:
        item_id (str): e.g. "sw123"
        condition (str): "N" or "U" for New or Used
        min_intl_quantity (int): Minimum quantity required for international listing
        min_price (float): Minimum price required for international listing
    
    Returns:
        dict: { 'US': float or None, 'INTL': float or None, 'INTL Quantity': int or None }
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
        # Find the first listing that is NOT from the US AND meets all requirements
        for listing in intl_listings:
            if listing.get('seller_country_code', '') != 'US':
                listing_price = float(listing['unit_price'])
                listing_quantity = int(listing['quantity'])
                
                # Check if this listing meets all requirements
                if (listing_quantity >= min_intl_quantity and 
                    listing_price >= min_price):
                    intl_price = listing_price
                    intl_quantity = listing_quantity
                    break

    return {'US': us_price, 'INTL': intl_price, 'INTL Quantity': intl_quantity}

def fetch_minifig_parts_with_colors(item_id):
    """
    Fetches all parts for the given minifigure and returns
    a list of (part_no, color_id) tuples.
    
    :param item_id: e.g. "sw0239"
    :return: [("970c00", 48), ("42446", 85), ...]
    """
    url = f"{BASE_URL}/items/MINIFIG/{item_id}/subsets"
    params = {"break_minifigs": "true"}
    throttle()  # Count this API call
    resp = requests.get(url, auth=auth, params=params)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to fetch subsets for {item_id}: HTTP {resp.status_code}")

    data = resp.json().get("data", [])
    if not data:
        return []

    parts = []
    for subset in data:
        for entry in subset.get("entries", []):
            item = entry.get("item", {})
            no = item.get("no")
            color_id = entry.get("color_id")
            # only include entries where we got both a part no and a color
            if no is not None and color_id is not None:
                parts.append((no, color_id))

    return parts


def get_prices_parts(item_id, condition):
    """
    Get the prices for a minifig and its parts that meet the specified thresholds.
    """
    part_ids = fetch_minifig_parts_with_colors(item_id)
    all_minifigs = get_price_guide('MINIFIG', item_id, condition)
    part_listings = {}
    for (part_id, color_id) in part_ids:
        part_listings[part_id] = get_price_guide('PART', part_id, condition, color_id=color_id)
    return (all_minifigs, part_listings)


def identify_price_arbitrage(item_id, condition, discount_rate, sell_thru_rate, min_intl_quantity=1, min_price=0):
    """
    Identify arbitrage opportunities based on the lowest prices.
    
    Args:
        item_id (str): e.g. "sw123"
        condition (str): "N" or "U" for New or Used
        discount_rate (float): Maximum ratio of international to US price (e.g., 0.6 for 60%)
        sell_thru_rate (float): Minimum sell-through rate required
        min_intl_quantity (int): Minimum quantity required for international listing
        min_price (float): Minimum price required for international listing
    
    Returns:
        dict: Arbitrage opportunity data if found, else None
    """
    prices = get_lowest_prices(item_id, condition, min_intl_quantity, min_price)
    us_price = prices.get('US')
    intl_price = prices.get('INTL')
    intl_quantity = prices.get('INTL Quantity')

    calc_sell_thru_rate = get_sell_thru_rate('MINIFIG', item_id, condition)

    if us_price is None or intl_price is None or calc_sell_thru_rate is None:
        return None

    # Arbitrage condition: international price meets discount rate AND sell-through rate requirement
    if intl_price <= discount_rate * us_price and calc_sell_thru_rate >= sell_thru_rate:
        return {
            'ItemID': item_id,
            'Condition': condition,
            'Intl Price': round(intl_price, 2),
            'US Price': round(us_price, 2),
            'Intl Quantity': intl_quantity,
            'Sell Thru Rate': round(calc_sell_thru_rate, 2),
            'Timestamp': datetime.utcnow().isoformat()
        }
    
    return None

def identify_price_arbitrage_parts(item_id, condition, discount_rate, sell_thru_rate_minifig, sell_thru_rate_part, min_minifig_quantity, min_minifig_price):
    """
    Identify arbitrage opportunities by breaking minifigs into parts or vice versa.
    Returns: opportunities_list or None
    """
    minifig_sell_thru = get_sell_thru_rate('MINIFIG', item_id, condition)
    all_minifigs, parts_dict = get_prices_parts(item_id, condition)
    if not all_minifigs or float(all_minifigs[0]['unit_price']) < min_minifig_price or not minifig_sell_thru:
        return None

    # check break apart first
    dicts_to_return = []
    for minifig in all_minifigs:
        if int(minifig['quantity']) >= min_minifig_quantity:
            total_parts_price = 0
            parts = []
            for part_id, part_listings in parts_dict.items():
                if part_listings and len(part_listings) > 0:
                    part_sell_thru = get_sell_thru_rate('PART', part_id, condition)
                    if part_sell_thru and part_sell_thru >= sell_thru_rate_part:
                        total_parts_price += float(part_listings[0]['unit_price'])
                        parts.append(part_id)
            if float(minifig['unit_price']) <= discount_rate * total_parts_price:
                dicts_to_return.append({
                    'ItemID': item_id,
                    'Condition': condition,
                    'Break or Build': "Break",
                    'Parts Considered': ", ".join(parts),
                    'Minifig Price': round(float(minifig['unit_price']), 2),
                    'Minifig Sell Thru Rate': round(minifig_sell_thru, 2),
                    'Minifig Quantity': int(minifig['quantity']),
                    'Parts Combined Price': round(total_parts_price, 2)
                })
        break

    # check build next
    minifig_price = float(all_minifigs[0]['unit_price'])
    
    if minifig_sell_thru >= sell_thru_rate_minifig:
        total_build_cost = 0
        parts_used = []
        failed_to_find = False
        for part_id, part_listings in parts_dict.items():
            if failed_to_find:
                break
            if part_listings and len(part_listings) > 0:
                for i in range(len(part_listings)):
                    part_entry = part_listings[i]
                    if int(part_entry['quantity']) >= min_minifig_quantity:
                        total_build_cost += float(part_entry['unit_price'])
                        parts_used.append(part_id)
                        break
                    elif i == len(part_listings) - 1:
                        failed_to_find = True
        if total_build_cost > 0 and total_build_cost <= discount_rate * minifig_price and not failed_to_find:
            dicts_to_return.append({
                    'ItemID': item_id,
                    'Condition': condition,
                    'Break or Build': "Build",
                    'Parts Considered': ", ".join(parts_used),
                    'Minifig Price': round(minifig_price, 2),
                    'Minifig Sell Thru Rate': round(minifig_sell_thru, 2),
                    'Minifig Quantity': min_minifig_quantity,
                    'Parts Combined Price': round(total_build_cost, 2)
            })
    return dicts_to_return if dicts_to_return else None

