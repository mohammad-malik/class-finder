import os
import streamlit as st
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from pdf_processor import process_pdf_to_csv
from excel_sheet_processor import process_exam_schedule
from classroom_finder import find_empty_classrooms

# Set up upload folder.
UPLOAD_FOLDER = "/tmp/data"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

st.title("Examtime Empty Classroom Finder")

# Initialize session state.
if 'files_uploaded' not in st.session_state:
    st.session_state.files_uploaded = False
if 'files_processed' not in st.session_state:
    st.session_state.files_processed = False

# Step 1: File Upload.
uploaded_excel = st.file_uploader("Upload Excel File", type=["xlsx"])
uploaded_pdf = st.file_uploader("Upload PDF File", type=["pdf"])

if uploaded_excel and uploaded_pdf:
    excel_path = os.path.join(UPLOAD_FOLDER, uploaded_excel.name)
    pdf_path = os.path.join(UPLOAD_FOLDER, uploaded_pdf.name)

    with open(excel_path, "wb") as f:
        f.write(uploaded_excel.getbuffer())
    with open(pdf_path, "wb") as f:
        f.write(uploaded_pdf.getbuffer())

    st.session_state.files_uploaded = True

# Step 2: Process Files
if st.session_state.files_uploaded:
    excel_output_path = os.path.join(UPLOAD_FOLDER, "scraped_sheet.csv")
    csv_output_path = os.path.join(UPLOAD_FOLDER, "scraped_pdf.csv")

    def process_excel():
        process_exam_schedule(excel_path, excel_output_path)
        return "Excel file processed successfully!"

    def process_pdf():
        try:
            process_pdf_to_csv(pdf_path, csv_output_path)
            return "PDF file processed successfully!"
        except Exception as e:
            return f"Failed to process PDF: {str(e)}"

    with st.spinner("Processing files..."):
        with ThreadPoolExecutor() as executor:
            future_excel = executor.submit(process_excel)
            future_pdf = executor.submit(process_pdf)
            excel_result = future_excel.result()
            pdf_result = future_pdf.result()

        st.success(excel_result)
        if "Failed" in pdf_result:
            st.error(pdf_result)
        else:
            st.success(pdf_result)

    st.session_state.files_processed = True

    # Clean up uploaded files
    os.remove(excel_path)
    os.remove(pdf_path)

# Step 3: Find Empty Classrooms.
if st.session_state.files_processed:
    classrooms_txt_path = os.path.join(os.getcwd(), "data/classrooms.txt")
    empty_classrooms_per_time = find_empty_classrooms(
        os.path.join(UPLOAD_FOLDER, "scraped_sheet.csv"),
        os.path.join(UPLOAD_FOLDER, "scraped_pdf.csv"),
        classrooms_txt_path
    )

    # Cleaning up temporary files.
    os.remove(os.path.join(UPLOAD_FOLDER, "scraped_pdf.csv"))
    os.remove(os.path.join(UPLOAD_FOLDER, "scraped_sheet.csv"))

    labs = {time: [room.replace("Lab-", "").strip() for room in empty_classrooms if "Lab-" in room] for time, empty_classrooms in empty_classrooms_per_time.items()}
    classrooms = {time: [room for room in empty_classrooms if "Lab-" not in room] for time, empty_classrooms in empty_classrooms_per_time.items()}

    # Converting dictionaries to DataFrames for display.
    classrooms_df = pd.DataFrame([
        {"Time Slot": time_slot, "Empty Classrooms": ", ".join(sorted(rooms))}
        for time_slot, rooms in sorted(classrooms.items())
    ]).set_index("Time Slot")

    labs_df = pd.DataFrame([
        {"Time Slot": time_slot, "Empty Labs": ", ".join(sorted(rooms))}
        for time_slot, rooms in sorted(labs.items())
    ]).set_index("Time Slot")

    # Display the DataFrames as tables.
    st.subheader("Empty Classrooms")
    st.dataframe(classrooms_df, width=1500, use_container_width=True)

    st.subheader("Empty Labs")
    st.dataframe(labs_df, width=1500, use_container_width=True)