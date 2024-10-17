import pandas as pd
import os


def find_empty_classrooms(scraped_sheet_csv_path, scraped_pdf_csv_path, classrooms_list_path):
    """
    Identifies empty classrooms for each time slot based on the scraped exam schedules.

    Parameters:
    - scraped_sheet_csv_path (str): Path to the CSV file generated from the Excel upload.
    - scraped_pdf_csv_path (str): Path to the CSV file generated from the PDF upload.
    - classrooms_list_path (str): Path to the classrooms.txt file containing the list of classrooms.

    Returns:
    - dict: A dictionary where keys are time slots and values are lists of empty classrooms.
    """
    # Checking if scraped_sheet CSV exists.
    if not os.path.exists(scraped_sheet_csv_path):
        raise FileNotFoundError(f"Scraped sheet CSV file not found at '{scraped_sheet_csv_path}'")

    # Checking if scraped_pdf CSV exists.
    if not os.path.exists(scraped_pdf_csv_path):
        raise FileNotFoundError(f"Scraped PDF CSV file not found at '{scraped_pdf_csv_path}'")

    # Reading first CSV file (from Excel upload).
    try:
        df1 = pd.read_csv(scraped_sheet_csv_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read scraped sheet CSV '{scraped_sheet_csv_path}': {e}")

    # Reading second CSV file (from PDF upload).
    try:
        df2 = pd.read_csv(scraped_pdf_csv_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read scraped PDF CSV '{scraped_pdf_csv_path}': {e}")

    # Merging the two dataframes on 'Course Code' and 'Section'.
    try:
        merged_df = pd.merge(df1, df2, on=['Course Code', 'Section'])
    except KeyError as e:
        raise RuntimeError(f"Missing expected columns during merge: {e}")
    except Exception as e:
        raise RuntimeError(f"Error during merging CSV files: {e}")

    # Reading classroom list txt file (each line is a classroom).
    if not os.path.exists(classrooms_list_path):
        raise FileNotFoundError(f"Classrooms list file not found at '{classrooms_list_path}'")

    classrooms_list = []
    try:
        with open(classrooms_list_path, 'r') as f:
            for line in f:
                if "Locked:" in line:
                    break
                classroom = line.strip()
                if classroom:
                    classrooms_list.append(classroom)
    except Exception as e:
        raise RuntimeError(f"Failed to read classrooms list from '{classrooms_list_path}': {e}")

    # Getting the unique combinations of classrooms and times from the 'Room' and 'Time Slot' columns.
    if 'Room' not in merged_df.columns or 'Time Slot' not in merged_df.columns:
        raise RuntimeError("Merged CSV does not contain 'Room' or 'Time Slot' columns")

    unique_classrooms_times = merged_df[['Room', 'Time Slot']].drop_duplicates()

    # Creating a dictionary to store empty classrooms per time slot.
    empty_classrooms_per_time = {}

    # Getting the unique time slots from the 'Time Slot' column.
    unique_times = merged_df['Time Slot'].unique()

    # Identifying empty classrooms for each time slot.
    for time in unique_times:
        occupied_classrooms = unique_classrooms_times[unique_classrooms_times['Time Slot'] == time]['Room'].tolist()
        empty_classrooms = [classroom for classroom in classrooms_list if classroom not in occupied_classrooms]

        # Assign the list of empty classrooms to the current time slot.
        empty_classrooms_per_time[time] = empty_classrooms

    # Sorting the dictionary by time slots for consistency.
    empty_classrooms_per_time = dict(sorted(empty_classrooms_per_time.items()))

    return empty_classrooms_per_time


if __name__ == "__main__":
    # Defining paths using environment variables with defaults
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', "/tmp/data")
    scraped_sheet_csv_path = os.getenv('SCRAPED_SHEET_CSV_PATH', os.path.join(UPLOAD_FOLDER, 'scraped_sheet.csv'))
    scraped_pdf_csv_path = os.getenv('SCRAPED_PDF_CSV_PATH', os.path.join(UPLOAD_FOLDER, 'scraped_pdf.csv'))
    classrooms_list_path = os.getenv('CLASSROOMS_FILE_PATH', os.path.join(os.getcwd(), "data/classrooms.txt"))

    # Ensuring the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    try:
        empty_classrooms = find_empty_classrooms(scraped_sheet_csv_path, scraped_pdf_csv_path, classrooms_list_path)
        print("Empty Classrooms per Time Slot:")
        for time_slot, classrooms in empty_classrooms.items():
            print(f"{time_slot}: {', '.join(classrooms)}")
    except Exception as e:
        print(f"Error finding empty classrooms: {e}")
