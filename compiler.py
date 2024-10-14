import pandas as pd

# Reading the first CSV file.
df1 = pd.read_csv('scraped_sheet.csv')

# Reading the second CSV file.
df2 = pd.read_csv('scraped_pdf.csv')

# Merging the two dataframes on 'course_code' and 'section'.
merged_df = pd.merge(df1, df2, on=['Course Code', 'Section'])

# Saviing the merged dataframe to a new CSV file.
merged_df.to_csv('merged_file.csv', index=False)

print("CSV files have been successfully merged.")