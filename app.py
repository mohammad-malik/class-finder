import os
import streamlit as st
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pdf_processor import process_pdf_to_csv
from excel_sheet_processor import process_exam_schedule
from classroom_finder import find_empty_classrooms

UPLOAD_FOLDER = "/tmp/data"
EXCEL_OUTPUT = "scraped_sheet.csv"
PDF_OUTPUT = "scraped_pdf.csv"
CLASSROOMS_TXT_PATH = os.path.join(os.getcwd(), "data/classrooms.txt")


def ensure_upload_folder():
    """
    Ensure upload folder exists.
    """
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)


def save_uploaded_file(uploaded_file, file_path):
    """
    Save the uploaded file to the specified path.

    Args:
        uploaded_file (BytesIO): The uploaded file.
        file_path (str): The path to save the uploaded file.
    """
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())


def process_files(excel_path, pdf_path):
    """
    Process the uploaded Excel and PDF files.

    Args:
        excel_path (str): The path to the uploaded Excel file.
        pdf_path (str): The path to the uploaded PDF file.

    Returns:
        tuple: A tuple containing the post-processed results for files.
    """    
    excel_output_path = os.path.join(UPLOAD_FOLDER, EXCEL_OUTPUT)
    pdf_output_path = os.path.join(UPLOAD_FOLDER, PDF_OUTPUT)

    def process_excel():
        process_exam_schedule(excel_path, excel_output_path)
        return "Excel file processed successfully!"

    def process_pdf():
        try:
            process_pdf_to_csv(pdf_path, pdf_output_path)
            return "PDF file processed successfully!"
        except Exception as e:
            return f"Failed to process PDF: {str(e)}"

    with st.spinner("Processing files..."):
        with ThreadPoolExecutor() as executor:
            future_excel = executor.submit(process_excel)
            future_pdf = executor.submit(process_pdf)
            excel_result = future_excel.result()
            pdf_result = future_pdf.result()

    return excel_result, pdf_result


def get_empty_classrooms():
    """
    Find empty classrooms and return cleaned results.

    Returns:
        tuple: A tuple containing two dictionaries (classrooms, others).
    """
    empty_classrooms_per_time = find_empty_classrooms(
        os.path.join(UPLOAD_FOLDER, EXCEL_OUTPUT),
        os.path.join(UPLOAD_FOLDER, PDF_OUTPUT),
        CLASSROOMS_TXT_PATH,
    )

    others = {
        time: [
            room.replace("Lab-", "").strip()
            for room in empty_classrooms
            if "Lab-" in room
            or room in 
                ["Auditorium", "CALL-1", "CALL-2", "CALL-3", "A-MEDC118"]
        ]
        for time, empty_classrooms in empty_classrooms_per_time.items()
    }

    classrooms = {
        time: [
            room.replace("Lab", "").strip()
            for room in empty_classrooms
            if "Lab" not in room
            and room not in 
                ["Auditorium", "CALL-1", "CALL-2", "CALL-3", "A-MEDC118"]
        ]
        for time, empty_classrooms in empty_classrooms_per_time.items()
    }

    return classrooms, others


def parse_time_slot(time_slot):
    """
    Parse the time slot string into a tuple of datetime objects for sorting.

    Args:
        time_slot (str): The time slot string in the format "hh:mm to hh:mm am/pm".

    Returns:
        tuple: The parsed start and end time as datetime objects.
    """
    # Split the start and end time
    start_time_str, end_time_str = time_slot.split(" to ")

    # Parse end_time
    end_time = datetime.strptime(end_time_str.strip(), "%I:%M %p")
    end_period = end_time_str[-2:].lower()  # "am" or "pm"
    end_hour = end_time.hour % 12 or 12  # Convert to 12-hour format

    # Extract start_hour
    start_hour = int(start_time_str.split(':')[0])

    # Determine start_period based on end_period and end_hour
    if end_period == "pm":
        if end_hour == 12:
            if start_hour == 12:
                start_period = "pm"
            else:
                start_period = "am"
        else:
            start_period = "pm"
    elif end_period == "am":
        if end_hour == 12:
            if start_hour == 12:
                start_period = "am"
            else:
                start_period = "pm"
        else:
            start_period = "am"

    # Append start_period to start_time_str if missing
    if "am" not in start_time_str.lower() and "pm" not in start_time_str.lower():
        start_time_str = start_time_str.strip() + f" {start_period}"

    # Parse start_time
    start_time = datetime.strptime(start_time_str.strip(), "%I:%M %p")

    return start_time, end_time


