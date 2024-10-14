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
        rf"([A-Z]{{2}}\d{{4}})"  # Course code: Two uppercase letters followed by four digits (e.g., "CS1234").
        rf"\s*-\s*"  # Optional spaces, hyphen, and optional spaces to separate the course code and course name.
        rf"([\w\s]+)"  # Course name: One or more alphanumeric characters and/or spaces (e.g., "Introduction to CS").
        rf"\s+"  # One or more spaces separating the course name from the section.
        rf"([A-Z]{{3}}-\d+[A-Z]?)"  # Section: Three uppercase letters followed by a hyphen, digits, and an optional uppercase letter (e.g., "MDS-3A").
        rf"\s+Room\sNo\.\s*"  # Literal text "Room No." with optional spaces around it.
        rf"([\w\d\-]+)",  # Room number: One or more alphanumeric characters or hyphens (e.g., "A123" or "B-101").
        re.IGNORECASE,
    )

    room_course_dict = {}
    matches = room_course_pattern.findall(text)
    for match in matches:
        course_code, _, section, room_number = match
        if room_number not in room_course_dict:
            room_course_dict[room_number] = []
        if [course_code, section] not in room_course_dict[room_number]:
            room_course_dict[room_number].append(
                [course_code, normalize_section(section)]
            )

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


if __name__ == "__main__":
    pdf_path = "seating_plan.pdf"
    csv_path = "scraped_pdf.csv"

    cleaned_text = extract_text_from_pdf(pdf_path)
    rooms_courses = extract_rooms_courses_from_text(cleaned_text)
    write_to_csv(rooms_courses, csv_path)
    print(f"Data has been written to {csv_path}")
