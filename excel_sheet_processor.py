import re
import pandas as pd


def extract_course_code(course_str):
    """
    Extracts the course code from a given course string.

    Parameters:
    course_str (str): The string containing course information.

    Returns:
    str or None: The extracted course code if found, else None.
    """
    # Extracting course code using regex.
    course_code_match = re.search(r"[A-Z]{2,4}\d{4}", course_str)
    return course_code_match.group(0) if course_code_match else None


def extract_bachelor_matches(course_str):
    """
    Extracts bachelor's department and section matches from a given course string.

    Parameters:
    course_str (str): The string containing course information.

    Returns:
    list: A list of tuples with department codes and sections.
    """
    # Regex pattern to capture bachelor's department and sections.
    pattern = re.compile(
        r"\b[A-Z]{2,4}\("  # 2 to 4 uppercase letters + opening parenthesis (e.g. CY().
        r"([A-Z]{2,4})\)\s*"  # 2 to 4 uppercase letters inside parentheses (e.g. CY).
        r"[-\s]*\(?([A-Z,]+)\)?"  # Hyphen or space + optional parentheses + uppercase letters or commas (e.g. CY-ABC,DEF).
    )
    return pattern.findall(course_str)


def extract_master_matches(course_str):
    """
    Extracts master's department and section matches from a given course string.

    Parameters:
    course_str (str): The string containing course information.

    Returns:
    list: A list of tuples with department codes and sections.
    """
    # Regex pattern to capture master's department and sections.
    pattern = re.compile(
        r"\b"  # Word boundary to ensure proper match.
        r"(M[A-Z]{2,4})"  # 'M' followed by 2 to 4 uppercase letters (e.g., MDS).
        r"(?:\([A-Z]{2,4}\))?"  # Optional parentheses with 2 to 4 uppercase letters (e.g., (DS)).
        r"-"  # Hyphen separating department and section.
        r"([A-Z0-9]+)"  # One or more uppercase letters or digits (e.g., 3A).
    )
    return pattern.findall(course_str)


def process_bachelor_matches(matches):
    """
    Processes bachelor's department-section pairs.

    Parameters:
    matches (list): A list of tuples with department codes and sections.

    Returns:
    list: A list of formatted department-section strings.
    """
    departments_sections = []
    for dept_code, sections_str in matches:
        if sections_str:
            # Splitting sections string by commas or spaces.
            sections = re.split(r"[,\s]+", sections_str)
            for sec in sections:
                # Exclude empty strings and 'R' for Repeaters.
                sec = sec.strip()
                if sec and "R" not in sec:
                    # Splitting concatenated sections like 'ABC' into ['A', 'B', 'C'].
                    for char in sec:
                        if char != "R" and char.isalpha():
                            departments_sections.append(f"{dept_code}-{char}")
    return departments_sections


def process_master_matches(matches):
    """
    Processes master's department-section pairs.

    Parameters:
    matches (list): A list of tuples with department codes and sections.

    Returns:
    list: A list of formatted department-section strings.
    """
    departments_sections = []
    for dept_code_raw, section_str in matches:
        # Removing parentheses and merge department codes, e.g., 'MS(DS)' to 'MDS'.
        dept_code = re.sub(r"\(|\)", "", dept_code_raw)
        if section_str:
            # Directly concatenate department code with section.
            departments_sections.append(f"{dept_code}-{section_str}")
        elif not section_str.strip():
            # Handling cases like MS(CY) where section is missing.
            departments_sections.append(f"{dept_code}-Default")
    return departments_sections


def extract_course_info(course_str):
    """
    Extracts course information including course code, departments, and sections.

    Parameters:
    course_str (str): The string containing course information.

    Returns:
    tuple: A tuple containing the course code and a list of department-section pairs.
    """
    # Cleaning course string to handle irregular formats and line breaks.
    course_str = course_str.replace("\n", " ")  # Remove line breaks
    course_str = re.sub(r"\s+", " ", course_str)  # Normalize spaces

    course_code = extract_course_code(course_str)
    bachelor_matches = extract_bachelor_matches(course_str)
    master_matches = extract_master_matches(course_str)

    # Processing matches.
    departments_sections = process_master_matches(
        master_matches
    ) + process_bachelor_matches(bachelor_matches)

    # Removing duplicates to ensure each department-section pair is unique.
    departments_sections = list(set(departments_sections))

    return course_code, departments_sections


def extract_day_time_course_info(df):
    """
    Extracts day, time slot, and course information from the DataFrame.

    Parameters:
    df (DataFrame): The DataFrame containing the exam schedule.

    Returns:
    list: A list of dictionaries containing extracted information (date, time slot, course code, section).
    """
    time_slots_row_index = 0
    time_slots = {}

    # Iterating through each column starting from column index 1.
    for col_index in range(1, df.shape[1]):
        # Extracting time slot from the first row.
        time_slot = df.iloc[time_slots_row_index, col_index]
        if pd.notna(time_slot):
            time_slots[col_index] = time_slot

    # Initializing variables to store extracted information.
    extracted_data = []
    current_date = None

    # Iterating through each row starting from row index 1.
    for index in range(time_slots_row_index + 1, len(df)):
        row = df.iloc[index]

        # Extracting date from the first column.
        if pd.notna(row[0]):
            current_date = row[0]

        # Iterating through each column starting from column index 1.
        for col_index in range(1, df.shape[1]):
            course_data = row[col_index]
            if isinstance(course_data, str):
                # Getting time slot corresponding to this column.
                time_slot = time_slots.get(col_index)
                if time_slot:
                    # Extracting course code, sections.
                    course_code, departments_sections = extract_course_info(course_data)
                    if course_code and departments_sections:
                        for section in departments_sections:
                            extracted_data.append(
                                {
                                    "Date": current_date,
                                    "Time Slot": time_slot,
                                    "Course Code": course_code,
                                    "Section": section,
                                }
                            )

    return extracted_data


def process_exam_schedule(file_path, sheet_name="Sheet1"):
    """
    Loads and processes the exam schedule Excel file.

    Parameters:
    file_path (str): The path to the Excel file.
    sheet_name (str): The sheet name containing the exam schedule.

    Returns:
    CSV: A CSV file containing the extracted exam schedule data.
    """
    # Loading and cleaning the DataFrame.
    df_cleaned = (
        pd.read_excel(file_path, sheet_name=sheet_name)
        .dropna(how="all")
        .iloc[2:]
        .reset_index(drop=True)
    )
    extracted_exam_data = extract_day_time_course_info(df_cleaned)

    # Convert extracted data into a DataFrame to save as CSV.
    exam_schedule_df = pd.DataFrame(extracted_exam_data)
    exam_schedule_df.to_csv("./data/scraped_sheet.csv", index=False)

    print("Exam schedule data has been extracted and saved as './data/scraped_sheet.csv'")


process_exam_schedule("./data/exam_schedule.xlsx", "FSC")
