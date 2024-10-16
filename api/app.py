import os
from flask import Flask, request, jsonify
from .pdf_processor import process_pdf_to_csv
from .excel_sheet_processor import process_exam_schedule
from .classroom_finder import find_empty_classrooms

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp/data"
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

    process_exam_schedule(excel_path)

    csv_output_path = "/tmp/data/scraped_sheet.csv"
    if not os.path.exists(csv_output_path):
        return jsonify({"error": "Failed to generate CSV file"}), 500

    # Deleting uploaded Excel file after processing
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

    csv_output_path = "/tmp/data/scraped_pdf.csv"
    process_pdf_to_csv(pdf_path, csv_output_path)

    # Deleting uploaded PDF file after processing
    os.remove(pdf_path)

    return jsonify(
        {"message": "PDF processed successfully!", "csv_file": csv_output_path}
    )


@app.route("/empty_classrooms", methods=["GET"])
def empty_classrooms():
    empty_classrooms_per_time = find_empty_classrooms()

    # Deleting temporary files after processing
    os.remove("/tmp/data/scraped_pdf.csv")
    os.remove("/tmp/data/scraped_sheet.csv")
    os.remove("/tmp/data/merged_file.csv")
    return jsonify(empty_classrooms_per_time)


@app.route("/")
def home():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)