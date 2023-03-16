from pathlib import Path

import pandas as pd
import  xlwings as xw

# Get the dates to compare
date1 = "2023-01-27"
date2 = "2023-02-03"

# Create the filenames
date1_filename = "TTIPAB register " + date1 + ".csv"
date2_filename = "TTIPAB register " + date2 + ".csv"

# Create the filepaths
date1_path = Path.cwd() / date1_filename

date2_path = Path.cwd() / date2_filename

#Read the CSV data into dataframes
df_date1 = pd.read_csv(date1_path)

df_date2 = pd.read_csv(date2_path)

#
#diff = df_date2.compare(df_date1, align_axis=1)

# Reset the index
df_date2 = df_date2.reset_index()

# Merge the dataframes so that differences can be compared
df_diff = pd.merge(df_date1, df_date2, how="outer", indicator="Exist")

# Query which rows are different
df_diff = df_diff.query("Exist != 'both'")

#print(df_diff)

# Separate rows that have changed into a pair of dataframes
df_left = df_diff.query("Exist == 'left_only'")
df_right = df_diff.query("Exist == 'right_only'")

df_left = df_left.sort_values(by = 'Name')
df_right = df_right.sort_values(by = 'Name')

# Find which names are new
df_names = pd.merge(df_left, df_right, on='Name', how="outer", indicator="NameExist")

df_newAttorneys = df_names.query("NameExist == 'right_only'")
df_lapsedAttorneys = df_names.query("NameExist == 'left_only'")
df_changedAttorneys = df_names.query("NameExist == 'both'")

print(df_changedAttorneys)

print('The followng attorneys are newly registered:')
print(df_newAttorneys[['Name', 'Firm_y']])
print('The followng attorneys have updated details:')
print(df_changedAttorneys[['Name', 'Firm_x', 'Firm_y']])