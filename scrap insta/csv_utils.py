print("Pick a file to extract instagram links to: ")
# list out current CSV files in the directory
import os
files = os.listdir()
csv_files = []
for file in files:
    if file.endswith('.csv'):
        csv_files.append(file)
for index, file in enumerate(csv_files):
    print(f'[{index + 1}] {file}')
# based on that, chose the file from user input
file_index = int(input('Enter the file number: '))
file = csv_files[file_index - 1]

# function to remove duplicates and save into the same file using pandas
def remove_duplicates_and_save_to_csv(file):
    import pandas as pd
    df = pd.read_csv(file)
    df.drop_duplicates(subset=['Username'], inplace=True)
    df.to_csv(file, index=False)

remove_duplicates_and_save_to_csv(file)