import os
import sys
print("Python executable being used:", sys.executable)
print("Python version:", sys.version)
print("sys.path:", sys.path)
from lxml import etree as ET
import csv
import html
import json
import re
import base64
from bs4 import BeautifulSoup
import bleach

def get_directory():
    directory = input("Please enter the directory containing the XML files: ").strip()
    if not os.path.isdir(directory):
        print(f"The directory '{directory}' does not exist.")
        sys.exit(1)
    return directory

def clean_html_content(html_content):
    # Strip leading and trailing whitespace
    html_content = html_content.strip()
    soup = BeautifulSoup(html_content, 'html.parser')

    allowed_tags = [
        'p', 'ul', 'ol', 'li', 'a', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'code', 'pre', 'img', 'figure', 'figcaption', 'br', 'hr'
    ]

    allowed_attributes = {
        '*': ['class', 'id'],
        'a': ['href', 'title', 'download'],
        'img': ['src', 'alt', 'title'],
    }

    # Remove empty text nodes
    for element in soup.find_all(string=lambda text: isinstance(text, str) and not text.strip()):
        element.extract()

    # Convert all <div> tags to <p> tags
    for div in soup.find_all('div'):
        div.name = 'p'

    # Remove inline styles and unwanted attributes
    for tag in soup.find_all():
        tag.attrs = {
            attr: value for attr, value in tag.attrs.items()
            if attr in allowed_attributes.get(tag.name, []) + allowed_attributes.get('*', [])
        }

    # Unwrap unnecessary tags like empty <font> and <span>
    for tag in soup.find_all(['font', 'span']):
        tag.unwrap()

    # Remove empty tags (including <p> tags with only whitespace or <br>)
    for tag in soup.find_all():
        # Skip tags that should not be removed even if empty
        if tag.name in ['br', 'img']:
            continue
        if not tag.get_text(strip=True) and not tag.find(['img', 'br']):
            tag.decompose()

    # Sanitize the HTML
    cleaned_html = bleach.clean(
        str(soup),
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )

    # Final parsing to remove any remaining empty tags
    final_soup = BeautifulSoup(cleaned_html, 'html.parser')
    for tag in final_soup.find_all():
        if tag.name in ['br', 'img']:
            continue
        if not tag.get_text(strip=True) and not tag.find(['img', 'br']):
            tag.decompose()

    cleaned_html = str(final_soup)

    return cleaned_html.strip()

def clean_value(value, output_dir='', unique_id=''):
    if value:
        # Unescape HTML entities.
        value = html.unescape(html.unescape(value))
        # Detect base64-encoded images and process them.
        if output_dir and unique_id and "<img" in value:
            value = extract_base64_images(value, output_dir, unique_id)
        # Replace line breaks with spaces.
        value = ' '.join(value.split())
        # Clean the HTML content
        if "<" in value and ">" in value:
            value = clean_html_content(value)
        return value
    return value

def extract_base64_images(html_content, output_dir, unique_id):
    # Ensure the images directory exists
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # Regular expression to find base64 image data.
    base64_pattern = r'src="data:image/(?P<ext>[^;]+);base64,(?P<data>.+?)"'

    image_counter = 0

    def replacer(match):
        nonlocal image_counter
        ext = match.group('ext')
        base64_data = match.group('data')
        # Decode the base64 data.
        try:
            image_data = base64.b64decode(base64_data)
        except base64.binascii.Error:
            return match.group(0)  # Return the original match if base64 data is invalid
        # Increment image counter to ensure uniqueness
        image_counter += 1
        # Create a unique filename for the image.
        image_filename = f"{unique_id}_image{image_counter}.{ext}"
        image_path = os.path.join(images_dir, image_filename)
        # Save the image file.
        with open(image_path, 'wb') as img_file:
            img_file.write(image_data)
        # Return the new src attribute with the relative file path.
        return f'src="images/{image_filename}"'

    # Substitute base64 images in the HTML content.
    processed_content = re.sub(base64_pattern, replacer, html_content, flags=re.DOTALL)
    return processed_content

def get_padded_id(value, prefix):
    if value and str(value).isdigit():
        padded_id = f"{prefix}-{int(value):0>4}"
    else:
        padded_id = f"{prefix}-{value}"
    return padded_id

