import pandas as pd

def find_empty_classrooms(sheet_csv_path, pdf_csv_path, classrooms_txt_path):
    """
    Finds empty classrooms based on the provided CSV files and classroom list.

    Args:
        sheet_csv_path (str): Path to the CSV file generated from the Excel sheet.
        pdf_csv_path (str): Path to the CSV file generated from the PDF.
        classrooms_txt_path (str): Path to the text file containing the list of classrooms.

    Returns:
        dict: A dictionary with time slots as keys and lists of empty classrooms as values.
    """
    # Reading the first CSV file.
    df1 = pd.read_csv(sheet_csv_path)

    # Reading the second CSV file.
    df2 = pd.read_csv(pdf_csv_path)

    # Merging the two dataframes on 'course_code' and 'section'.
    merged_df = pd.merge(df1, df2, on=['Course Code', 'Section'])

    # Reading classroom list txt file (each line is a classroom).
    classrooms_list = []
    with open(classrooms_txt_path, 'r') as f:
        for line in f:
            if "Locked:" in line:
                break
            classrooms_list.append(line.strip())

    # Removing the newline character from each classroom.
    classrooms_list = [classroom.strip() for classroom in classrooms_list if classroom != '']

    # Getting the unique combinations of classrooms and times from the 'Room' and 'Time' columns.
    unique_classrooms_times = merged_df[['Room', 'Time Slot']].drop_duplicates()

    # Creating a dictionary to store empty classrooms per time slot.
    empty_classrooms_per_time = {}

    # Getting the unique times from the 'Time Slot' column.
    unique_times = merged_df['Time Slot'].unique()

    # Identifying empty classrooms for each time slot.
    for time in unique_times:
        occupied_classrooms = unique_classrooms_times[unique_classrooms_times['Time Slot'] == time]['Room'].tolist()
        empty_classrooms = [classroom for classroom in classrooms_list if classroom not in occupied_classrooms]
        empty_classrooms_per_time[time] = empty_classrooms

    # Converting to dictionary to sort the keys.
    empty_classrooms_per_time = dict(sorted(empty_classrooms_per_time.items()))

    return empty_classrooms_per_time

if __name__ == "__main__":
    sheet_csv_path = "data/scraped_sheet.csv"
    pdf_csv_path = "data/scraped_pdf.csv"
    classrooms_txt_path = "data/classrooms.txt"

    empty_classrooms_per_time = find_empty_classrooms(sheet_csv_path, pdf_csv_path, classrooms_txt_path)
    
    # Separating labs and classrooms. (Keys is the time slot)
    labs = {time: [room for room in empty_classrooms if "Lab" in room] for time, empty_classrooms in empty_classrooms_per_time.items()}
    classrooms = {time: [room for room in empty_classrooms if "Lab" not in room] for time, empty_classrooms in empty_classrooms_per_time.items()}
    
    for time, empty_classrooms in empty_classrooms_per_time.items():
        print()
        print(f"Time Slot: {time}")
        print(f"Empty Classrooms: {classrooms[time]}")
        print(f"Empty Labs: {labs[time]}")
        print()