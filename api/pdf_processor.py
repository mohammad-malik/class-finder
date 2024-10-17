import os
import re
import csv
import subprocess

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

def extract_text_with_pdftotext(file_path, pdftotext_path, temp_txt_path):
    """
    Extracts text from a PDF using the external pdftotext tool.

    Args:
        file_path (str): Path to the PDF file.
        pdftotext_path (str): Path to the pdftotext binary.
        temp_txt_path (str): Path to store the temporary extracted text.

    Returns:
        str: Cleaned extracted text.
    """
    # Execute pdftotext command
    try:
        subprocess.run([pdftotext_path, '-layout', file_path, temp_txt_path], check=True)
        with open(temp_txt_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error during pdftotext execution: {e}")
    except FileNotFoundError as e:
        raise RuntimeError(f"pdftotext binary not found at '{pdftotext_path}': {e}")
    finally:
        # Clean up temporary file
        if os.path.exists(temp_txt_path):
            os.remove(temp_txt_path)

    # Normalize whitespace
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
    try:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Room", "Course Code", "Section"])
            rows = [
                [room, course_code, section]
                for room, courses in data.items()
                for course_code, section in courses
            ]
            writer.writerows(rows)
    except Exception as e:
        raise RuntimeError(f"Failed to write CSV file '{csv_path}': {e}")

def process_pdf_to_csv(file_path, csv_path, pdftotext_path, upload_folder):
    """
    Processes a PDF file to extract room-course-section mappings and writes them to a CSV.

    Args:
        file_path (str): Path to the PDF file.
        csv_path (str): Path to save the processed CSV file.
        pdftotext_path (str): Path to the pdftotext binary.
        upload_folder (str): Directory for temporary file storage.

    Returns:
        None
    """
    file_path = os.path.abspath(file_path)
    csv_path = os.path.abspath(csv_path)
    temp_txt_path = os.path.join(upload_folder, "extracted_text.txt")

    # Extracting text from PDF
    text = extract_text_with_pdftotext(file_path, pdftotext_path, temp_txt_path)

    # Extracting room-course mappings
    rooms_courses = extract_rooms_courses_from_text(text)

    # Writing data to CSV
    write_to_csv(rooms_courses, csv_path)
    print(f"Data has been written to '{csv_path}'")

if __name__ == "__main__":
    # Defining paths using environment variables with defaults
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', "/tmp/data")
    pdftotext_path = os.getenv('PDFTOTEXT_BIN_PATH', os.path.join(os.getcwd(), 'bin/pdftotext'))
    pdf_file_path = os.getenv('PDF_FILE_PATH', os.path.join(UPLOAD_FOLDER, 'seating_plan.pdf'))
    scraped_pdf_csv_path = os.getenv('SCRAPED_PDF_CSV_PATH', os.path.join(UPLOAD_FOLDER, 'scraped_pdf.csv'))

    # Ensuring upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    try:
        process_pdf_to_csv(pdf_file_path, scraped_pdf_csv_path, pdftotext_path, UPLOAD_FOLDER)
    except Exception as e:
        print(f"Error processing PDF: {e}")
