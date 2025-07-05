from requests_oauthlib import OAuth1
import os
import csv
import pandas as pd
from helper_functions import identify_price_arbitrage

auth = OAuth1(
    os.getenv("BRICKLINK_CONSUMER_KEY"),
    os.getenv("BRICKLINK_CONSUMER_SECRET"),
    os.getenv("BRICKLINK_TOKEN_VALUE"),
    os.getenv("BRICKLINK_TOKEN_SECRET")
)

minifig_ids = []
with open('processed_data/all_minifigs.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        minifig_ids.append(row['item_id'])

# Limit to first 100 minifigs due to API rate limits
# TODO implement batch processing
minifig_ids = minifig_ids[:100]

arbitrage_data = []

for item_id in minifig_ids:
    for condition in ['N', 'U']:
        try:
            arbitrage = identify_price_arbitrage(item_id=item_id, condition=condition)
            if arbitrage:
                arbitrage_data.append(arbitrage)
        except Exception as e:
            print(f"Error with {item_id} ({condition}): {e}")

# Create DataFrame and save
df_arbitrage = pd.DataFrame(arbitrage_data)
df_arbitrage.to_csv("arbitrage/minifig_opportunities.csv", index=False)

print(f"Found {len(df_arbitrage)} arbitrage opportunities.")