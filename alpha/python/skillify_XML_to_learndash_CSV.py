import os
import sys
from lxml import etree as ET
import csv
import html

def get_directory():
    directory = input("Please enter the directory containing the XML files: ").strip()
    if not os.path.isdir(directory):
        print(f"The directory '{directory}' does not exist.")
        sys.exit(1)
    return directory

def initialize_csv_files(directory):
    csv_files = {
        'Course': ['Path', 'CourseID', 'Course_RN', 'Course_CourseSummary', 'Course_Video', 'Course_Image', 'Course_Duration', 'Course_CategoryName', 'Course_Level', 'Course_Language', 'Course_Price', 'Course_ProductId', 'Course_CourseName', 'Course_CourseId'],
        'Expert': ['Path', 'CourseID', 'ExpertID', 'Expert_FirstName', 'Expert_LastName', 'Expert_Title', 'Expert_Bio'],
        'Section': ['Path', 'CourseID', 'SectionID', 'Lesson_Id', 'Lesson_Name', 'Lesson_DisplayOrder'],
        'Lesson': ['Path', 'CourseID', 'SectionID', 'LessonID', 'Section_Id', 'Section_Type', 'Section_ContentType', 'Section_Name', 'Section_Pass', 'Section_Take', 'Section_HasBookmark', 'Section_DisplayOrder'],
        'Topic': ['Path', 'CourseID', 'SectionID', 'LessonID', 'TopicID', 'DownloadID', 'VideoElementHtml', 'Content_Id', 'Content_Type', 'Content_ContentType', 'Content_Name', 'Content_Take', 'Content_HasBookmark', 'Content_DisplayOrder', 'Content_Url', 'Content_Guid', 'Content_Time', 'Content_Pass', 'File_Id', 'File_Name', 'File_Description', 'File_Questions', 'File_Time', 'File_Url', 'File_DisplayOrder', 'File_Guid', 'File_ViewGradebook', 'File_Points', 'File_Pages', 'File_SizeKb', 'Settings_EnableRetakes', 'Settings_ForcePassTest', 'Settings_TakeInOrder', 'Settings_SaveAndResume', 'Settings_Resumes', 'Settings_IsTimed', 'Settings_DefaultTime', 'Settings_ShowFeedback', 'Settings_ShowAnswers', 'Settings_AllowRetakes', 'Settings_Retakes', 'Settings_ShowStudyGuide', 'Settings_IsPooling', 'Settings_PoolSize', 'Settings_IsProctored', 'Settings_UseAnyProctor', 'Settings_ProctorId', 'Settings_IsFullScreen', 'Download_Id', 'Download_Name', 'Download_Title', 'Download_Url', 'Download_SizeKb', 'Track_MediaId', 'Track_Label', 'Track_Name', 'Track_Url']
    }

    csv_writers = {}
    for name, headers in csv_files.items():
        file_path = os.path.join(directory, f"{name}.csv")
        f = open(file_path, 'w', newline='', encoding='utf-8-sig')  # Using utf-8-sig for better compatibility
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        csv_writers[name] = {'file': f, 'writer': writer}
    return csv_writers

def clean_value(value):
    if value:
        # Replace line breaks with spaces
        value = ' '.join(value.split())
        # Convert double-HTML-encoded values to standard HTML
        # For example, "&lt;div&gt;" to "<div>"
        # Unescape twice to handle double encoding
        value = html.unescape(html.unescape(value))
        return value
    return value

def get_padded_id(value, prefix):
    if value and value.isdigit():
        padded_id = f"{prefix}-{int(value):0>4}"
    else:
        padded_id = f"{prefix}-{value}"
    return padded_id

def generate_video_element_html(file_url, track_url):
    video_element_html = f'''<!-- wp:video {{"tracks":[{{"src":"{track_url}","label":"English","srcLang":"en","kind":"captions"}}]}} --> 
<figure class="wp-block-video"><video controls src="{file_url}" crossorigin="anonymous"><track src="{track_url}" label="English" srclang="en" kind="captions"/></video></figure> 
<!-- /wp:video -->'''
    return video_element_html

def process_xml_files(directory, csv_writers):
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
                process_course(course, csv_writers)
        except ET.ParseError as e:
            print(f"Error parsing '{xml_file}': {e}")
            continue

