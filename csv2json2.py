import csv
import json

hierarchy = {}

def insert_node(path, leaf_name, value, body, current_level):
    # Ensure we are working with the processed path without blanks for proper nesting
    processed_path = [p for p in path if p]

    # Traverse to the correct node based on the processed path
    for node in processed_path:
        if node not in current_level:
            current_level[node] = {"children": {}, "leaves": []}
        current_level = current_level[node]["children"]

    # Insert the leaf with its correct name and details
    # This ensures the leaf name is used, correcting the previous issue
    if leaf_name not in current_level:
        current_level[leaf_name] = {"leaves": []}
    current_level[leaf_name]["leaves"].append({"value": value, "body": body})

def build_hierarchy(csv_filepath):
    with open(csv_filepath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try:
                # Extract the leaf name, value, and body from the row
                leaf_name = row[-3]
                value = int(row[-2])  # Convert the value to an integer
                body = row[-1]
                path = row[:-3]  # Extract the path, excluding leaf name, value, and body
                insert_node(path, leaf_name, value, body, hierarchy)
            except ValueError:
                continue  # Skip rows where conversion fails

def hierarchy_to_json(current_level):
    result = []
    for name, info in current_level.items():
        node = {"name": name}
        # Correctly process leaves
        if info.get("leaves"):  # Safely access "leaves"
            for leaf in info["leaves"]:
                # Directly append leaf nodes under the current node
                result.append({"name": leaf.get("name", name), "value": leaf["value"], "body": leaf["body"]})
        # Safely check and process children if they exist
        if "children" in info and info["children"]:  # Check if "children" exists and is not empty
            children = hierarchy_to_json(info["children"])
            if children:  # Add children only if the list is not empty
                # Ensure we append the children to the current node
                node["children"] = children
                result.append(node)
    return result


csv_file_path = 'skills.csv'

build_hierarchy(csv_file_path)

hierarchy_json = hierarchy_to_json(hierarchy)

# print(json.dumps(hierarchy_json, indent=2))

# Optionally, save the updated hierarchy to a file
with open('skills.json', 'w') as f:
    json.dump(hierarchy_json, f, indent=2)
