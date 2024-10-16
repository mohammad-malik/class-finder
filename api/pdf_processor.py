import re
import csv
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

# Precompiled regex patterns (unchanged)
SEMESTER_SECTION_PATTERN = re.compile(r"(\d+)([A-Z])")
ROOM_COURSE_PATTERN = re.compile(
    rf"([A-Z]{{2}}\d{{4}})"  # Course code: e.g., "CS1234"
    rf"\s*-\s*"               # Separator: " - "
    rf"([\w\s]+)"             # Course name: e.g., "Introduction to CS"
    rf"\s+"                   # Space separator
    rf"([A-Z]{{3}}-\d+[A-Z]?)"  # Section: e.g., "MDS-3A"
    rf"\s+"                   # Space separator
    rf"(?:Room\sNo\.\s*([\w\d\-]+)"  # Room number: e.g., "B-230"
    rf"|([A-Za-z]+\sLab-[IVX]+))"   # Lab name: e.g., "Rawal Lab-III"
    rf"(?:\s+\d+(?:st|nd|rd|th)\s+Floor)",  # Floor info: e.g., "5th Floor"
    re.IGNORECASE,
)

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF using pdfminer.six directly with optimized LAParams.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Cleaned extracted text.
    """
    laparams = LAParams(line_overlap=0, char_margin=1.0, line_margin=0.5, word_margin=0.1, boxes_flow=0.0)
    text = extract_text(pdf_path, laparams=laparams)
    return ' '.join(text.split())

def normalize_section(section_str):
    """
    Normalizes the section string by removing certain prefixes and numerical parts.

    Args:
        section_str (str): Original section string.

    Returns:
        str: Normalized section string.
    """
    if section_str.startswith("M"):
        return section_str
    if section_str.startswith("B"):
        section_str = section_str[1:]
    return SEMESTER_SECTION_PATTERN.sub(r"\2", section_str)

def extract_rooms_courses_from_text(text):
    """
    Maps room numbers to unique courses allocated to them.

    Args:
        text (str): Cleaned extracted text.

    Returns:
        dict: Room numbers as keys and lists of unique courses as values.
    """
    room_course_dict = {}
    seen_courses = set()

    for match in ROOM_COURSE_PATTERN.finditer(text):
        course_code, _, section, room_no, lab_name = match.groups()
        room = room_no if room_no else lab_name
        if not room:
            continue

        normalized_section = normalize_section(section)
        course_key = (room, course_code, normalized_section)
        if course_key not in seen_courses:
            seen_courses.add(course_key)
            if room in room_course_dict:
                room_course_dict[room].append((course_code, normalized_section))
            else:
                room_course_dict[room] = [(course_code, normalized_section)]

    return room_course_dict

def write_to_csv(data, csv_path):
    """
    Writes the room-course-section data to a CSV file.

    Args:
        data (dict): Room-course-section data.
        csv_path (str): Path to the CSV file.
    """
    with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Room", "Course Code", "Section"])
        rows = [
            [room, course_code, section]
            for room, courses in data.items()
            for course_code, section in courses
        ]
        writer.writerows(rows)

def process_pdf_to_csv(pdf_path, csv_path):
    text = extract_text_from_pdf(pdf_path)
    rooms_courses = extract_rooms_courses_from_text(text)
    write_to_csv(rooms_courses, csv_path)
    print(f"Data has been written to {csv_path}")

if __name__ == "__main__":
    pdf_path = "./api/data/seating_plan.pdf"
    csv_path = "./api/data/scraped_pdf.csv"
    process_pdf_to_csv(pdf_path, csv_path)