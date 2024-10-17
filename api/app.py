import os
from flask import Flask, request, jsonify
from .pdf_processor import process_pdf_to_csv
from .excel_sheet_processor import process_exam_schedule
from .classroom_finder import find_empty_classrooms

app = Flask(__name__)

# Define current working directory.
cwd = os.getcwd()

# Define paths using environment variables with defaults.
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "/tmp/data")
classrooms_list_path = os.getenv(
    "CLASSROOMS_FILE_PATH", os.path.join(cwd, "data/classrooms.txt")
)
pdftotext_path = os.getenv("PDFTOTEXT_BIN_PATH", os.path.join(cwd, "bin/pdftotext"))

# Ensuring upload folder exists.
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/upload_excel", methods=["POST"])
def upload_excel():
    if "excel" not in request.files:
        return jsonify({"error": "No Excel file uploaded"}), 400

    excel_file = request.files["excel"]
    excel_path = os.path.join(app.config["UPLOAD_FOLDER"], excel_file.filename)
    excel_file.save(excel_path)

    csv_output_path = os.path.join(app.config["UPLOAD_FOLDER"], "scraped_sheet.csv")

    try:
        process_exam_schedule(excel_path, output_csv_path=csv_output_path)
    except Exception as e:
        # Cleaning up uploaded file in case of processing failure.
        os.remove(excel_path)
        return jsonify({"error": f"Failed to process Excel file: {str(e)}"}), 500

    if not os.path.exists(csv_output_path):
        # Cleaning up uploaded file if CSV generation failed.
        os.remove(excel_path)
        return jsonify({"error": "Failed to generate CSV file"}), 500

    # Deleting uploaded Excel file after processing.
    os.remove(excel_path)

    return jsonify(
        {
            "message": "Exam schedule processed successfully!",
            "csv_file": csv_output_path,
        }
    )


@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF file uploaded"}), 400

    pdf_file = request.files["pdf"]
    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], pdf_file.filename)
    pdf_file.save(pdf_path)

    csv_output_path = os.path.join(app.config["UPLOAD_FOLDER"], "scraped_pdf.csv")

    # Retrieving path to pdftotext from environment variables
    pdftotext_path = os.getenv(
        "PDFTOTEXT_BIN_PATH", os.path.join(os.getcwd(), "bin/pdftotext")
    )

    try:
        process_pdf_to_csv(
            file_path=pdf_path,
            csv_path=csv_output_path,
            pdftotext_path=pdftotext_path,
            upload_folder=app.config["UPLOAD_FOLDER"],
        )
    except Exception as e:
        # Cleaning up the uploaded PDF file in case of processing failure.
        os.remove(pdf_path)
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500

    # Deleting uploaded PDF file after processing.
    os.remove(pdf_path)

    return jsonify(
        {"message": "PDF processed successfully!", "csv_file": csv_output_path},
    )


@app.route("/empty_classrooms", methods=["GET"])
def empty_classrooms():
    # Retrieving paths from environment variables.
    scraped_sheet_csv_path = os.getenv('SCRAPED_SHEET_CSV_PATH', os.path.join(app.config["UPLOAD_FOLDER"], 'scraped_sheet.csv'))
    scraped_pdf_csv_path = os.getenv('SCRAPED_PDF_CSV_PATH', os.path.join(app.config["UPLOAD_FOLDER"], 'scraped_pdf.csv'))
    classrooms_list_path = os.getenv('CLASSROOMS_FILE_PATH', os.path.join(os.getcwd(), "data/classrooms.txt"))

    try:
        empty_classrooms_per_time = find_empty_classrooms(
            scraped_sheet_csv_path,
            scraped_pdf_csv_path,
            classrooms_list_path
        )
    except Exception as e:
        return jsonify({"error": f"Failed to find empty classrooms: {str(e)}"}), 500

    # Defining paths to temporary CSV files.
    pdf_csv = scraped_pdf_csv_path
    sheet_csv = scraped_sheet_csv_path

    # Cleaning up temporary files.
    for file_path in [pdf_csv, sheet_csv]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Failed to remove temporary file '{file_path}': {e}")

    return jsonify(empty_classrooms_per_time)


@app.route("/")
def home():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
