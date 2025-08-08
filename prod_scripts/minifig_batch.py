from requests_oauthlib import OAuth1
import os
import csv
import sys
import pandas as pd
from datetime import datetime
from helper_functions import identify_price_arbitrage
from dotenv import load_dotenv
load_dotenv()

DISCOUNT_RATE = 0.6
SELL_THRU_RATE = 0.4
MIN_INTL_QUANTITY = 1 
MIN_PRICE = 0.25

auth = OAuth1(
    os.getenv("BRICKLINK_CONSUMER_KEY"),
    os.getenv("BRICKLINK_CONSUMER_SECRET"),
    os.getenv("BRICKLINK_TOKEN_VALUE"),
    os.getenv("BRICKLINK_TOKEN_SECRET")
)

minifig_ids = []
working_file = 'processed_data/all_minifigs.csv'
if os.path.exists('processed_data/all_minifigs_filtered.csv'):
    working_file = 'processed_data/all_minifigs_filtered.csv'
progress_file = "flags/minifig_last_index.txt"

if "-sw" in sys.argv:
    working_file = 'processed_data/star_wars_minifigs.csv'
    progress_file = "flags/sw_minifig_last_index.txt"
elif "-sh" in sys.argv:
    working_file = 'processed_data/super_hero_minifigs.csv'
    progress_file = "flags/sh_minifig_last_index.txt"
with open(working_file, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        minifig_ids.append(row['item_id'])


if os.path.exists(progress_file):
    with open(progress_file, "r") as f:
        start_idx = int(f.read().strip())
else:
    start_idx = 0

n = len(minifig_ids)
batch_size = 100
arbitrage_data = []
api_limit_hit = False

# Only process a batch, wrapping around if needed
for offset in range(batch_size):
    idx = (start_idx + offset) % n
    item_id = minifig_ids[idx]
    for condition in ['N', 'U']:
        try:
            arbitrage = identify_price_arbitrage(item_id=item_id, 
                                                 condition=condition, 
                                                 discount_rate=DISCOUNT_RATE,
                                                 sell_thru_rate=SELL_THRU_RATE,
                                                 min_intl_quantity=MIN_INTL_QUANTITY,
                                                 min_price=MIN_PRICE)
            if arbitrage:
                arbitrage_data.append(arbitrage)
        except Exception as e:
            if "api limit" in str(e).lower():
                print(f"API limit hit at index {idx}. Saving progress and flag.")
                with open(progress_file, "w") as f:
                    f.write(str(idx))
                api_limit_hit = True
                break
            else:
                print(f"Error with {item_id} ({condition}): {e}")
    if api_limit_hit:
        break

# If finished batch without hitting API limit, update last index
if not api_limit_hit:
    next_idx = (start_idx + batch_size) % n
    with open(progress_file, "w") as f:
        f.write(str(next_idx))

# Create DataFrame and save
df_arbitrage = pd.DataFrame(arbitrage_data)

# Load existing opportunities
csv_path = "arbitrage/minifig_opportunities.csv"
if os.path.exists(csv_path):
    df_existing = pd.read_csv(csv_path)
else:
    df_existing = pd.DataFrame(columns=["ItemID", "Condition", "Intl Price", "US Price", "Intl Quantity", "Sell Thru Rate", "Timestamp"])

# Remove duplicates from existing
if not df_arbitrage.empty:
    # Ensure columns match
    df_new = df_arbitrage[df_existing.columns]
    # Remove any existing rows with same ItemID and Condition
    mask = ~df_existing.set_index(["ItemID", "Condition"]).index.isin(
        df_new.set_index(["ItemID", "Condition"]).index
    )
    df_existing = df_existing[mask]
    # Append new data
    df_result = pd.concat([df_existing, df_new], ignore_index=True)
    # Save (append mode)
    df_result.to_csv(csv_path, index=False)
    print(f"Found {len(df_new)} arbitrage opportunities. Appended to CSV.")
else:
    print("No new arbitrage opportunities found.")

# Update API call count
api_call_count_file = "flags/api_call_count.txt"
today_str = datetime.now().strftime("%Y-%m-%d")
calls_today = 0

if os.path.exists(api_call_count_file):
    try:
        with open(api_call_count_file, "r") as f:
            lines = f.readlines()
        file_date = lines[0].strip() if len(lines) > 0 else ""
        file_count = int(lines[1].strip()) if len(lines) > 1 and lines[1].strip().isdigit() else 0
        if file_date == today_str:
            calls_today = file_count
    except Exception:
        calls_today = 0

calls_today += batch_size * 2 * 4  # 100 items, 2 conditions (N, U), 4 calls per item

with open(api_call_count_file, "w") as f:
    f.write(f"{today_str}\n{calls_today}\n")