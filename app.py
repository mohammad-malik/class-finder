from flask import Flask, request, jsonify
import os
from pdf_extractor import process_pdf_to_csv
from excel_sheet_processor import process_exam_schedule
from classroom_finder import find_empty_classrooms

app = Flask(__name__)

# Define a folder to save uploaded files
UPLOAD_FOLDER = './data'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'excel' not in request.files:
        return jsonify({"error": "No Excel file uploaded"}), 400
    
    excel_file = request.files['excel']
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_file.filename)
    excel_file.save(excel_path)
    
    # Process the Excel file to extract exam schedule
    process_exam_schedule(excel_path)
    
    # Assuming the process generates a CSV output
    csv_output_path = './data/scraped_sheet.csv'
    if not os.path.exists(csv_output_path):
        return jsonify({"error": "Failed to generate CSV file"}), 500
    
    return jsonify({"message": "Exam schedule processed successfully", "csv_file": csv_output_path})


@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({"error": "No PDF file uploaded"}), 400
    
    pdf_file = request.files['pdf']
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
    pdf_file.save(pdf_path)
    
    # Process the PDF file to extract data and write to CSV
    csv_output_path = './data/scraped_pdf.csv'
    process_pdf_to_csv(pdf_path, csv_output_path)
    
    return jsonify({"message": "PDF processed successfully", "csv_file": csv_output_path})


@app.route('/empty_classrooms', methods=['GET'])
def empty_classrooms():
    empty_classrooms_per_time = find_empty_classrooms()
    return jsonify(empty_classrooms_per_time)


@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)