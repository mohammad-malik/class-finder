import re
import PyPDF2
import csv


def extract_text_from_pdf(pdf_path):
    """
    Extracts and cleans the text from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The cleaned text extracted from the PDF.
    """
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    cleaned_text = re.sub(r"\s+", " ", text)  # Clean line breaks and multiple spaces
    return cleaned_text


def normalize_section(section_str):
    """
    Normalizes the section string by removing certain prefixes and numerical parts based on rules.

    Args:
        section_str (str): The original section string.

    Returns:
        str: The normalized section string.
    """
    # Ignore if leading 'M' present (Master's students)
    if section_str.startswith("M"):
        return section_str
    # Remove leading 'B' if present
    if section_str.startswith("B"):
        section_str = section_str[1:]

    # Removing semester number from sections (DS-5D -> DS-D)
    section_str = re.sub(r"(\d+)([A-Z])", r"\2", section_str)

    return section_str


def extract_rooms_courses_from_text(text):
    """
    Extracts a mapping of room numbers to the list of unique courses allocated to them from a cleaned text.

    Args:
        text (str): The cleaned text from a PDF file.

    Returns:
        dict: A dictionary with room numbers as keys and lists of unique course names as values.
    """
    room_course_pattern = re.compile(
        rf"([A-Z]{{2}}\d{{4}})"                  # Course code: Two uppercase letters followed by four digits (e.g., "CS1234").
        rf"\s*-\s*"                              # Optional spaces, hyphen, and optional spaces to separate the course code and course name.
        rf"([\w\s]+)"                             # Course name: One or more alphanumeric characters and/or spaces (e.g., "Introduction to CS").
        rf"\s+"                                   # One or more spaces separating the course name from the section.
        rf"([A-Z]{{3}}-\d+[A-Z]?)"                # Section: Three uppercase letters followed by a hyphen, digits, and an optional uppercase letter (e.g., "MDS-3A").
        rf"\s+"                                   # One or more spaces separating the section from the room.
        rf"(?:Room\sNo\.\s*([\w\d\-]+)"           # Capture group 4: Room number after "Room No." (e.g., "B-230").
        rf"|([A-Za-z]+\sLab-[IVX]+))"             # Capture group 5: Lab name (e.g., "Rawal Lab-III").
        rf"(?:\s+\d+(?:st|nd|rd|th)\s+Floor)",    # Non-capturing group for floor information (e.g., "5th Floor").
        re.IGNORECASE,
    )

    room_course_dict = {}
    matches = room_course_pattern.findall(text)
    for match in matches:
        course_code, course_name, section, room_no, lab_name = match

        # Determine the room name based on which group matched
        if room_no:
            room = room_no
        elif lab_name:
            room = lab_name
        else:
            continue  # Skip if no room information is found

        # Normalize the section
        normalized_section = normalize_section(section)

        # Initialize the list for the room if not already present
        if room not in room_course_dict:
            room_course_dict[room] = []

        # Check for uniqueness before adding
        if [course_code, normalized_section] not in room_course_dict[room]:
            room_course_dict[room].append([course_code, normalized_section])

    return room_course_dict


def write_to_csv(data, csv_path):
    """
    Writes the room-course-section data to a CSV file.

    Args:
        data (dict): The dictionary containing room-course-section data.
        csv_path (str): The path to the CSV file.
    """
    with open(csv_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Room", "Course Code", "Section"])
        for room, courses in data.items():
            for course in courses:
                writer.writerow([room, course[0], course[1]])


def process_pdf_to_csv(pdf_path, csv_path):
    cleaned_text = extract_text_from_pdf(pdf_path)
    rooms_courses = extract_rooms_courses_from_text(cleaned_text)
    write_to_csv(rooms_courses, csv_path)
    print(f"Data has been written to {csv_path}")

if __name__ == "__main__":
    pdf_path = "./data/seating_plan.pdf"
    csv_path = "./data/scraped_pdf.csv"
    process_pdf_to_csv(pdf_path, csv_path)