def dict_to_dataframe(data_dict, column_name):
    """
    Convert dictionary to DataFrame and sort by time slots.

    Args:
        data_dict (dict): The dictionary containing data.
        column_name (str): The column name for the DataFrame.

    Returns:
        DataFrame: The DataFrame containing the data.
    """
    # Sort the items based on parsed start and end times
    sorted_items = sorted(
        data_dict.items(),
        key=lambda x: parse_time_slot(x[0])
    )
    
    # Create the DataFrame
    df = pd.DataFrame(
        [
            {"Time Slot": time_slot, column_name: ", ".join(sorted(rooms))}
            for time_slot, rooms in sorted_items
        ]
    )
    
    # Set 'Time Slot' as the index
    df.set_index("Time Slot", inplace=True)
    
    return df


def display_classroom_data(classrooms, others):
    """
    Display the empty classrooms and others.

    Args:
        classrooms (dict): The dictionary containing empty classrooms.
        others (dict): The dictionary containing other rooms.
    """
    st.subheader("Empty Classrooms")
    st.dataframe(
        dict_to_dataframe(classrooms, "Empty Classrooms"),
        use_container_width=True,
    )

    st.subheader("Others (might be locked)")
    st.dataframe(
        dict_to_dataframe(others, "Others"),
        use_container_width=True
    )


# Main Streamlit application flow.
if __name__ == "__main__":
    st.title("Exam-time Empty Classroom Finder")

    ensure_upload_folder()

    # Initializing session state.
    if "files_uploaded" not in st.session_state:
        st.session_state.files_uploaded = False
    if "files_processed" not in st.session_state:
        st.session_state.files_processed = False

    # Step 1: File Upload.
    st.subheader("Upload Seating Plan of the day to check:")
    uploaded_pdf = st.file_uploader(
        "Upload PDF File", type=["pdf"])
    st.subheader("Upload Exam schedule:")
    uploaded_excel = st.file_uploader(
        "Upload Excel File", type=["xlsx"])

    if uploaded_excel and uploaded_pdf:
        excel_path = os.path.join(UPLOAD_FOLDER, uploaded_excel.name)
        pdf_path = os.path.join(UPLOAD_FOLDER, uploaded_pdf.name)

        save_uploaded_file(uploaded_excel, excel_path)
        save_uploaded_file(uploaded_pdf, pdf_path)

        st.session_state.files_uploaded = True

    # Step 2: Process Files.
    if st.session_state.files_uploaded and not st.session_state.files_processed:
        excel_result, pdf_result = process_files(excel_path, pdf_path)

        st.success(excel_result)
        if "Failed" in pdf_result:
            st.error(pdf_result)
        else:
            st.success(pdf_result)

        st.session_state.files_processed = True

        # Clean up uploaded files.
        os.remove(excel_path)
        os.remove(pdf_path)

    # Step 3: Find Empty Classrooms.
    if st.session_state.files_processed:
        classrooms, others = get_empty_classrooms()

        # Clean up temporary processed files.
        os.remove(os.path.join(UPLOAD_FOLDER, PDF_OUTPUT))
        os.remove(os.path.join(UPLOAD_FOLDER, EXCEL_OUTPUT))

        display_classroom_data(classrooms, others)