def process_course(course_elem, csv_writers):
    course_id_value = course_elem.findtext('CourseId')
    if not course_id_value or not course_id_value.isdigit():
        print(f"Warning: Skipping course with missing or invalid <CourseId>.")
        return
    course_id_padded = get_padded_id(course_id_value, 'C')
    course_path = course_id_padded

    # Skillify term: Courses
    # LearnDash term: Courses
    # Process values belonging to <Course>.
    # All values are stored in elements, not attributes.
    # To be saved in Course.csv
    course_data = {
        'Path': course_path,
        'CourseID': course_id_padded
    }
    for child in course_elem:
        if len(child) == 0 and child.text:
            field_name = f"Course_{child.tag}"
            course_data[field_name] = clean_value(child.text.strip()) if child.text else ''
    csv_writers['Course']['writer'].writerow(course_data)

    # Skillify term: Experts
    # LearnDash term: Authors
    # Process values belonging to the <Expert> elements in <Course><Experts>
    # All values are stored in elements, not attributes.
    # To be saved in Expert.csv
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
            for child in expert_elem:
                field_name = f"Expert_{child.tag}"
                expert_data[field_name] = clean_value(child.text.strip()) if child.text else ''
            csv_writers['Expert']['writer'].writerow(expert_data)

    # Skillify Term: Lessons
    # LearnDash Term: Sections
    # Process values belonging to the <Lesson> elements in <Course><Outline><Lessons>
    # All values are stored in attributes, not elements.
    # To be saved in Section.csv
    outline_elem = course_elem.find('Outline')
    if outline_elem is not None:
        lessons_elem = outline_elem.find('Lessons')
        if lessons_elem is not None:
            lesson_list = lessons_elem.findall('Lesson')
            for lesson_idx, lesson_elem in enumerate(lesson_list):
                lesson_display_order = lesson_elem.get('DisplayOrder')
                if lesson_display_order and lesson_display_order.isdigit():
                    section_id_padded = get_padded_id(lesson_display_order, 'S')
                else:
                    section_id_padded = get_padded_id(str(lesson_idx), 'S')
                section_path = f"{course_path}/{section_id_padded}"
                section_data = {
                    'Path': section_path,
                    'CourseID': course_id_padded,
                    'SectionID': section_id_padded
                }
                for attr in lesson_elem.attrib:
                    field_name = f"Lesson_{attr}"
                    section_data[field_name] = clean_value(lesson_elem.attrib[attr])
                csv_writers['Section']['writer'].writerow(section_data)

                # Skillify Term: Sections
                # LearnDash Term: Lessons
                # Process values belonging to the <Section> elements in <Course><Outline><Lessons><Lesson>
                # All values are stored in attributes, not elements.
                # To be saved in Lessons.csv
                section_list = lesson_elem.findall('Section')
                for section_idx, section_elem in enumerate(section_list):
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
                    }
                    for attr in section_elem.attrib:
                        field_name = f"Section_{attr}"
                        lesson_data[field_name] = clean_value(section_elem.attrib[attr])

                    csv_writers['Lesson']['writer'].writerow(lesson_data)

                    # Skillify terms: Content, Files, and Downloads
                    # LearnDash term: Topics
                    # Process values belonging to the <File> elements and their sibling and parent elements within <Courses><Course><Outline><Lessons><Lesson><Section>
                    # Values are stored in the attributes of the elements, as well as in the attributes of sibling, parent, and child elements
                    # To be saved in Topics.csv

                    # Initialize Topic Counter for this Lesson
                    topic_counter = -1

                    # Get the list of child elements of section_elem, to process them in order
                    section_children = list(section_elem)

                    i = 0
                    while i < len(section_children):
                        child_elem = section_children[i]
                        if child_elem.tag == 'Content':
                            content_elem = child_elem
                            # Process Files within Content
                            content_file_elems = content_elem.findall('File')
                            for file_elem in content_file_elems:
                                topic_counter += 1
                                topic_id_padded = get_padded_id(str(topic_counter), 'T')
                                topic_path = f"{lesson_path}/{topic_id_padded}"
                                topic_data = {
                                    'Path': topic_path,
                                    'CourseID': course_id_padded,
                                    'SectionID': section_id_padded,
                                    'LessonID': lesson_id_padded,
                                    'TopicID': topic_id_padded,
                                }
                                # File attributes
                                for attr in file_elem.attrib:
                                    field_name = f"File_{attr}"
                                    topic_data[field_name] = clean_value(file_elem.attrib[attr])

                                # Settings
                                settings_elem = file_elem.find('Settings')
                                if settings_elem is not None:
                                    for attr in settings_elem.attrib:
                                        field_name = f"Settings_{attr}"
                                        topic_data[field_name] = clean_value(settings_elem.attrib[attr])

                                # Content attributes
                                for attr in content_elem.attrib:
                                    field_name = f"Content_{attr}"
                                    topic_data[field_name] = clean_value(content_elem.attrib[attr])

                                # Track
                                track_elem = file_elem.find('Track')
                                if track_elem is not None:
                                    for attr in track_elem.attrib:
                                        field_name = f"Track_{attr}"
                                        topic_data[field_name] = clean_value(track_elem.attrib[attr])

                                # Generate VideoElementHtml if both File_Url and Track_Url are present
                                if 'File_Url' in topic_data and 'Track_Url' in topic_data and topic_data['File_Url'] and topic_data['Track_Url']:
                                    topic_data['VideoElementHtml'] = generate_video_element_html(topic_data['File_Url'], topic_data['Track_Url'])

                                # Write the topic data to Topic.csv
                                csv_writers['Topic']['writer'].writerow(topic_data)
                            i += 1  # Move to next child
                        elif child_elem.tag == 'File':
                            file_elem = child_elem
                            topic_counter += 1
                            topic_id_padded = get_padded_id(str(topic_counter), 'T')
                            topic_path = f"{lesson_path}/{topic_id_padded}"
                            topic_data = {
                                'Path': topic_path,
                                'CourseID': course_id_padded,
                                'SectionID': section_id_padded,
                                'LessonID': lesson_id_padded,
                                'TopicID': topic_id_padded,
                            }
                            # File attributes
                            for attr in file_elem.attrib:
                                field_name = f"File_{attr}"
                                topic_data[field_name] = clean_value(file_elem.attrib[attr])

                            # Settings
                            settings_elem = file_elem.find('Settings')
                            if settings_elem is not None:
                                for attr in settings_elem.attrib:
                                    field_name = f"Settings_{attr}"
                                    topic_data[field_name] = clean_value(settings_elem.attrib[attr])

                            # Check for following <Download> siblings
                            download_counter = -1
                            i += 1  # Move to next child
                            while i < len(section_children) and section_children[i].tag == 'Download':
                                download_elem = section_children[i]
                                download_counter += 1
                                download_id_padded = get_padded_id(str(download_counter), 'D')
                                topic_data_with_download = topic_data.copy()
                                topic_data_with_download['DownloadID'] = download_id_padded
                                for attr in download_elem.attrib:
                                    field_name = f"Download_{attr}"
                                    topic_data_with_download[field_name] = clean_value(download_elem.attrib[attr])
                                topic_path_with_download = f"{lesson_path}/{topic_id_padded}/{download_id_padded}"
                                topic_data_with_download['Path'] = topic_path_with_download

                                # Generate VideoElementHtml if both File_Url and Track_Url are present
                                if 'File_Url' in topic_data_with_download and 'Track_Url' in topic_data_with_download and topic_data_with_download['File_Url'] and topic_data_with_download['Track_Url']:
                                    topic_data_with_download['VideoElementHtml'] = generate_video_element_html(topic_data_with_download['File_Url'], topic_data_with_download['Track_Url'])

                                # Write the topic data to Topic.csv
                                csv_writers['Topic']['writer'].writerow(topic_data_with_download)
                                i += 1  # Move to next child
                            if download_counter == -1:
                                # Generate VideoElementHtml if both File_Url and Track_Url are present
                                if 'File_Url' in topic_data and 'Track_Url' in topic_data and topic_data['File_Url'] and topic_data['Track_Url']:
                                    topic_data['VideoElementHtml'] = generate_video_element_html(topic_data['File_Url'], topic_data['Track_Url'])
                                # No downloads, write topic_data as is
                                csv_writers['Topic']['writer'].writerow(topic_data)
                            # No need to increment i here since it's already moved
                        else:
                            # Other elements, skip or handle accordingly
                            print(f"Warning: Contains a '{child_elem.tag}' element in a <Section>.")
                            i += 1  # Move to next child

def main():
    directory = get_directory()
    csv_writers = initialize_csv_files(directory)
    try:
        process_xml_files(directory, csv_writers)
    finally:
        # Close all CSV files
        for writer_info in csv_writers.values():
            writer_info['file'].close()

if __name__ == "__main__":
    main()
