import xml.etree.ElementTree as ET
import pandas as pd

# Load and parse the XML file
tree = ET.parse('raw_data/Minifigures.xml')
root = tree.getroot()

# Collect Star Wars minifigs
col_minifigs = []

for item in root.findall('ITEM'):
    item_type = item.find('ITEMTYPE').text
    item_id = item.find('ITEMID').text
    item_name = item.find('ITEMNAME').text
    category = item.find('CATEGORY').text

    if item_type == 'M' and item_id.lower().startswith('col'):
        col_minifigs.append({
            'item_id': item_id,
            'item_name': item_name,
            'category': category
        })

# Convert to DataFrame and save
df = pd.DataFrame(col_minifigs)
df.to_csv('processed_data/collectible_minifigs.csv', index=False)

print(f"Extracted {len(df)} collectible minifigs to collectible_minifigs.csv")
