import xml.etree.ElementTree as ET
import pandas as pd

# Load and parse the XML file
tree = ET.parse('raw_data/Minifigures.xml')
root = tree.getroot()

# Collect Star Wars minifigs
star_wars_minifigs = []

for item in root.findall('ITEM'):
    item_type = item.find('ITEMTYPE').text
    item_id = item.find('ITEMID').text
    item_name = item.find('ITEMNAME').text
    category = item.find('CATEGORY').text

    if item_type == 'M' and item_id.lower().startswith('sw'):
        star_wars_minifigs.append({
            'item_id': item_id,
            'item_name': item_name,
            'category': category
        })

# Convert to DataFrame and save
df = pd.DataFrame(star_wars_minifigs)
df.to_csv('processed_data/star_wars_minifigs.csv', index=False)

print(f"Extracted {len(df)} Star Wars minifigs to star_wars_minifigs.csv")
