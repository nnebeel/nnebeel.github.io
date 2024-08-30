import json
from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement

# Define the GEDCOM file path
gedcom_file_path = "C:\\Users\\BenjaminLee\\OneDrive\\Genealogy\\LJL Direct Only.ged"
json_file_path = "C:\\Users\\BenjaminLee\\OneDrive\\Genealogy\\LJL Direct Only.json"

# Initialize the parser
gedcom_parser = Parser()
gedcom_parser.parse_file(gedcom_file_path)

# Get the root child elements from the GEDCOM file
root_child_elements = gedcom_parser.get_element_list()

data = {}

# Function to get the name from the individual element
def get_name(individual):
    names = individual.get_name()
    if names:
        return ' '.join(names)
    return "unknown"

# Function to get the place data from an event
def get_place(event):
    if event and len(event) > 1 and event[1]:
        return ''.join(event[1])
    return "unknown"

# Function to get the year from an event
def get_year(event):
    if event and event[0]:
        return event[0].split()[-1]
    return "unknown"

testing = True
sample_size = 100
counter = 0

# Traverse the tree to extract relevant information
for element in root_child_elements:
    if isinstance(element, IndividualElement):
        individual_id = element.get_pointer()
        birth_place = get_place(element.get_birth_data())
        birth_year = get_year(element.get_birth_data())
        death_place = get_place(element.get_death_data())
        death_year = get_year(element.get_death_data())
        name = get_name(element)

        data[individual_id] = {
            "Name": name,
            "BirthYear": birth_year,
            "BirthPlace": birth_place,
            "ChildBirthPlace": [],
            "ChildIDs": [],
            "ChildNames": [],
            "ChildBirthYears": [],
            "DeathYear": death_year,
            "DeathPlace": death_place
        }

        # Print the data to the console
        print(f"Processed Individual {individual_id}: {data[individual_id]}")
        
        counter += 1
        if testing and counter >= sample_size:
            break

# Update parents with child's birth information
for element in root_child_elements:
    if isinstance(element, IndividualElement):
        individual_id = element.get_pointer()
        birth_place = data[individual_id]["BirthPlace"]
        birth_year = data[individual_id]["BirthYear"]
        name = data[individual_id]["Name"]

        # Manually traverse families to find parents
        for family in root_child_elements:
            if isinstance(family, FamilyElement):
                children = family.get_child_elements()
                if individual_id in [child.get_pointer() for child in children]:
                    husband = family.get_husband()
                    wife = family.get_wife()

                    if husband:
                        husband_id = husband.get_pointer()
                        if husband_id in data:
                            data[husband_id]["ChildBirthPlace"].append(birth_place)
                            data[husband_id]["ChildIDs"].append(individual_id)
                            data[husband_id]["ChildNames"].append(name)
                            data[husband_id]["ChildBirthYears"].append(birth_year)
                            print(f"Updated Husband {husband_id} with child {individual_id} birth info")

                    if wife:
                        wife_id = wife.get_pointer()
                        if wife_id in data:
                            data[wife_id]["ChildBirthPlace"].append(birth_place)
                            data[wife_id]["ChildIDs"].append(individual_id)
                            data[wife_id]["ChildNames"].append(name)
                            data[wife_id]["ChildBirthYears"].append(birth_year)
                            print(f"Updated Wife {wife_id} with child {individual_id} birth info")

# Save data to JSON file
with open(json_file_path, 'w') as json_file:
    json.dump(data, json_file, indent=4)

print(f"Data has been successfully written to {json_file_path}")
