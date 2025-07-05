import xml.etree.ElementTree as ET
import pandas as pd

# Load and parse the XML file
tree = ET.parse('raw_data/Minifigures.xml')
root = tree.getroot()

all_items = []

for item in root.findall('ITEM'):
    item_type = item.find('ITEMTYPE').text
    item_id = item.find('ITEMID').text
    item_name = item.find('ITEMNAME').text
    category = item.find('CATEGORY').text

    if item_type == 'M':
        all_items.append({
            'item_id': item_id,
            'item_name': item_name,
            'category': category
        })

# Convert to DataFrame and save
df = pd.DataFrame(all_items)
df.to_csv('processed_data/all_minifigs.csv', index=False)

print(f"Extracted {len(df)} minifigs to all_minifigs.csv")
