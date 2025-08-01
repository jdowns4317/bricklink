#!/usr/bin/env python3
"""
Filter out BrickLink items marked for deletion, writing results in batches of 100.

Assumes your CSV is named 'items.csv' with columns:
    item_id,item_name,category

Installs needed:
    pip install pandas requests beautifulsoup4
"""

import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

INPUT_CSV = 'processed_data/all_minifigs.csv'
OUTPUT_CSV = 'processed_data/all_minifigs_filtered.csv'
BATCH_SIZE = 100

# Adjust this if you're also checking PARTs, SETs, etc.
ITEM_TYPE_PREFIX = 'M'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; ArbitrageBot/1.0)'
}

def is_marked_for_deletion(item_id: str) -> bool:
    """
    Returns True if the BrickLink catalog page for this item
    contains the deletion banner text.
    """
    url = (
        f'https://www.bricklink.com/v2/catalog/catalogitem.page'
        f'?{ITEM_TYPE_PREFIX}={item_id}'
    )
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        print(f'  [!] HTTP {resp.status_code} for {item_id}; keeping by default')
        return False

    page_text = BeautifulSoup(resp.text, 'html.parser')\
                    .get_text(separator=' ')\
                    .lower()
    # Look for the exact phrase BrickLink uses at the top of deleted items
    return 'this catalog item is marked for deletion' in page_text

def main():
    # Remove existing output so we start fresh
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)

    df = pd.read_csv(INPUT_CSV, dtype=str)
    buffer = []
    write_header = True

    print(f'Checking {len(df)} items for deletion…')
    for idx, row in df.iterrows():
        item_id = row['item_id']
        print(f'[{idx+1}/{len(df)}] {item_id}…', end=' ')
        try:
            if is_marked_for_deletion(item_id):
                print('💀 removed')
            else:
                print('✅ keep')
                buffer.append(row)
        except Exception as e:
            print(f'(!) error: {e}; keeping')
            buffer.append(row)

        # If buffer hits batch size, write it out
        if len(buffer) >= BATCH_SIZE:
            batch_df = pd.DataFrame(buffer, columns=df.columns)
            batch_df.to_csv(
                OUTPUT_CSV,
                mode='a',
                index=False,
                header=write_header
            )
            write_header = False
            buffer.clear()

        time.sleep(0.2)  # polite throttle

    # Write any remaining rows
    if buffer:
        batch_df = pd.DataFrame(buffer, columns=df.columns)
        batch_df.to_csv(
            OUTPUT_CSV,
            mode='a',
            index=False,
            header=write_header
        )

    print(f'\nDone. Filtered file written to {OUTPUT_CSV}')

if __name__ == '__main__':
    # main()
    # Compare lengths of input and output files
    try:
        input_len = len(pd.read_csv(INPUT_CSV, dtype=str))
        output_len = len(pd.read_csv(OUTPUT_CSV, dtype=str))
        print(f'Input rows: {input_len}, Output rows: {output_len}')
    except Exception as e:
        print(f'Could not compare file lengths: {e}')
