import csv
import json

# Initialize an empty dictionary for the hierarchical data
hierarchy = {}

def insert_node(path, value, body, current_level):
    """Recursively inserts a node based on the provided path into the current level of the hierarchy."""
    if not path:
        return
    current_node = path.pop(0)
    if current_node not in current_level:
        current_level[current_node] = {"children": {}} if path else {"value": value, "body": body}
    if path:
        insert_node(path, value, body, current_level[current_node]["children"])

def build_hierarchy(csv_filepath):
    """Builds a hierarchical structure from a CSV file."""
    with open(csv_filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Assuming headers are named Grandparent, Parent, Child, Leaf, Value, Body
            path = [row['Grandparent'], row['Parent'], row['Child'], row['Leaf']]
            path = [p for p in path if p]  # Remove empty values from the path
            value = int(row['Value'])
            body = row['Body']
            insert_node(path, value, body, hierarchy)

def hierarchy_to_json(hierarchy):
    """Converts the hierarchical dictionary into a nested list of dictionaries suitable for JSON."""
    result = []
    for name, node in hierarchy.items():
        if 'value' in node:  # Leaf node
            json_node = {"name": name, "value": node['value'], "body": node['body']}
        else:  # Intermediate node
            json_node = {"name": name, "children": hierarchy_to_json(node['children'])}
        result.append(json_node)
    return result

# Path to your CSV file
csv_file_path = 'skills.csv'

# Build the hierarchy from the CSV
build_hierarchy(csv_file_path)

# Convert the hierarchy to JSON format
hierarchy_json = hierarchy_to_json(hierarchy)

# Print or save the JSON output
print(json.dumps(hierarchy_json, indent=2))

# Optionally, save to a file
with open('skills.json', 'w') as f:
    json.dump(hierarchy_json, f, indent=2)
