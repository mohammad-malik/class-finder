import pandas as pd
import os


def find_empty_classrooms(cwd):
    # Reading the first CSV file.
    df1 = pd.read_csv('/tmp/data/scraped_sheet.csv')

    # Reading the second CSV file.
    df2 = pd.read_csv('/tmp/data/scraped_pdf.csv')

    # Merging the two dataframes on 'course_code' and 'section'.
    merged_df = pd.merge(df1, df2, on=['Course Code', 'Section'])

    # Reading classroom list txt file (each line is a classroom).
    classrooms_list = []
    classrooms_list_path = os.path.join(cwd, "/data/classrooms.txt")

    with open(classrooms_list_path, 'r') as f:
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

    # Getting the unique times from the 'Time' column.
    unique_times = merged_df['Time Slot'].unique()

    # Identifying empty classrooms for each time slot.
    for time in unique_times:
        occupied_classrooms = unique_classrooms_times[unique_classrooms_times['Time Slot'] == time]['Room'].tolist()
        empty_classrooms = [classroom for classroom in classrooms_list if classroom not in occupied_classrooms]
        empty_classrooms_per_time[time] = empty_classrooms

    # Converting to dictionary to sort the keys.
    empty_classrooms_per_time = dict(sorted(empty_classrooms_per_time.items()))

    return empty_classrooms_per_time