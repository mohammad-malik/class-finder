import os
import streamlit as st
from pdf_processor import process_pdf_to_csv
from excel_sheet_processor import process_exam_schedule
from classroom_finder import find_empty_classrooms

# Set up upload folder
UPLOAD_FOLDER = "/tmp/data"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

st.title("Examtime Empty Classroom Finder")

# Initialize session state
if 'files_uploaded' not in st.session_state:
    st.session_state.files_uploaded = False
if 'files_processed' not in st.session_state:
    st.session_state.files_processed = False

# Step 1: File Upload
st.header("Step 1: Upload Files")
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
    st.success("Files uploaded successfully!")

if st.session_state.files_uploaded:
    with st.spinner("Processing Excel file..."):
        excel_output_path = os.path.join(UPLOAD_FOLDER, "scraped_sheet.csv")
        process_exam_schedule(excel_path, excel_output_path)

    with st.spinner("Processing PDF file..."):
        csv_output_path = os.path.join(UPLOAD_FOLDER, "scraped_pdf.csv")
        try:
            process_pdf_to_csv(pdf_path, csv_output_path)
        except Exception as e:
            st.error(f"Failed to process PDF: {str(e)}")

    st.session_state.files_processed = True

    # Clean up uploaded files
    os.remove(excel_path)
    os.remove(pdf_path)

# Step 3: Find Empty Classrooms
if st.session_state.files_processed:
    print(os.getcwd())
    classrooms_txt_path = os.path.join(os.getcwd(), "data/classrooms.txt")
    empty_classrooms_per_time = find_empty_classrooms(
        os.path.join(UPLOAD_FOLDER, "scraped_sheet.csv"),
        os.path.join(UPLOAD_FOLDER, "scraped_pdf.csv"),
        classrooms_txt_path
    )
    
    # Separating the labs and classrooms into two different tables
    labs = empty_classrooms_per_time[empty_classrooms_per_time["Room"].str.contains("LAB")]
    classrooms = empty_classrooms_per_time[~empty_classrooms_per_time["Room"].str.contains("LAB")]
    
    st.success("Empty classrooms found successfully!")
    st.header("Empty Classrooms")
    st.table(classrooms)

    st.header("Empty Labs")
    st.table(labs)

    # Clean up temporary files
    os.remove(os.path.join(UPLOAD_FOLDER, "scraped_pdf.csv"))
    os.remove(os.path.join(UPLOAD_FOLDER, "scraped_sheet.csv"))