def append_element_attributes(tree_elem, data_dict, prefix, output_dir='', file_id=''):
    for attr in tree_elem.attrib:
        field_name = f"{prefix}_{attr}"
        value = tree_elem.attrib[attr]
        unique_id = f"{file_id}_{field_name}"
        data_dict[field_name] = clean_value(value, output_dir, unique_id)
    return data_dict

def append_child_element_values(tree_elem, data_dict, prefix, output_dir='', file_id=''):
    for child in tree_elem:
        if len(child) == 0 and child.text:
            field_name = f"{prefix}_{child.tag}"
            unique_id = f"{file_id}_{field_name}"
            data_dict[field_name] = clean_value(child.text.strip(), output_dir, unique_id)
    return data_dict

def process_xml_files(directory):
    # Initialize data collections and fieldnames
    data_collections = {
        'Course': [],
        'Expert': [],
        'Section': [],
        'Lesson': [],
        'Topic': []
    }
    fieldnames = {
        'Course': set(),
        'Expert': set(),
        'Section': set(),
        'Lesson': set(),
        'Topic': set()
    }

    xml_files = sorted([f for f in os.listdir(directory) if f.lower().endswith('.xml')])
    for xml_file in xml_files:
        xml_path = os.path.join(directory, xml_file)
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            if root.tag != 'Courses':
                print(f"Warning: Skipping file '{xml_file}' because it does not contain a top-level <Courses> element.")
                continue
            for course in root.findall('Course'):
                # Begin processing courses
                process_course(course, data_collections, fieldnames, directory)
        except ET.ParseError as e:
            print(f"Error parsing '{xml_file}': {e}")
            continue

    # After processing all XML files, write CSV files
    write_csv_files(directory, data_collections, fieldnames)

