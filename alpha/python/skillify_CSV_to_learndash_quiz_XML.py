import re
from html import unescape

import csv
from lxml import etree as ET
from lxml.etree import CDATA

import json
from collections import defaultdict

from bs4 import BeautifulSoup

################################################################################################################################

def load_csv_as_list_of_dicts(filename):
    with open(filename, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

################################################################################################################################

# REVISIT 4/4: truncate reference to only the first breadcrumb, which will end up being equivalent to ^(<.+?>)?((not line break, not &nbsp, not <blah>)*)
def standardize_question_reference(reference_str):
    # Converts a raw QuestionReference (potentially containing HTML tags, 
    # multiple lines, extra spaces) into a single standardized breadcrumb-like 
    # string: 'Heading 1 > Heading 2 > Heading 3...'

    # :param reference_str: The raw string from QuestionReference column.
    # :return: A cleaned string with headings joined by ' > '.

    if not reference_str or reference_str.strip() == "0":
        # If the value is empty or literally '0', just return it as-is or handle as needed
        return reference_str.strip()

    # 1) Unescape any HTML entities (like &nbsp;, &amp;, etc.)
    ref_unescaped = unescape(reference_str)

    # 2) Replace <br> tags (if any) with a special delimiter to ensure we separate those too
    ref_unescaped = re.sub(r'<br\s*/?>', '\n', ref_unescaped, flags=re.IGNORECASE)

    # 3) Replace block-level tags <p>, <div>, etc. with a uniform delimiter (e.g. '\n')
    #    We'll consider each block-level tag a new "heading" line.
    #    The pattern below also captures the closing tags: </p>, </div>, etc.
    ref_unescaped = re.sub(r'</?(p|div|h[1-6]|section|article|blockquote)[^>]*>', '\n', ref_unescaped, flags=re.IGNORECASE)

    # 4) Remove any remaining HTML tags entirely.
    #    This should clear out <span>, <o:p>, <strong>, style attributes, etc.
    ref_unescaped = re.sub(r'<[^>]+>', '', ref_unescaped)

    # 5) Split on line breaks to isolate potential headings.
    lines = re.split(r'[\r\n]+', ref_unescaped)

    # 6) Clean each line: remove extra spaces, leftover HTML codes, etc.
    cleaned_lines = []
    for line in lines:
        # Replace multiple spaces (including &nbsp;) with a single space
        # (Though we already unescaped &nbsp;, so now they are actual spaces)
        line = re.sub(r'\s+', ' ', line).strip()
        if line:
            cleaned_lines.append(line)

    # 7) Join them with ' > ' to create the breadcrumb-like format
    breadcrumb = " > ".join(cleaned_lines)

    return breadcrumb

################################################################################################################################

def writeAnswer(element, options):
    answer_elt = ET.SubElement(element, "answer")

    # XML: /wpProQuiz/data/quiz/questions/question/answers/answer/@points
    # 0
    # 1+ if /wpProQuiz/data/quiz/questions/question/answerPointsActivated=true
    answer_elt.set("points", options["points"])

    # XML: /wpProQuiz/data/quiz/questions/question/answers/answer/@correct
    # false = incorrect
    # true = correct
    answer_elt.set("correct", options["correct"])

    # XML: /wpProQuiz/data/quiz/questions/question/answers/answer/@gradingProgression
    # not-graded-none = Not graded, no points awarded (""This response will be reviewed and graded after submission."")
    # not-graded-full = Not graded, full points awarded (""This response will be awarded full points automatically, but it will be reviewed and possibly adjusted after submission."")
    # graded-full = Graded, full points awarded (""This response will be awarded full points automatically, but it can be reviewed and adjusted after submission."")
    if options["gradingProgression"] is not None:
        answer_elt.set("gradingProgression", options["gradingProgression"])

    # XML: /wpProQuiz/data/quiz/questions/question/answers/answer/@gradedType
    # text = Text box
    # upload = Upload
    if options["gradedType"] is not None:
        answer_elt.set("gradedType", options["gradedType"])

    # XML: /wpProQuiz/data/quiz/questions/question/answers/answer/answerText
    # Text 
    # HTML (set @html to true)
    answerText_elt = ET.SubElement(answer_elt, 'answerText')
    answerText_elt.text = CDATA(options["answerText"])

    # XML: /wpProQuiz/data/quiz/questions/question/answers/answer/answerText/@html
    # false = plain text
    # true = HTML
    # An audit of all answers showed that the only answers with HTML elements in them are intended to be displayed as literal code, not rendered.
    answerText_elt.set('html', options["answerText_html"])

    # XML: /wpProQuiz/data/quiz/questions/question/answers/answer/stortText
    # sort text
    # Always blank
    stortText_elt = ET.SubElement(answer_elt, 'stortText')
    stortText_elt.text = CDATA(options["stortText"])

    # XML: /wpProQuiz/data/quiz/questions/question/answers/answer/stortText/@html
    # Always true
    stortText_elt.set('html', options["stortText_html"])

################################################################################################################################
################################################################################################################################
################################################################################################################################

def main():
    # 1) Read your CSV data
    tests_csv = load_csv_as_list_of_dicts('LK_Tests.csv')
    questions_csv = load_csv_as_list_of_dicts('LK_Questions.csv')
    answers_csv = load_csv_as_list_of_dicts('LK_Answers.csv')

    # 2) Group questions and answers for easy lookup
    questions_by_test = defaultdict(list)
    for q in questions_csv:
        questions_by_test[q['TestId']].append(q)

    answers_by_test_question = defaultdict(list)
    for a in answers_csv:
        answers_by_test_question[(a['TestId'], a['QuestionId'])].append(a)

    # 3) Build the final XML (which includes a JSON string in <meta_value>) for each Test
    for test_row in tests_csv:
        # --- Create the root / top-level structure ---
        root = ET.Element('wpProQuiz')
        data_elt = ET.SubElement(root, 'data')
        quiz_elt = ET.SubElement(data_elt, 'quiz')
        # We'll also build a partial “quiz_json” to store in meta_value
        quiz_json = {}

        ################################################################################################################################
        ################################################################################################################################
        ################################################################################################################################

        # XML: /wpProQuiz/data/quiz/title
        # Title of the quiz
        # Quiz > Quiz page > Title
        # Text
        xml_title = ET.SubElement(quiz_elt, 'title')
        xml_title.text = CDATA(f"{test_row['CourseId']}: {test_row['TestName']}")

        # XML: /wpProQuiz/data/quiz/title/@titleHidden
        # JSON: sfwd-quiz_titleHidden
        # A second quiz title will be displayed on the Quiz Post. This option is recommended if displaying Quizzes via Shortcode. The Quiz Title is displayed in addition to the Quiz Post title. Recommended for quiz shortcode usage.
        # Quiz > Settings > Display and Content Options > Quiz Title
        # true = hidden
        # false = shown
        xml_title.set('titleHidden', 'true')
        quiz_json["sfwd-quiz_titleHidden"] = 'true'

        # Required text
        # XML: /wpProQuiz/data/quiz/text
        # N/A
        # AAZZAAZZ
        ET.SubElement(quiz_elt, 'text').text = CDATA('AAZZAAZZ')

        # XML: /wpProQuiz/data/quiz/resultText/@gradeEnabled
        # JSON: sfwd-quiz_resultGradeEnabled
        # When enabled, the first message will be displayed to ALL users. To customize the message based on earned score, add new Graduation Levels and set the 'From' field to the desired grade.
        # Quiz > Settings > Results Page Display > Result Message(s)
        # true = shown
        # false = hidden
        xml_resultText = ET.SubElement(quiz_elt, 'resultText')
        xml_resultText.set('gradeEnabled', 'true')

        # XML: /wpProQuiz/data/quiz/resultText/text
        # JSON: sfwd-quiz_resultText
        # Quiz result text. Becomes <resultText><text> entries, but data not recorded in sfwd data
        # Quiz > Settings > Results Page Display > Result Message(s) > The message below is displayed on the Quiz results page.
        # Text, but not recorded in JSON
        xml_resultText_text = ET.SubElement(xml_resultText, 'text')
        xml_resultText_text.text = CDATA('')
        quiz_json["sfwd-quiz_resultText"] = "" # Even if more than one resultText exists, only one blank JSON key is written.

        # XML: /wpProQuiz/data/quiz/resultText/text/@prozent
        # Quiz result text floor score.
        # Quiz > Settings > Results Page Display > Result Message(s) > The message below is displayed on the Quiz results page. > From % score, display this message:
        # 0+
        xml_resultText_text.set('prozent','0')

        # JSON: sfwd-quiz_quiz_pro
        # Automatically assigned settings template; new ID generated for each quiz unless otherwise specified.
        # Quiz > Settings > (hidden)
        # Number
        quiz_json["sfwd-quiz_quiz_pro"] = ""

        # JSON: sfwd-quiz_course
        # Search or select a Course
        # Quiz > Settings > Quiz Access Settings > Associated Course
        # ?
        quiz_json["sfwd-quiz_course"] = "" # Don't know how to use this yet. I assume that leaving it blank is correct and that the importer will ask which course to assign it to or that the course builder will import the quiz.

        # JSON: sfwd-quiz_lesson
        # Search or select a Lesson or Topic
        # Quiz > Settings > Quiz Access Settings > Associated Lesson
        # ?
        quiz_json["sfwd-quiz_lesson"] = "" # Same note as sfwd-quiz_course

        # JSON: sfwd-quiz_lesson_schedule
        # Quiz > Settings > Quiz Access Settings > Quiz Release Schedule
        # "" = Immediately: the quiz is made available on course enrollment.
        # "visible_after" = Enrollment-based: the quiz will be available X days after course enrollment.
        # "visible_after_specific_date" = The quiz will be available on a specific date
        quiz_json["sfwd-quiz_lesson_schedule"] = ""

        # JSON: sfwd-quiz_visible_after
        # The quiz will be available X days after course enrollment
        # Quiz > Settings > Quiz Access Settings > Quiz Release Schedule > Enrollment-based > day(s)
        # ""
        # "0"+
        quiz_json["sfwd-quiz_visible_after"] = ""

        # JSON: sfwd-quiz_visible_after_specific_date
        # The quiz will be available on a specific date
        # Quiz > Settings > Quiz Access Settings > Quiz Release Schedule > Specific date > MMDDYYYYHHMN
        # ""
        # "0"-"2147483647"
        quiz_json["sfwd-quiz_visible_after_specific_date"] = ""

        # JSON: sfwd-quiz_external
        # Whether a quiz takes place in a virtual setting (e.g, Zoom) or in-person.
        # Quiz > Settings > Quiz Access Settings > External Quiz
        # "" = native
        # "on" = external
        quiz_json["sfwd-quiz_external"] = ""

        # JSON: sfwd-quiz_external_type
        # Whether a quiz takes place in a virtual setting (e.g, Zoom) or in-person.
        # Quiz > Settings > Quiz Access Settings > External Quiz > Type
        # ""
        # "virtual" = This quiz takes place in a virtual setting (e.g., Zoom).
        # "in-person" = This quiz takes place in-person.
        quiz_json["sfwd-quiz_external_type"] = ""

        # JSON: sfwd-quiz_external_require_attendance
        # If attendance is required the student will not be able to continue in the course until they have been marked by an admin or group leader that they have attended the virtual or in-person quiz. If attendance is not required the student will be able to continue the course without requiring to be marked as attending the virtual or in-person quiz.
        # Quiz > Settings > Quiz Access Settings > External Quiz > Require Attendance
        # "" = attendance not required
        # "yes" = require attendance
        quiz_json["sfwd-quiz_external_require_attendance"] = ""

        # XML: /wpProQuiz/data/quiz/prerequisite
        # JSON: sfwd-quiz_prerequisite
        # Select one or more quizzes that must be completed prior to taking this quiz.
        # Quiz > Settings > Quiz Access Settings > Quiz Prerequisites
        # "" or false = none
        # true = prerequisites exist
        ET.SubElement(quiz_elt, 'prerequisite').text = 'false'
        quiz_json["sfwd-quiz_prerequisite"] = ""

        # JSON: sfwd-quiz_prerequisiteList
        # Select one or more quizzes that must be completed prior to taking this quiz.
        # Quiz > Settings > Quiz Access Settings > Quiz Prerequisites
        # ["1","2"] = quiz 1 and 2 must be completed first
        quiz_json["sfwd-quiz_prerequisiteList"] = ""

        # XML: /wpProQuiz/data/quiz/startOnlyRegisteredUser
        # JSON: sfwd-quiz_startOnlyRegisteredUser
        # This option is especially useful if administering Quizzes via shortcodes on non-course pages, or if your Course are open but you wish only authenticated users to take the Quiz.
        # Quiz > Settings > Quiz Access Settings > Allowed users > Only registered users can take this Quiz
        # false = open to unregistered users
        # true = require authentication
        ET.SubElement(quiz_elt, 'startOnlyRegisteredUser').text = 'false'
        quiz_json["sfwd-quiz_startOnlyRegisteredUser"] = False

        # JSON: sfwd-quiz_passingpercentage
        # Passing percentage (e.g. 80)
        # Quiz > Settings > Progression and Restriction Settings > Passing Score
        # "0"-"100"
        quiz_json["sfwd-quiz_passingpercentage"] = "80"

        # REVISIT (BL)
        # JSON: sfwd-quiz_certificate
        # Search or select a certificate
        # Quiz > Settings > Progression and Restriction Settings > Quiz Certificate
        # "1" = use certificate 1
        quiz_json["sfwd-quiz_certificate"] = ""

        # JSON: sfwd-quiz_threshold
        # Set the score needed to receive a certificate. This can be different from the "Passing Score".
        # Quiz > Settings > Progression and Restriction Settings > Quiz Certificate > Certificate Awarded for
        # "0"-"100"
        quiz_json["sfwd-quiz_threshold"] = "80"

        # JSON: sfwd-quiz_quiz_resume
        # Quiz saving allows your users to save their current Quiz progress and return to it at a later date and preserve their progress. Progress will be saved to the server
        # Quiz > Settings > Progression and Restriction Settings > Enable Quiz Saving
        # false = no resume
        # true = allow resume
        quiz_json["sfwd-quiz_quiz_resume"] = test_row["SaveAndResume"]

        # JSON: sfwd-quiz_quiz_resume_cookie_send_timer
        # Save quiz data to the server every X seconds
        # Quiz > Settings > Progression and Restriction Settings > Enable Quiz Saving > Save Quiz data to the server every
        # 1+
        quiz_json["sfwd-quiz_quiz_resume_cookie_send_timer"] = 20

        # JSON: sfwd-quiz_retry_restrictions
        # Restrict quiz retakes
        # Quiz > Settings > Progression and Restriction Settings > Restrict Quiz Retakes
        # "" = not restricted
        # "on" = restricted
        quiz_json["sfwd-quiz_retry_restrictions"] = ""

        # XML: /wpProQuiz/data/quiz/quizRunOnce
        # JSON: sfwd-quiz_quizRunOnce
        # Restrict quiz retakes
        # Quiz > Settings > Progression and Restriction Settings > Restrict Quiz Retakes
        # false = not restricted
        # true = restricted
        xml_quizRunOnce = ET.SubElement(quiz_elt, 'quizRunOnce').text = 'false'
        quiz_json["sfwd-quiz_quizRunOnce"] = False

        # XML: /wpProQuiz/data/quiz/quizRunOnce/@time
        # JSON: sfwd-quiz_repeats
        # You must input a whole number value or leave blank to default to 0.
        # Quiz > Settings > Progression and Restriction Settings > Restrict Quiz Retakes > Number of Retries Allowed
        # 0+
        xml_quizRunOnce.set('time', test_row["Resumes"])
        quiz_json["sfwd-quiz_repeats"] = test_row["Resumes"]

        # (allow unlimited retakes, none for unregistered users)
        # XML: /wpProQuiz/data/quiz/quizRunOnce/@type
        # JSON: sfwd-quiz_quizRunOnceType
        # Retries applicable to
        # Quiz > Settings > Progression and Restriction Settings > Restrict Quiz Retakes > Retries Applicable to
        # 1 or "1" = All users
        # 2 or "2" = Registered users only
        # 3 or "3" = Anonymous user only
        xml_quizRunOnce.set('type', '0')
        quiz_json["sfwd-quiz_quizRunOnceType"] = ""

        # XML: /wpProQuiz/data/quiz/quizRunOnce/@cookie
        # JSON: sfwd-quiz_quizRunOnceCookie
        # Use a cookie to restrict anonymous visitors; option hidden; always true.
        # Quiz > Settings > Progression and Restriction Settings > Restrict Quiz Retakes > Use a cookie to restrict anonymous visitors (hidden)
        # "" or false = don't use cookies
        # true = use cookies
        xml_quizRunOnce.set('cookie', 'true')
        quiz_json["sfwd-quiz_quizRunOnceCookie"] = True

        # XML: /wpProQuiz/data/quiz/forcingQuestionSolve
        # JSON: sfwd-quiz_forcingQuestionSolve
        # All questions required to complete
        # Quiz > Settings > Progression and Restriction Settings > Question Completion > All Questions required to complete
        # false = answers required
        # true = can skip
        ET.SubElement(quiz_elt, 'forcingQuestionSolve').text = 'false'
        quiz_json["sfwd-quiz_forcingQuestionSolve"] = False

        # JSON: sfwd-quiz_quiz_time_limit_enabled
        # Time limit enabled
        # Quiz > Settings > Progression and Restriction Settings > Time Limit
        # "" = no time limit
        # "on" = time limit enabled
        quiz_json["sfwd-quiz_quiz_time_limit_enabled"] = ""

        # XML: /wpProQuiz/data/quiz/timeLimit
        # JSON: sfwd-quiz_timeLimit
        # Automatically submit after X seconds
        # Quiz > Settings > Progression and Restriction Settings > Time Limit > Automatically Submit After
        # 0 = none
        # 1+
        ET.SubElement(quiz_elt, 'timeLimit').text = '0'
        quiz_json["sfwd-quiz_timeLimit"] = 0

        # JSON: sfwd-quiz_quiz_materials_enabled
        # List and display support materials for the quiz. This is visible to any user having access to the quiz.
        # Quiz > Settings > Display and Content Options > Quiz Materials
        # "" = hide support materials
        # "on" = show support materials
        quiz_json["sfwd-quiz_quiz_materials_enabled"] = ""

        # JSON: sfwd-quiz_quiz_materials
        # Any content added below is displayed on the Quiz page
        # Quiz > Settings > Display and Content Options > Quiz Materials > Any content added below is displayed on the Quiz page
        # HTML content
        quiz_json["sfwd-quiz_quiz_materials"] = ""

        # XML: /wpProQuiz/data/quiz/autostart
        # JSON: sfwd-quiz_autostart
        # Start automatically, without the "Start Quiz" button
        # Quiz > Settings > Display and Content Options > Autostart
        # false = enable "Start Quiz" button
        # true = start automatically
        ET.SubElement(quiz_elt, 'autostart').text = 'false'
        quiz_json["sfwd-quiz_autostart"] = False

        # XML: /wpProQuiz/data/quiz/quizModus
        # JSON: sfwd-quiz_quizModus
        # Question display
        # Quiz > Settings > Display and Content Options > Question Display
        # 0 = one question at a time
        # 1 = one question at a time with Back button
        # 2 = one question at a time with results after each submitted answer
        # 3 = All questions at once (or paginated)
        xml_quizModus = ET.SubElement(quiz_elt, 'quizModus')
        xml_quizModus.text = '0'
        quiz_json["sfwd-quiz_quizModus"] = 0

        # JSON: sfwd-quiz_quizModus_single_feedback
        # Display results at the end only
        # Quiz > Settings > Display and Content Options > Question Display > One question at a time > Display results at the end only
        # blank = default
        # "end" = Display results at the end only
        # "each" = Display results after each submitted answer
        if test_row["ShowFeedback"]:
            quiz_json["sfwd-quiz_quizModus_single_feedback"] = "each"
        else:
            quiz_json["sfwd-quiz_quizModus_single_feedback"] = ""

        # JSON: sfwd-quiz_quizModus_single_back_button
        # Display Back button
        # Quiz > Settings > Display and Content Options > Question Display > One question at a time > Display results at the end only > Display Back button
        # "" = hide Back button
        # "on" = display Back button
        quiz_json["sfwd-quiz_quizModus_single_back_button"] = ""

        # XML: /wpProQuiz/data/quiz/quizModus/@questionsPerPage
        # JSON: sfwd-quiz_quizModus_multiple_questionsPerPage
        # Questions per page (only for quizModus type 3)
        # Quiz > Settings > Display and Content Options > Question Display > All questions at once (or paginated) > questions per page (0 = all)
        # 0 = all
        # 1+
        xml_quizModus.set('questionsPerPage','0')
        quiz_json["sfwd-quiz_quizModus_multiple_questionsPerPage"] = 0

        # XML: /wpProQuiz/data/quiz/showReviewQuestion
        # JSON: sfwd-quiz_showReviewQuestion
        # An overview table will be shown for all questions.
        # Quiz > Settings > Display and Content Options > Question Overview Table
        # false = no table
        # true = show table
        ET.SubElement(quiz_elt, 'showReviewQuestion').text = 'false'
        quiz_json["sfwd-quiz_showReviewQuestion"] = False

        # XML: /wpProQuiz/data/quiz/quizSummaryHide
        # JSON: sfwd-quiz_quizSummaryHide
        # Display a summary table before submission
        # Quiz > Settings > Display and Content Options > Question Overview Table > Quiz Summary
        # true = hidden
        # false = shown
        ET.SubElement(quiz_elt, 'quizSummaryHide').text = 'false' # default true
        quiz_json["sfwd-quiz_quizSummaryHide"] = False

        # XML: /wpProQuiz/data/quiz/skipQuestionDisabled
        # JSON: sfwd-quiz_skipQuestionDisabled
        # Display skip button. Must use the ""One question at a time"" and ""Display results after each submitted answer"" settings in the Question Display setting above. (only valid if sfwd-quiz_quizModus_single_feedback = ""each"" and
        # sfwd-quiz_quizModus = 2)
        # Quiz > Settings > Display and Content Options > Question Overview Table > Skip Question
        # true = shown
        # false = hidden
        ET.SubElement(quiz_elt, 'skipQuestionDisabled').text = 'true'
        quiz_json["sfwd-quiz_skipQuestionDisabled"] = True

        # JSON: sfwd-quiz_custom_sorting
        # Custom question ordering
        # Quiz > Settings > Display and Content Options > Custom Question Ordering
        # "" = false
        # "on" = true
        quiz_json["sfwd-quiz_custom_sorting"] = ""

        # XML: /wpProQuiz/data/quiz/sortCategories
        # JSON: sfwd-quiz_sortCategories
        # Sort by category
        # Quiz > Settings > Display and Content Options > Custom Question Ordering > Sort by Category
        # false = don't sort
        # true = sort
        ET.SubElement(quiz_elt, 'sortCategories').text = 'false'
        quiz_json["sfwd-quiz_sortCategories"] = False

        # XML: /wpProQuiz/data/quiz/questionRandom
        # JSON: sfwd-quiz_questionRandom
        # Randomize order
        # Quiz > Settings > Display and Content Options > Custom Question Ordering > Randomize Order
        # false = randomize
        # true = don't randomize
        ET.SubElement(quiz_elt, 'questionRandom').text = 'false'
        quiz_json["sfwd-quiz_questionRandom"] = False

        # XML: /wpProQuiz/data/quiz/showMaxQuestion
        # JSON: sfwd-quiz_showMaxQuestion
        # In randomized quiz, display subset of questions
        # Quiz > Settings > Display and Content Options > Custom Question Ordering > Randomize Order
        # "" or false = Display all questions
        # true = Display subset of questions
        xml_showMaxQuestion = ET.SubElement(quiz_elt, 'showMaxQuestion')
        xml_showMaxQuestion.text = 'false'
        quiz_json["sfwd-quiz_showMaxQuestion"] = ""

        # XML: /wpProQuiz/data/quiz/showMaxQuestion/@showMaxQuestionValue
        # JSON: sfwd-quiz_showMaxQuestionValue
        # In randomized quiz, limit subset to X questions
        # Quiz > Settings > Display and Content Options > Custom Question Ordering > Randomize Order > Display subset of questions > out of [totalNum] questions
        # 0 = all questions
        # 1+
        xml_showMaxQuestion.set('showMaxQuestionValue', '0')
        quiz_json["sfwd-quiz_showMaxQuestionValue"] = 0

        # JSON: sfwd-quiz_custom_question_elements
        # Enable additional question options. Any enabled elements below will be displayed in each Question
        # Quiz > Settings > Display and Content Options > Additional Question Options
        # "" = No additional question elements shown
        # "on" = Display additional question elements
        quiz_json["sfwd-quiz_custom_question_elements"] = ""

        # XML: /wpProQuiz/data/quiz/showPoints
        # JSON: sfwd-quiz_showPoints
        # Display point value in each question
        # Quiz > Settings > Display and Content Options > Additional Question Options > Point Value
        # false = hidden
        # true = shown
        ET.SubElement(quiz_elt, 'showPoints').text = 'false'
        quiz_json["sfwd-quiz_showPoints"] = False

        # XML: /wpProQuiz/data/quiz/showCategory
        # JSON: sfwd-quiz_showCategory
        # Display question category in each question
        # Quiz > Settings > Display and Content Options > Additional Question Options > Question Category
        # false = hidden
        # true = shown
        ET.SubElement(quiz_elt, 'showCategory').text = 'false'
        quiz_json["sfwd-quiz_showCategory"] = False

        # XML: /wpProQuiz/data/quiz/hideQuestionPositionOverview
        # JSON: sfwd-quiz_hideQuestionPositionOverview
        # Display question position in each question
        # Quiz > Settings > Display and Content Options > Additional Question Options > Question Position
        # false = hidden
        # true = shown
        ET.SubElement(quiz_elt, 'hideQuestionPositionOverview').text = 'true'
        quiz_json["sfwd-quiz_hideQuestionPositionOverview"] = True

        # XML: /wpProQuiz/data/quiz/hideQuestionNumbering
        # JSON: sfwd-quiz_hideQuestionNumbering
        # Display question numbering in each question
        # Quiz > Settings > Display and Content Options > Additional Question Options > Question Numbering
        # false = hidden
        # true = shown
        ET.SubElement(quiz_elt, 'hideQuestionNumbering').text = 'true'
        quiz_json["sfwd-quiz_hideQuestionNumbering"] = True

        # XML: /wpProQuiz/data/quiz/numberedAnswer
        # JSON: sfwd-quiz_numberedAnswer
        # Display answer numbering
        # Quiz > Settings > Display and Content Options > Additional Question Options > Number Answers
        # false = hidden
        # true = shown
        ET.SubElement(quiz_elt, 'numberedAnswer').text = 'false'
        quiz_json["sfwd-quiz_numberedAnswer"] = False

        # XML: /wpProQuiz/data/quiz/answerRandom
        # JSON: sfwd-quiz_answerRandom
        # Answer display will be randomized within any given question.
        # Quiz > Settings > Display and Content Options > Additional Question Options > Randomize Answers
        # false = respect ordering
        # true = randomize answer ordering
        ET.SubElement(quiz_elt, 'answerRandom').text = 'true' # default is false
        quiz_json["sfwd-quiz_answerRandom"] = True

        # XML: /wpProQuiz/data/quiz/btnRestartQuizHidden
        # JSON: sfwd-quiz_btnRestartQuizHidden
        # Hide Restart Quiz button
        # Quiz > Settings > Results Page Display > Restart Quiz button
        # true = hidden
        # false = shown
        ET.SubElement(quiz_elt, 'btnRestartQuizHidden').text = 'false' # default "true"
        quiz_json["sfwd-quiz_btnRestartQuizHidden"] = False

        # JSON: sfwd-quiz_custom_result_data_display
        # Enable custom results display options. Enable the items you wish to display on the Result Page
        # Quiz > Settings > Results Page Display > Custom Results Display
        # "" = disabled (default)
        # "on" = enabled
        quiz_json["sfwd-quiz_custom_result_data_display"] = "on" # default: ""

        # XML: /wpProQuiz/data/quiz/showAverageResult
        # JSON: sfwd-quiz_showAverageResult
        # Display the average score of all users who took the quiz
        # Quiz > Settings > Results Page Display > Custom Results Display > Average Score
        # "" or false = disabled (default)
        # "on" or true = enabled
        ET.SubElement(quiz_elt, 'showAverageResult').text = 'true'
        quiz_json["sfwd-quiz_showAverageResult"] = "on"

        # XML: /wpProQuiz/data/quiz/showCategoryScore
        # JSON: sfwd-quiz_showCategoryScore
        # Display the score achieved for each Question Category
        # Quiz > Settings > Results Page Display > Custom Results Display > Category Score
        # "" or false = disabled
        # "on" or true = enabled
        ET.SubElement(quiz_elt, 'showCategoryScore').text = 'true' # default false
        quiz_json["sfwd-quiz_showCategoryScore"] = "on"

        # XML: /wpProQuiz/data/quiz/hideResultPoints
        # JSON: sfwd-quiz_hideResultPoints
        # Hide result points (mainly applicable for quizzes with questions that have point values)
        # Quiz > Settings > Results Page Display > Custom Results Display > Overall Score
        # true = hidden
        # false = shown
        ET.SubElement(quiz_elt, 'hideResultPoints').text = 'true'
        quiz_json["sfwd-quiz_hideResultPoints"] = True

        # XML: /wpProQuiz/data/quiz/hideResultCorrectQuestion
        # JSON: sfwd-quiz_hideResultCorrectQuestion
        # Hide number of correct answers
        # Quiz > Settings > Results Page Display > Custom Results Display > No. of Correct Answers
        # true = hidden
        # false = shown
        ET.SubElement(quiz_elt, 'hideResultCorrectQuestion').text = 'false' # default = true
        quiz_json["sfwd-quiz_hideResultCorrectQuestion"] = False

        # XML: /wpProQuiz/data/quiz/hideResultQuizTime
        # JSON: sfwd-quiz_hideResultQuizTime
        # Hide time spent
        # Quiz > Settings > Results Page Display > Custom Results Display > Time Spent
        # true = hidden
        # false = shown
        ET.SubElement(quiz_elt, 'hideResultQuizTime').text = 'false' # default = true
        quiz_json["sfwd-quiz_hideResultQuizTime"] = False

        # JSON: sfwd-quiz_custom_answer_feedback
        # Enable custom answer feedback. Select which data users should be able to view when reviewing their submitted questions.
        # Quiz > Settings > Results Page Display > Custom Answer Feedback
        # "" = disabled
        # "on" = enabled
        quiz_json["sfwd-quiz_custom_answer_feedback"] = "on" # default ""

        # XML: /wpProQuiz/data/quiz/hideAnswerMessageBox
        # JSON: sfwd-quiz_hideAnswerMessageBox
        # Hide "Correct" and "Incorrect" messages.
        # Quiz > Settings > Results Page Display > Custom Answer Feedback > Correct / Incorrect Messages
        # true = hidden
        # false = shown
        if test_row["ShowStudyGuide"] == "TRUE":
            ET.SubElement(quiz_elt, 'hideAnswerMessageBox').text = 'false'
            quiz_json["sfwd-quiz_hideAnswerMessageBox"] = False
        else:
            ET.SubElement(quiz_elt, 'hideAnswerMessageBox').text = 'true'
            quiz_json["sfwd-quiz_hideAnswerMessageBox"] = True

        # XML: /wpProQuiz/data/quiz/disabledAnswerMark
        # JSON: sfwd-quiz_disabledAnswerMark
        # Hide correct/incorrect answer marks
        # Quiz > Settings > Results Page Display > Custom Answer Feedback > Correct / Incorrect Answer Marks
        # true = hidden
        # false = shown
        ET.SubElement(quiz_elt, 'disabledAnswerMark').text = 'true'
        quiz_json["wd-quiz_disabledAnswerMark"] = True

        # XML: /wpProQuiz/data/quiz/btnViewQuestionHidden
        # JSON: sfwd-quiz_btnViewQuestionHidden
        # Hide View Questions button
        # Quiz > Settings > Results Page Display > Custom Answer Feedback > View Questions Button
        # true = hidden
        # false = shown
        ET.SubElement(quiz_elt, 'btnViewQuestionHidden').text = 'false' # default = true
        quiz_json["sfwd-quiz_btnViewQuestionHidden"] = False

        # REVISIT. We might want to collect LikeRT and other experience feedback from users after they take a quiz. Maybe one question for experience, and another additional feedback field.
        # XML: /wpProQuiz/data/quiz/forms/@activated
        # JSON: sfwd-quiz_formActivated
        # Enable custom fields.
        # Enable this option to gather data from your users before or after the quiz. All data is stored in the Quiz Statistics.
        # Quiz > Settings > Administrative and Data Handling Settings > Custom Fields
        xml_forms = ET.SubElement(quiz_elt, 'forms')
        xml_forms.set('activated', 'false')
        quiz_json["sfwd-quiz_formActivated"] = False

        # REVISIT
        # XML: /wpProQuiz/data/quiz/forms/@position
        # JSON: sfwd-quiz_formShowPosition
        # Form display position
        # Quiz > Settings > Administrative and Data Handling Settings > Custom Fields > Display Position
        # "0" = On the quiz startpage
        # "1" = At the end of the quiz (before the quiz result)
        xml_forms.set('position', '0')
        quiz_json["sfwd-quiz_formShowPosition"] = "0"

        # JSON: sfwd-quiz_custom_fields_forms
        # Quiz custom fields placeholder (only "" allowed)
        # Quiz > Settings > Administrative and Data Handling Settings > Custom Fields
        # ""
        quiz_json["sfwd-quiz_custom_fields_forms"] = ""

        # REVISIT: If we're doing custom forms, extra fields would be added here from 'form!' and 'formData!'

        # XML: /wpProQuiz/data/quiz/toplist/@activated
        # JSON: sfwd-quiz_toplistActivated
        # Enable leaderboard
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard
        # false = disabled
        # true = enabled
        xml_toplist = ET.SubElement(quiz_elt, 'toplist')
        xml_toplist.set('activated', 'false')
        quiz_json["sfwd-quiz_toplistActivated"] = False

        # XML: /wpProQuiz/data/quiz/toplist/toplistDataAddPermissions
        # JSON: sfwd-quiz_toplistDataAddPermissions
        # Leaderboard allowed applicants
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard > Who can apply?
        # 1 = All user
        # 2 = Registered users only
        # 3 = Anonymous users only
        ET.SubElement(xml_toplist, 'toplistDataAddPermissions').text = '1'
        quiz_json["sfwd-quiz_toplistDataAddPermissions"] = 1

        # XML: /wpProQuiz/data/quiz/toplist/toplistDataAddMultiple
        # JSON: sfwd-quiz_toplistDataAddMultiple
        # Users can apply more than once to the leaderboard
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard > Multiple Applications per user
        # false = single leadeboard entry
        # true = multiple leaderboard applications
        ET.SubElement(xml_toplist, 'toplistDataAddMultiple').text = 'false'
        quiz_json["sfwd-quiz_toplistDataAddMultiple"] = False

        # XML: /wpProQuiz/data/quiz/toplist/toplistDataAddBlock
        # JSON: sfwd-quiz_toplistDataAddBlock
        # Leaderboard application timeout (minutes)
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard > Multiple Applications per user > Re-apply after minutes
        # 0 = no limit
        # 1+
        ET.SubElement(xml_toplist, 'toplistDataAddBlock').text = '0'
        quiz_json["sfwd-quiz_toplistDataAddBlock"] = 0

        # XML: /wpProQuiz/data/quiz/toplist/toplistDataAddAutomatic
        # JSON: sfwd-quiz_toplistDataAddAutomatic
        # Always apply to leaderboard
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard > Automatic user entry
        # false = disabled
        # true = enabled
        ET.SubElement(xml_toplist, 'toplistDataAddAutomatic').text = 'false'
        quiz_json["sfwd-quiz_toplistDataAddAutomatic"] = False

        # XML: /wpProQuiz/data/quiz/toplist/toplistDataShowLimit
        # JSON: sfwd-quiz_toplistDataShowLimit
        # Number of displayed leaderboard entries
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard > Number of displayed entries
        # 0 = no limit
        # 1+
        ET.SubElement(xml_toplist, 'toplistDataShowLimit').text = '0'
        quiz_json["sfwd-quiz_toplistDataShowLimit"] = 0

        # XML: /wpProQuiz/data/quiz/toplist/toplistDataSort
        # JSON: sfwd-quiz_toplistDataSort
        # Sort leaderboard by
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard > Sort list by?
        # "1" = Best user
        # "2" = Newest entry
        # "3" = Oldest entry
        ET.SubElement(xml_toplist, 'toplistDataSort').text = '1'
        quiz_json["sfwd-quiz_toplistDataSort"] = "1"

        # JSON: sfwd-quiz_toplistDataShowIn_enabled
        # Display leaderboard on quiz results page
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard > Display on Quiz results page
        # "" = hidden
        # "on" = shown
        quiz_json["sfwd-quiz_toplistDataShowIn_enabled"] = ""

        # XML: /wpProQuiz/data/quiz/toplist/toplistDataShowIn
        # JSON: sfwd-quiz_toplistDataShowIn
        # Quiz results page leaderboard position
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard > Display on Quiz results page
        # 0 = Display on Quiz results page
        # 1 = Display on quiz results page below the result text
        # 2 = Display on Quiz results page in a button
        ET.SubElement(xml_toplist, 'toplistDataShowIn').text = '0'
        quiz_json["sfwd-quiz_toplistDataShowIn"] = 0

        # XML: /wpProQuiz/data/quiz/toplist/toplistDataCaptcha
        # JSON: sfwd-quiz_toplistDataCaptcha
        # Really Simple CAPTCHA. This option requires additional plugin:
        # Really Simple CAPTCHA (http://wordpress.org/extend/plugins/really-simple-captcha/)
        # Quiz > Settings > Administrative and Data Handling Settings > Leaderboard > Really Simple CAPTCHA
        # false = disabled
        # true = enabled
        ET.SubElement(xml_toplist, 'toplistDataCaptcha').text = 'false'
        quiz_json["sfwd-quiz_toplistDataCaptcha"] = False

        # XML: /wpProQuiz/data/quiz/statistic/@activated
        # JSON: sfwd-quiz_statisticsOn
        # Activate quiz statistics
        # Quiz > Settings > Administrative and Data Handling Settings > Quiz Statistics
        # false = disabled
        # true = enabled
        xml_statistic = ET.SubElement(quiz_elt, 'statistic')
        xml_statistic.set('activated', 'true')
        quiz_json["sfwd-quiz_statisticsOn"] = True

        # JSON: sfwd-quiz_statisticsIpLock_enabled
        # Enable Statistics IP-Lock
        # Quiz > Settings > Administrative and Data Handling Settings > Quiz Statistics > Statistics IP-lock
        # "" = disabled
        # "on" = enabled
        quiz_json["sfwd-quiz_statisticsIpLock_enabled"] = "on"

        # XML: /wpProQuiz/data/quiz/statistic/@ipLock
        # JSON: sfwd-quiz_statisticsIpLock
        # IP-Lock timeout. Protect the statistics from spam. Results will only be saved every X minutes. Stored in seconds.
        # Recommended to be 1440 so that the same results aren't submitted to statistics multiple times (https://coursemethod.com/learndash-tutorial.html)
        # Quiz > Settings > Administrative and Data Handling Settings > Quiz Statistics > Statistics IP-lock > IP-lock time limit
        # 0 = disabled
        # 1+
        xml_statistic.set('ipLock', '1440')
        quiz_json["sfwd-quiz_statisticsIpLock"] = 1440

        # JSON: sfwd-quiz_email_enabled
        # Enable email notifications
        # Quiz > Settings > Administrative and Data Handling Settings > Email Notifications
        # "" = disabled
        # "on" = enabled
        quiz_json["sfwd-quiz_email_enabled"] = ""

        # JSON: sfwd-quiz_email_enabled_admin
        # Enable admin email notifications
        # Quiz > Settings > Administrative and Data Handling Settings > Email Notifications > Admin
        # "" = disabled
        # "on" = enabled
        quiz_json["sfwd-quiz_email_enabled_admin"] = ""

        # XML: /wpProQuiz/data/quiz/emailNotification
        # JSON: sfwd-quiz_emailNotification
        # The admin will receive an email notification when the following users have taken the quiz.
        # Quiz > Settings > Administrative and Data Handling Settings > Email Notifications > Admin > Email trigger
        # "0" = default
        # "1" = Registered users only
        # "2" = All users
        ET.SubElement(quiz_elt, 'emailNotification').text = '0'
        quiz_json["sfwd-quiz_emailNotification"] = "0"

        # XML: /wpProQuiz/data/quiz/userEmailNotification
        # JSON: sfwd-quiz_userEmailNotification
        # Enable user email notifications
        # Quiz > Settings > Administrative and Data Handling Settings > Email Notifications > User
        # false = disabled
        # true = enabled
        ET.SubElement(quiz_elt, 'userEmailNotification').text = 'false'
        quiz_json["sfwd-quiz_userEmailNotification"] = 0

        # JSON: sfwd-quiz_templates_enabled
        # Enable quiz templates. Probably shouldn't use.
        # Quiz > Settings > Administrative and Data Handling Settings > Quiz Templates
        # "" = disabled
        # "on" = enabled
        quiz_json["sfwd-quiz_templates_enabled"] = ""

        # JSON: sfwd-quiz_advanced_settings
        # Enable advanced settings
        # Quiz > Settings > Administrative and Data Handling Settings > Advanced Settings
        # "" = disabled
        # "on" = enabled
        quiz_json["sfwd-quiz_advanced_settings"] = "on"

        # REVISIT. This is the second cookie-enabled feature. We'll need a cookie notice.
        # JSON: sfwd-quiz_timeLimitCookie_enabled
        # Enable browser cookie answer protection. Save the user's answers into a browser cookie until the Quiz is submitted. Browser cookies have limited memory. This may not work with large quizzes.
        # Quiz > Settings > Administrative and Data Handling Settings > Advanced Settings > Browser Cookie Answer Protection
        # "" = disabled
        # "on" = enabled
        quiz_json["sfwd-quiz_timeLimitCookie_enabled"] = "on"

        # JSON: sfwd-quiz_associated_settings_enabled
        # Association settings. Leave disabled.
        # Quiz > Settings > Administrative and Data Handling Settings > Advanced Settings > Associated Settings
        # "" = disabled
        # "on" = enabled
        quiz_json["sfwd-quiz_associated_settings_enabled"] = ""

        # JSON: sfwd-quiz_course_short_description
        # Short description that will be displayed for this quiz in the Course Grid. Doesn't seem to be configurable from the quiz builder; was always "" in all tests.
        # Quiz > Settings > LearnDash Course Grid Settings > Short Description
        # Text
        quiz_json["sfwd-quiz_course_short_description"] = ""

        ################################################################################################################################
        ################################################################################################################################
        ################################################################################################################################

        # Create questions element
        questions_elt = ET.SubElement(quiz_elt, 'questions')

        # Collect questions for this test
        test_questions = questions_by_test.get(test_row['TestId'], [])

        for q_row in test_questions:
            if q_row["QuestionType"] in ("NULL",""):
                continue # skip this row

            # Add the question to the XML
            question_elt = ET.SubElement(questions_elt, 'question')

            # REVISIT
            # XML: /wpProQuiz/data/quiz/questions/question/title
            # Question title
            # Question > Question page > Question title
            # Text
            # Current format: [Question title] ([Course ID]-[Question ID])
            # Example: Motherboard Identification (1011-16613)
            ET.SubElement(question_elt, 'title').text = CDATA(f"{q_row['QuestionName']} ({q_row['TestId']}-{q_row['QuestionId']})")

            # XML: /wpProQuiz/data/quiz/questions/question/questionText
            # Question content
            # Question > Question page > Content
            # Text
            questiontext_elt = ET.SubElement(question_elt, 'questionText')
            questiontext_elt.text = CDATA(q_row['QuestionText'])

            # XML: /wpProQuiz/data/quiz/questions/question/category
            # You can assign classify category for a question. Categories are e.g. visible in statistics function."
            # You can manage categories in global settings.
            # Question > Question page > Question Category (optional)
            # ?
            ET.SubElement(question_elt, 'category').text = standardize_question_reference(q_row['QuestionReference'])

            # XML: /wpProQuiz/data/quiz/questions/question/points
            # Question points. These points will be rewarded, only if the user chooses the answer correctly.
            # Question > Question page > Points (required) > Points for this question (Standard is 1 point)
            # 1+
            ET.SubElement(question_elt, 'points').text = '1'

            # XML: /wpProQuiz/data/quiz/questions/question/answerPointsActivated
            # Different points for each answer. If you enable this option, you can enter different points for every answer.
            # Question > Question page > Points (required) > Different points for each answer
            # false = disabled
            # true = enabled
            ET.SubElement(question_elt, 'answerPointsActivated').text = 'false'

            # XML: /wpProQuiz/data/quiz/questions/question/showPointsInBox
            # Show reached points in the correct/incorrect message. Only available if Different points for each answer is enabled
            # Question > Question page > Points (required) > Show reached points in the correct and incorrect message?
            # false = disabled
            # true = enabled
            ET.SubElement(question_elt, 'showPointsInBox').text = 'false'

            # XML: /wpProQuiz/data/quiz/questions/question/answerPointsDiffModusActivated
            # If "Different points for each answer" is activated, you can activate a special mode.
            # This changes the calculation of the points.
            # Question > Question page > Single choice options (optional) > Different points - modus 2 activate
            # false = disabled
            # true = enabled
            ET.SubElement(question_elt, 'answerPointsDiffModusActivated').text = 'false'

            # XML: /wpProQuiz/data/quiz/questions/question/disableCorrect
            # Disables the distinction between correct and incorrect. If enabled, the total points for the question are the greatest points from all answers.
            # Question > Question page > Single choice options (optional) > Disable correct and incorrect
            # false = enable distinction
            # true = disable distinction
            ET.SubElement(question_elt, 'disableCorrect').text = 'false'

            # XML: /wpProQuiz/data/quiz/questions/question/correctSameText
            # Same text for correct and incorrect message
            # Question > Question page > Message with the correct answer (optional) > Same text for correct- and incorrect-message?
            # false = different messages
            # true = same messages
            ET.SubElement(question_elt, 'correctSameText').text = 'false'

            # XML: /wpProQuiz/data/quiz/questions/question/correctMsg
            # This text will be visible if answered correctly. It can be used as explanation for complex questions. The message ""Right"" or ""Wrong"" is always displayed automatically.
            # Question > Question page > Message with the correct answer (optional) > correctMsg
            # text
            if q_row['QuestionExplanation'] in ("","NULL"):
                ET.SubElement(question_elt, 'correctMsg').text = CDATA("")
            else:
                ET.SubElement(question_elt, 'correctMsg').text = CDATA(q_row['QuestionExplanation']) # Even if the Skillify data is HTML, LearnDash always encases it in CDATA in this case.
            
            # XML: /wpProQuiz/data/quiz/questions/question/incorrectMsg
            # This text will be visible if answered incorrectly. It can be used as explanation for complex questions. The message ""Right"" or ""Wrong"" is always displayed automatically.
            # Question > Question page > Message with the incorrect answer (optional) > incorrectMsg
            # text
            if q_row['IncorrectExplanation'] in ("","NULL"):
                ET.SubElement(question_elt, 'incorrectMsg').text = CDATA("")
            else:
                ET.SubElement(question_elt, 'incorrectMsg').text = CDATA(q_row['IncorrectExplanation']) # Even if the Skillify data is HTML, LearnDash always encases it in CDATA in this case.

            # XML: /wpProQuiz/data/quiz/questions/question/tipMsg
            # Here you can enter solution hint.
            # Question > Question page > Hint (optional) > tipMsg
            # text
            xml_tipMsg = ET.SubElement(question_elt, 'tipMsg')
            xml_tipMsg.text = CDATA("")

            # XML: /wpProQuiz/data/quiz/questions/question/tipMsg/@enabled
            # Activate hint for this question? 
            # Question > Question page > Hint (optional) > Activate hint for this question
            # true = enabled
            # false = disabled
            xml_tipMsg.set("enabled", "false")

            #############################################################################################################################################
            #############################################################################################################################################
            #############################################################################################################################################

            answers_elt = ET.SubElement(question_elt, 'answers')
            answer_list = answers_by_test_question.get((test_row['TestId'], q_row['QuestionId']), [])

            # XML: /wpProQuiz/data/quiz/questions/question/@answerType
            # Answer type
            # Question > Question page > Answer type
            # "single" = Single choice
            # "multiple" = Multiple choice
            # "free_answer" = "Free" choice
            # "sort_answer" = "Sorting" choice
            # "matrix_sort_answer" = "Matrix Sorting" choice
            # "cloze_answer" = Fill in the blank
            # "assessment_answer" = Assessment
            # "essay" = Essay / Open Answer
            
            # (Skillify QuestionType):
            # "Multiple Selection"
            # "Multiple Choice"
            # "True / False"
            # "Drag Match"
            # "Sort Answers"
            # "Drag to Pharagraph"
            # "Multiple Choice With Image"
            # "Short Answer"

            # Answer_params defaults:
            answer_params = {
                "points": "0",
                "correct": "false",
                "gradingProgression": None, # Use "is None" for conditionals
                "gradedType": None,
                "answerText_html": "false",
                "stortText": "",
                "stortText_html": "true",
            }

            match q_row["QuestionType"]:
                
                # Multiple response question
                case "Multiple Selection":
                    question_elt.set("answerType", "multiple")
                    # Uses all default answer_params, but "correct" will be chosen later on
                    answer_params.update({
                        "correct": None,
                    })
                    for answer in answer_list:
                        answer_params.update({
                            "answerText": answer["AnswerDescription"],
                            "correct": "true" if answer["AnswerType"] == "Correct" else "false"
                        })
                        writeAnswer(answers_elt, answer_params)

                # Multiple choice question
                case "Multiple Choice": 
                    question_elt.set("answerType", "single")
                    # Uses all default answer_params, but "correct" will be chosen later on
                    answer_params.update({
                        "correct": None,
                    })
                    for answer in answer_list:                        
                        answer_params.update({
                            "answerText": answer["AnswerDescription"],
                            "correct": "true" if answer["AnswerType"] == "Correct" else "false"
                        })
                        writeAnswer(answers_elt, answer_params)

                # True/false question
                case "True / False":
                    question_elt.set("answerType", "single") 
                    # Skillify answers table contains only one answer per T/F question with AnswerType=correct and AnswerDescription=1/0 (1=True, 0=False). Therefore, for "single" types, we'll need to detect if there is only one answer, create two answers ("True" and "False"), and set one the answers' "correct" value depending on AnswerDescription.
                    # Uses all default answer_params, but "correct" will be chosen later on
                    answer_params.update({
                        "correct": None,
                    })

                    quantum_answer = answer_list[0] if answer_list else None

                    # Write "true" answer
                    answer_params.update({
                        "answerText": "True",
                        "correct": "true" if quantum_answer["AnswerDescription"] == 1 else "false"
                    })
                    writeAnswer(answers_elt, answer_params)

                    # Write "false" answer
                    answer_params.update({
                        "answerText": "False",
                        "correct": "true" if quantum_answer["AnswerDescription"] == 0 else "false"
                    })
                    writeAnswer(answers_elt, answer_params)

                # Matrix sorting question
                case "Drag Match":
                    question_elt.set("answerType", "matrix_sort_answer")
                    # Skillify answers contain 2 answers per matrix row, both with the same AnswerOrder value. The first row is the left column ("Criterion"), and the second row is the right (stort) column.
                    # Uses all default answer_params

                    if len(answer_list) % 2 != 0:
                        raise ValueError("Expected pairs in matrix_sort_answer but found an odd number of items in answer_list")

                    for i in range(0, len(answer_list), 2):
                        answer_params.update({
                            "answerText": answer_list[i]["AnswerDescription"],
                            "stortText": answer_list[i+1]["AnswerDescription"]
                        })
                        writeAnswer(answers_elt, answer_params)

                # Sorting question
                case "Sort Answers":
                    question_elt.set("answerType", "sort_answer")
                    # Skillify answers use the AnswerOrder field to denote the correct order. They need to be added to XML in that order.
                    # Uses all default answer_params

                    answer_list.sort(key=lambda row: int(row["AnswerOrder"]))

                    for answer in answer_list:
                        answer_params.update({
                            "answerText": answer["AnswerDescription"]
                        })
                        writeAnswer(answers_elt, answer_params)

                # Drag to paragraph 
                case "Drag to Pharagraph":
                    # Only 32 questions in the sample, all related to HTML and Python, so case sensitivity shouldn't be an issue. Making them into fill-in-the-blanks
                    question_elt.set("answerType", "cloze_answer")
                    # Uses all default answer_params
                    
                    questiontext = "<p><strong>Drag and drop disabled. Select the empty box(es) and type your answer instead.</strong></p><p>Available entries: "
                    
                    for i, answer in enumerate(answer_list):                        
                        questiontext += f"<code>{answer['answerDescription']}</code>"
                        if i != len(answer_list) - 1:
                            questiontext += ", "

                    questiontext += "</p>"

                    questiontext_elt.text = CDATA(questiontext)

                    soup = BeautifulSoup(q_row['QuestionText'], "html.parser")
                    spans = soup.find_all("span", class_="ext-questions", attrs={"data-text": True})

                    for i, span in enumerate(spans):
                        correct_text = span["data-text"]
                        placeholder = f"{{{correct_text}}}" # Blank answers are noted as {correct answer}.
                        span.replace_with(placeholder) # Replace entire element with LearnDash placeholder
                    
                    answertext = str(soup)

                    answer_params.update({
                        "answerText" : answertext
                    })

                    writeAnswer(answers_elt, answer_params)

                # Multiple choice with image
                case "Multiple Choice With Image":
                    question_elt.set("answerType", "single") 
                    # This is a multiple-choice question with one answer and a scenario image
                    # Uses all default answer_params, but "correct" will be chosen later on
                    answer_params.update({
                        "correct": None,
                    })

                # Short answer (fill-in-the-blank)
                case "Short Answer":
                    question_elt.set("answerType", "cloze_answer")
                    # Uses all default answer_params


                # No free_answer, assessment_answer, or essay type questions in existing sample.

                    
            # process answer_params
            question_elt.set("answerType", "multiple")
            
            
            
            
            
            q_type = (q_row.get('QuestionType') or '').lower()

            # Example: map "Multiple Choice" -> 'single'
            if 'multiple choice' in q_type:
                question_elt.set('answerType', 'single')
            else:
                question_elt.set('answerType', 'single')  # or "free_answer", etc.

            ET.SubElement(question_elt, 'title').text = CDATA(q_row.get('QuestionName', ''))
            create_cdata_element(question_elt, 'title', q_row.get('QuestionName', ''))
            create_cdata_element(question_elt, 'questionText', q_row.get('QuestionText', ''))
            create_cdata_element(question_elt, 'correctMsg', q_row.get('QuestionExplanation', ''))
            create_cdata_element(question_elt, 'incorrectMsg', q_row.get('IncorrectExplanation', ''))

            # Answers in XML
            answers_elt = ET.SubElement(question_elt, 'answers')
            ans_list = answers_by_test_question.get((test_row['TestId'], q_row['QuestionId']), [])

            for ans in ans_list:
                ans_elt = ET.SubElement(answers_elt, 'answer')
                is_correct = ans['AnswerType'].lower() == 'correct'
                ans_elt.set('correct', 'true' if is_correct else 'false')

                ans_text_elt = ET.SubElement(ans_elt, 'answerText')
                ans_text_elt.text = CDATA(ans['AnswerDescription']) if ans['AnswerDescription'] else ''

        #
        # NOW: Add the <post_meta> block with <meta_key>, <meta_value>
        # in the same pass, embedding “quiz_json” as CDATA.
        #
        post_elt = ET.SubElement(quiz_elt, 'post')  # e.g., <post> if your reversed-engineered format uses it
        create_cdata_element(post_elt, 'post_title', test_row['TestName'])
        create_cdata_element(post_elt, 'post_content', '')  # example

        post_meta_elt = ET.SubElement(quiz_elt, 'post_meta')
        meta_key_elt = ET.SubElement(post_meta_elt, 'meta_key')
        meta_key_elt.text = CDATA('_sfwd-quiz')  # the standard key for LD quiz settings?

        meta_value_elt = ET.SubElement(post_meta_elt, 'meta_value')
        # Convert your Python dict to JSON
        json_str = json.dumps(quiz_json)
        # Then place it as CDATA
        meta_value_elt.text = CDATA(json_str)

        # Potentially add more <post_meta> as needed, each with meta_key / meta_value.
        # ...

        # Write out to disk
        tree = ET.ElementTree(root)
        xml_filename = f"test_{test_row['TestId']}.xml"
        tree.write(xml_filename, encoding='utf-8', xml_declaration=True, pretty_print=True)
        print(f"Wrote XML (with JSON in <meta_value>) to {xml_filename}")

if __name__ == '__main__':
    main()
