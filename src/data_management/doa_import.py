import pandas as pd


df = pd.read_excel("doa.xlsx")

matching_rows = df.loc[df['Department Name'] == 'Psychology']


print(matching_rows[['Name', 'Student ID', 'Department Name']])