def process_course(course_elem, data_collections, fieldnames, directory):
    # Initialize course_order_counter
    global_order_counter = {'counter': 0}  # Use dict to pass by reference

    # Initialize the list to store JSON objects for CourseSections
    course_sections_json_list = []

    # Extract CourseId and generate course_id_padded
    course_id_value = course_elem.findtext('CourseId')
    if not course_id_value or not course_id_value.isdigit():
        print(f"Warning: Skipping course with missing or invalid <CourseId>.")
        return
    course_id_padded = get_padded_id(course_id_value, 'C')
    course_path = course_id_padded

    # Initialize course_data with Path and CourseID
    course_data = {
        'Path': course_path,
        'CourseID': course_id_padded
    }

    course_data = append_child_element_values(course_elem, course_data, "Course")
    fieldnames['Course'].update(course_data.keys())

    course_name = course_elem.findtext('CourseName')

    # Process Course Image
    image_url = course_elem.findtext('Image')
    if image_url:
        # Clean up the image URL
        image_url = clean_value(image_url.strip())
        if image_url.endswith('/'):
            image_url = image_url[:-1]  # Remove trailing slash if present
        # Extract the original filename
        image_filename = image_url.split('/')[-1]
        # Extract the extension
        _, ext = os.path.splitext(image_filename)
        # Construct the optimized filename
        course_image_optimized_filename = f"{course_id_padded}{ext}"
        # Add to course_data
        course_data['CourseImageOriginalFilename'] = image_filename
        course_data['CourseImageOptimizedFilename'] = course_image_optimized_filename
    else:
        course_data['CourseImageOriginalFilename'] = ''
        course_data['CourseImageOptimizedFilename'] = ''

    fieldnames['Course'].update(['CourseImageOriginalFilename', 'CourseImageOptimizedFilename'])
    
    # Delay until after all topics and sections are finished because of JSON data requirement.
    # data_collections['Course'].append(course_data)

    # Process Experts
    experts_elem = course_elem.find('Experts')
    if experts_elem is not None:
        expert_list = experts_elem.findall('Expert')
        for idx, expert_elem in enumerate(expert_list):
            expert_id_padded = get_padded_id(str(idx), 'E')
            expert_path = f"{course_path}/{expert_id_padded}"
            expert_data = {
                'Path': expert_path,
                'CourseID': course_id_padded,
                'ExpertID': expert_id_padded
            }

            expert_data = append_child_element_values(expert_elem, expert_data, "Expert")
            fieldnames['Expert'].update(expert_data.keys())
            data_collections['Expert'].append(expert_data)

    # Process Sections (Skillify Term: Lessons)
    outline_elem = course_elem.find('Outline')
    if outline_elem is not None:
        lessons_elem = outline_elem.find('Lessons')
        if lessons_elem is not None:
            lesson_list = lessons_elem.findall('Lesson')
            for lesson_idx, lesson_elem in enumerate(lesson_list):
                global_order_counter['counter'] += 1  # Increment order
                lesson_display_order = lesson_elem.get('DisplayOrder')
                if lesson_display_order and lesson_display_order.isdigit():
                    section_id_padded = get_padded_id(lesson_display_order, 'S')
                else:
                    section_id_padded = get_padded_id(str(lesson_idx), 'S')
                section_path = f"{course_path}/{section_id_padded}"
                section_data = {
                    'Path': section_path,
                    'CourseID': course_id_padded,
                    'SectionID': section_id_padded,
                    'CourseOrder': global_order_counter['counter']
                }

                section_data = append_element_attributes(lesson_elem, section_data, "Lesson")
                fieldnames['Section'].update(section_data.keys())
                data_collections['Section'].append(section_data)

                 # Build JSON object for CourseSections
                try:
                    JSON_order = section_data['CourseOrder']
                    lesson_id = section_data.get('Lesson_Id', '')
                    if not lesson_id.isdigit():
                        lesson_id = '0'
                    if not lesson_display_order.isdigit():
                        lesson_display_order = '0'
                    JSON_ID = f"{int(course_id_value):0>4}{int(lesson_display_order):0>4}{int(lesson_id):0>5}"
                    JSON_title = section_data.get('Lesson_Name', '')
                    json_object = {
                        "order": JSON_order,
                        "ID": int(JSON_ID),
                        "post_title": JSON_title,
                        "url": "",
                        "edit_link": "",
                        "tree": [],
                        "expanded": False,
                        "type": "section-heading"
                    }
                    course_sections_json_list.append(json_object)
                except Exception as e:
                    print(f"Error creating JSON object for section: {e}")

                # Process Lessons (Skillify Term: Sections)
                section_list = lesson_elem.findall('Section')
                for section_idx, section_elem in enumerate(section_list):
                    global_order_counter['counter'] += 1  # Increment order
                    lesson_display_order = section_elem.get('DisplayOrder')
                    if lesson_display_order and lesson_display_order.isdigit():
                        lesson_id_padded = get_padded_id(lesson_display_order, 'L')
                    else:
                        lesson_id_padded = get_padded_id(str(section_idx), 'L')
                    lesson_path = f"{section_path}/{lesson_id_padded}"

                    lesson_data = {
                        'Path': lesson_path,
                        'CourseID': course_id_padded,
                        'SectionID': section_id_padded,
                        'LessonID': lesson_id_padded,
                        'CourseOrder': global_order_counter['counter'],
                        'Course': course_name,
                        'SharedCourse': course_name
                    }
                    lesson_data = append_element_attributes(section_elem, lesson_data, "Section")
                    fieldnames['Lesson'].update(lesson_data.keys())
                    data_collections['Lesson'].append(lesson_data)

                    lesson_name = lesson_data.get('Section_Name', '')

                    # Get the list of descendant <File> elements
                    file_elems = section_elem.findall('.//File')
                    for topic_idx, file_elem in enumerate(file_elems):
                        global_order_counter['counter'] += 1  # Increment order
                        topic_id_padded = get_padded_id(str(topic_idx), "T")
                        topic_full_path = f"{lesson_path}/{topic_id_padded}"

                        topic_data = {
                            "Path": topic_full_path,
                            'CourseID': course_id_padded,
                            'SectionID': section_id_padded,
                            'LessonID': lesson_id_padded,
                            'TopicID': topic_id_padded,
                            'CourseOrder': global_order_counter['counter'],
                            'Course': course_name,
                            'Lesson': lesson_name,
                            'SharedCourse': course_name,
                            'SharedLesson': lesson_name
                        }

                        # Prepare topic_file_id
                        topic_file_id = topic_full_path.replace('/', '_')

                        # Append file attributes, passing output_dir and file_id
                        topic_data = append_element_attributes(
                            file_elem, topic_data, "File", output_dir=directory, file_id=topic_file_id
                        )

                        # Get parent element
                        parent_elem = file_elem.getparent()

                        # Determine topic_level
                        if parent_elem.tag == 'Section':
                            topic_level = 0
                        elif parent_elem.tag == 'Content':
                            topic_level = 1
                        else:
                            topic_level = 2  # For deeper nesting

                        topic_data['Level'] = topic_level

                        # Get parent_elem's Type and ContentType attributes
                        parent_type = clean_value(parent_elem.get('Type'), directory, topic_file_id)
                        parent_contentType = clean_value(parent_elem.get('ContentType'), directory, topic_file_id)

                        # Initialize variables
                        topic_specific_data = {}
                        topic_type_not_configured = False

                        # Switch cases based on parent_elem's Type and ContentType attributes:

                        # Multimedia pages:

                        if parent_type == "1" and parent_contentType == "0":
                            # Get and clean the description
                            description = topic_data.get("File_Description", "").strip()
                            if description:
                                # Clean the description before concatenation
                                description = clean_value(description, directory, topic_file_id)
                            else:
                                description = ""

                            # Initialize topic_body
                            topic_body = description

                            # Collect all <Download> elements that are immediate children of parent_elem
                            download_elems = parent_elem.findall('Download')
                            downloads_html = ""
                            if download_elems:
                                downloads_list = []
                                for download_idx, download_elem in enumerate(download_elems, start=1):
                                    download_prefix = f"Download{download_idx}"
                                    topic_data = append_element_attributes(
                                        download_elem, topic_data, download_prefix, directory, topic_file_id
                                    )
                                    download_url = topic_data.get(f"{download_prefix}_Url", "")
                                    download_name = topic_data.get(f"{download_prefix}_Name", "")
                                    download_title = topic_data.get(f"{download_prefix}_Title", "")
                                    if download_url and download_title:
                                        file_ext = os.path.splitext(download_url)[1].upper().lstrip('.')
                                        downloads_list.append(f'<li><a href="{download_url}" title="{download_name}" download>{download_title} ({file_ext})</a></li>')
                                if downloads_list:
                                    downloads_html = "<ul>" + "".join(downloads_list) + "</ul>"

                            # Concatenate description and downloads_html without extra whitespace
                            topic_body = topic_body.strip() + downloads_html.strip()

                            # Clean the entire topic_body
                            topic_body = clean_html_content(topic_body)

                            topic_specific_data = {
                                "Type": "Article",
                                "TypeDescription": "Download page",
                                "FontAwesomeIcon": "newspaper",
                                "Title": clean_value(parent_elem.get("Name", ""), directory, topic_file_id),
                                "Body": topic_body
                            }

                        elif parent_type == "1" and parent_contentType == "1":
                            topic_specific_data = {
                                "Type": "Audio",
                                "TypeDescription": "Audio page",
                                "FontAwesomeIcon": "music"
                            }
                            topic_type_not_configured = True

                        elif parent_type == "1" and parent_contentType == "2":
                            topic_specific_data = {
                                "Type": "Image",
                                "TypeDescription": "Image page",
                                "FontAwesomeIcon": "image"
                            }
                            topic_type_not_configured = True

                        elif parent_type == "1" and parent_contentType == "3":
                            # Video page
                            track_elem = file_elem.find('Track')
                            if track_elem is not None:
                                topic_data = append_element_attributes(track_elem, topic_data, "Track")
                                track_url = topic_data["Track_Url"]
                                track_label = topic_data["Track_Label"]
                                file_url = topic_data["File_Url"]
                                topic_body = f'''<!-- wp:video {{"tracks":[{{"src":"{track_url}","label":"{track_label}","srcLang":"en","kind":"captions"}}]}} -->
<figure class="wp-block-video"><video controls src="{file_url}" crossorigin="anonymous"><track src="{track_url}" label="{track_label}" srclang="en" kind="captions"/></video></figure>
<!-- /wp:video -->'''
                            else:
                                file_url = topic_data["File_Url"]
                                topic_body = f'''<!-- wp:video -->
<figure class="wp-block-video"><video controls src="{file_url}" crossorigin="anonymous"></video></figure>
<!-- /wp:video -->'''

                            topic_specific_data = {
                                "Type": "Video",
                                "TypeDescription": "Video page",
                                "FontAwesomeIcon": "video",
                                "Title": clean_value(parent_elem.get("Name", ""), directory, topic_file_id),
                                "Body": topic_body
                            }

                        elif parent_type == "1" and parent_contentType == "5":
                            topic_specific_data = {
                                "Type": "Slide",
                                "TypeDescription": "Slide page",
                                "FontAwesomeIcon": "file-powerpoint"
                            }
                            topic_type_not_configured = True

                        elif parent_type == "1" and parent_contentType == "6":
                            file_url = topic_data["File_Url"]
                            file_name = topic_data["File_Name"]
                            topic_specific_data = {
                                "Type": "PDF",
                                "TypeDescription": "PDF page",
                                "FontAwesomeIcon": "file-pdf",
                                "Title": clean_value(parent_elem.get("Name", ""), directory, topic_file_id),
                                "Body": f'<p><a href="{file_url}" target="_blank">{file_name}</a></p>'
                            }

                        elif parent_type == "1" and parent_contentType == "11":
                            topic_specific_data = {
                                "Type": "TXT",
                                "TypeDescription": "TXT page",
                                "FontAwesomeIcon": "font"
                            }
                            topic_type_not_configured = True

                        elif parent_type == "1" and parent_contentType == "16":
                            # Multi-video page
                            files_in_parent = parent_elem.findall('File')
                            file_position = files_in_parent.index(file_elem) + 1
                            file_count = len(files_in_parent)

                            file_name = topic_data["File_Name"]
                            parent_name = clean_value(parent_elem.get("Name", ""), directory, topic_file_id)

                            if parent_name and parent_name != "Video Training":
                                if file_name:
                                    if not re.match(r'\w+\d+', file_name):
                                        topic_title = f"{parent_name}: {file_name}"
                                    else:
                                        topic_title = f"{parent_name} ({file_position}/{file_count})"
                                else:
                                    topic_title = f"{parent_name} ({file_position}/{file_count})"
                            else:
                                if file_name and not re.match(r'\w+\d+', file_name):
                                    topic_title = file_name
                                else:
                                    topic_title = parent_name  # Note: If parent_name is empty, topic_title will be empty

                            # If topic_title is empty, set a default title
                            if not topic_title:
                                topic_title = f"Video ({file_position}/{file_count})"

                            track_elem = file_elem.find('Track')
                            if track_elem is not None:
                                topic_data = append_element_attributes(track_elem, topic_data, "Track")
                                track_url = topic_data["Track_Url"]
                                track_label = topic_data["Track_Label"]
                                file_url = topic_data["File_Url"]
                                topic_body = f'''<!-- wp:video {{"tracks":[{{"src":"{track_url}","label":"{track_label}","srcLang":"en","kind":"captions"}}]}} -->
                        <figure class="wp-block-video"><video controls src="{file_url}" crossorigin="anonymous"><track src="{track_url}" label="{track_label}" srclang="en" kind="captions"/></video></figure>
                        <!-- /wp:video -->'''
                            else:
                                file_url = topic_data["File_Url"]
                                topic_body = f'''<!-- wp:video -->
                        <figure class="wp-block-video"><video controls src="{file_url}" crossorigin="anonymous"></video></figure>
                        <!-- /wp:video -->'''

                            topic_specific_data = {
                                "Type": "Video",
                                "TypeDescription": "Multi-video page",
                                "FontAwesomeIcon": "video-plus",
                                "Title": topic_title,
                                "Body": topic_body
                            }

                        elif parent_type == "1" and parent_contentType == "20":
                            topic_specific_data = {
                                "Type": "Activity",
                                "TypeDescription": "Activity page",
                                "FontAwesomeIcon": "user-cog"
                            }
                            topic_type_not_configured = True

                        elif parent_type == "1" and parent_contentType == "22":
                            topic_specific_data = {
                                "Type": "Code Activity",
                                "TypeDescription": "Code Activity page",
                                "FontAwesomeIcon": "laptop-code"
                            }
                            topic_type_not_configured = True

                        # Single-question pages

                        elif parent_type == "2":
                            topic_specific_data = {
                                "Type": "Question",
                                "Title": topic_data["File_Name"],
                                "Body": f"<placeholder>{topic_data["File_Id"]}</placeholder>"
                            }
                            if parent_contentType == "2":
                                topic_specific_data["TypeDescription"] = "Single question page - Drag matching"
                                topic_specific_data["FontAwesomeIcon"] = "clone"
                            elif parent_contentType == "4":
                                topic_specific_data["TypeDescription"] = "Single question page - Multiple choice"
                                topic_specific_data["FontAwesomeIcon"] = "check-circle"
                            elif parent_contentType == "5":
                                topic_specific_data["TypeDescription"] = "Single question page - Multiple selection"
                                topic_specific_data["FontAwesomeIcon"] = "check-square"
                            elif parent_contentType == "7":
                                topic_specific_data["TypeDescription"] = "Single question page - True/false"
                                topic_specific_data["FontAwesomeIcon"] = "toggle-off"
                            else:
                                topic_type_not_configured = True

                        # Pages for test launch

                        elif parent_type == "3" and parent_contentType == "1":
                            settings_elem = parent_elem.find('Settings')
                            if settings_elem is not None:
                                topic_data = append_element_attributes(settings_elem, topic_data, "Settings")

                            topic_specific_data = {
                                "Type": "Test",
                                "TypeDescription": "Test launch page",
                                "FontAwesomeIcon": "file-alt",
                                "Title": clean_value(parent_elem.get("Name", ""), directory, topic_file_id),
                                "Body": f"<h2>{topic_data["File_Name"]}</h2><placeholder>{topic_data["File_Id"]}</placeholder>"
                            }

                        # Lessons (write nothing)

                        elif parent_type == "4" and parent_contentType == "1":
                            parent_elem_type = parent_elem.tag
                            topic_data = append_element_attributes(parent_elem, topic_data, parent_elem_type)
                            topic_specific_data = {
                                "Type": "Section",
                                "TypeDescription": "Unknown",
                                "FontAwesomeIcon": "stream"
                            }
                            print(f"<File> element found directly within a {parent_elem_type} element.")
                            print(json.dumps(topic_data, indent=2))
                            topic_type_not_configured = True

                        # Default case
                        else:
                            # Other cases handled as previously
                            topic_type_not_configured = True

                        # Append whatever data was collected from the switch statements to topic_data
                        topic_data.update(topic_specific_data)
                        fieldnames['Topic'].update(topic_data.keys())

                        if topic_type_not_configured:
                            print("Topic skipped because topic type is not yet configured.")
                            print(json.dumps(topic_data, indent=2))
                        else:
                            # Add topic_data to collection
                            data_collections['Topic'].append(topic_data)

    # After processing all sections, add the JSON array to course_data
    course_data['CourseSections'] = json.dumps(course_sections_json_list)
    fieldnames['Course'].update(['CourseSections'])
    
    # Add course_data to data_collections
    data_collections['Course'].append(course_data)

def write_csv_files(directory, data_collections, fieldnames):
    # Define the desired field order for all CSV files
    core_field_order = [
        'Path', 'CourseID', 'SectionID', 'LessonID', 'TopicID', 'CourseOrder', 'Course', 'Lesson', 'SharedCourse', 'SharedLesson', 'Level', 
        'Type', 'TypeDescription', 'FontAwesomeIcon', 'Title', 'Body',
        'CourseImageOriginalFilename', 'CourseImageOptimizedFilename', 'CourseSections'
    ]

    for name, data_list in data_collections.items():
        if data_list:
            file_path = os.path.join(directory, f"{name}.csv")
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                # Determine the fieldnames for this CSV
                specific_core_fields = [field for field in core_field_order if field in fieldnames[name]]
                # Collect additional dynamic fields
                dynamic_fields = sorted(set(fieldnames[name]) - set(specific_core_fields))
                all_fieldnames = specific_core_fields + dynamic_fields

                writer = csv.DictWriter(f, fieldnames=all_fieldnames, extrasaction='ignore')
                writer.writeheader()
                for data in data_list:
                    writer.writerow(data)

def main():
    directory = get_directory()
    process_xml_files(directory)

if __name__ == "__main__":
    main()
