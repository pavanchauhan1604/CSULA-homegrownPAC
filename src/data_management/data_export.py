import sqlite3
import sys
import os
from collections import namedtuple
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import range_boundaries
from openpyxl.worksheet.table import Table, TableStyleInfo
import csv

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.data_management.data_import import get_site_id_from_domain_name
from src.core.filters import check_for_node, is_high_priority
from openpyxl.worksheet.datavalidation import DataValidation

def get_all_sites():


    with open("sql/get_all_sites.sql", 'r') as file:
        sql_query = file.read()
        conn = sqlite3.connect("drupal_pdfs.db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        results = [result[0] for result in results]

        if not results:
            return []
        return results



def get_pdf_reports_by_site_name(site_name):

    with open("sql/get_pdf_reports_by_site_name.sql", 'r') as file:
        sql_query = file.read()
        formatted_query = sql_query.format(site_name=site_name)

        conn = sqlite3.connect("drupal_pdfs.db")
        cursor = conn.cursor()

        # Execute the SQL query
        cursor.execute(formatted_query)
        results = cursor.fetchall()

        # If there are no results, return an empty list
        if not results:
            return []

        # Get column names from the cursor
        col_names = [desc[0] for desc in cursor.description]
        # Create a namedtuple class with column names
        Row = namedtuple('Row', col_names)

        # Convert sqlite3.Row objects to namedtuples
        results = [Row(*row) for row in results]

        # Close the database connection
        conn.close()

        return results


def get_pdfs_by_site_name(site_name):

    with open("sql/get_pdfs_by_domain_name.sql", 'r') as file:
        sql_query = file.read()
        formatted_query = sql_query.format(site_name=site_name)
        conn = sqlite3.connect("drupal_pdfs.db")
        cursor = conn.cursor()
        cursor.execute(formatted_query)
        results = cursor.fetchall()
        return results


#
# print(get_pdfs_by_site_name('creativewriting.sfsu.edu'))



def get_all_users_with_pdfs():
    with open("sql/get_all_users_with_pdf_files.sql", 'r') as file:
        sql_query = file.read()
        conn = sqlite3.connect("drupal_pdfs.db")
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        results = [result for result in results]

        if not results:
            return []
        return results


def get_site_failures(site_name):

    with open("sql/get_failures_by_site_id.sql", 'r') as file:
        sql_query = file.read()

        # need to get site id from site name

        site_id = get_site_id_from_domain_name(site_name.replace("-", "."))
        formatted_query = sql_query.format(site_id=site_id)
        conn = sqlite3.connect("drupal_pdfs.db")
        cursor = conn.cursor()

        cursor.execute(formatted_query)
        results = cursor.fetchall()

        # If there are no results, return an empty list
        if not results:
            return []


        # Get column names from the cursor
        col_names = [desc[0] for desc in cursor.description]
        # Create a namedtuple class with column names
        Row = namedtuple('Row', col_names)

        # Convert sqlite3.Row objects to namedtuples
        results = [Row(*row) for row in results]

        # Close the database connection
        conn.close()

        return results



def write_data_to_excel(data, failure_data, file_name="output.xlsx"):
    # Create a workbook
    wb = Workbook()

    # Create "Scanned PDFs" worksheet and set it as the active worksheet
    scanned_pdfs_ws = wb.create_sheet("Scanned PDFs", 0)
    wb.active = 0

    # Create "Failure" worksheet
    failure_ws = wb.create_sheet("Failure", 1)

    def add_data_to_scanned_pdfs(data, worksheet):
        if not data:
            print("No data to write to Excel.")
            return

        # 1) Build the columns list from the namedtuple fields
        columns = list(data[0]._fields)
        # Rename 'file_hash' to 'fingerprint'
        columns = ["fingerprint" if col == "file_hash" else col for col in columns]
        # Remove the 'box_folder' column
        columns.remove('box_folder')

        # Add custom columns to the end
        columns.append("Errors/Page")
        columns.append("Low Priority")
        columns.append("DPRC Will Remediate")

        # 2) Write the column headers to the worksheet
        worksheet.append(columns)

        # 3) Define the fill color for high priority rows
        red_fill = PatternFill(start_color='FF9999', end_color='FF9999', fill_type='solid')

        # 4) Create data validations for "Low Priority" and "DPRC Will Remediate" columns
        dv_low_priority = DataValidation(type="list", formula1='"Yes,No"', allow_blank=False)
        dv_dprc_remediate = DataValidation(type="list", formula1='"Yes,No"', allow_blank=False)

        # Add both data validations to the worksheet
        worksheet.add_data_validation(dv_low_priority)
        worksheet.add_data_validation(dv_dprc_remediate)

        # Loop through data rows and populate cells
        for item in data:
            item_list = list(item)

            high_priority = is_high_priority(item)  # (Your function to check if row is high priority)

            # Skip if the second item is a node link
            if not check_for_node(item_list[1]):    # (Your function to check if node link)
                # Convert first two columns to hyperlinks
                item_list[0] = f'=HYPERLINK("{item[0]}", "{item[0]}")'
                item_list[1] = f'=HYPERLINK("{item[1]}", "{item[1].split(" ")[0]}")' # remove accidental datatime info aadded

                # Truncate the 4th item (index 3) to 6 characters
                item_list[3] = item[3][0:6]

                # Convert these columns to "Yes"/"No"
                item_list[8] = "Yes" if item_list[8] == 1 else "No"
                item_list[10] = "Yes" if item_list[10] == 1 else "No"
                item_list[11] = "Yes" if item_list[11] == 1 else "No"
                item_list[13] = "Yes" if item_list[13] == 1 else "No"

                # Remove the box.com link at index 14
                del item_list[14]

                # Calculate Errors/Page
                errors_per_page = 0
                if item[7] != 0 and item[12] != 0:
                    errors_per_page = round(int(item[7]) / int(item[12]))
                item_list.append(errors_per_page)

                # Append placeholders for Low Priority & DPRC columns
                item_list.append("")
                item_list.append("")

                # Append the row to the worksheet
                worksheet.append(item_list)
                current_row = worksheet._current_row

                # Identify columns for data validation
                low_priority_col_idx = len(columns) - 1
                dprc_remediate_col_idx = len(columns)

                # Set Low Priority based on high_priority flag
                # Low Priority = Yes means NOT high priority (safe to defer)
                # Low Priority = No means IS high priority (needs immediate attention)
                low_priority_cell = worksheet.cell(row=current_row, column=low_priority_col_idx)
                dprc_remediate_cell = worksheet.cell(row=current_row, column=dprc_remediate_col_idx)
                low_priority_cell.value = "No" if high_priority else "Yes"
                dprc_remediate_cell.value = "No"

                dv_low_priority.add(low_priority_cell)
                dv_dprc_remediate.add(dprc_remediate_cell)

                # If high_priority is True, apply red_fill to the entire row
                if high_priority:
                    for cell in worksheet[current_row]:
                        cell.fill = red_fill

        # Make columns A and B appear as hyperlinks (blue + underline)
        max_row = worksheet.max_row
        for row in worksheet.iter_rows(min_row=2, min_col=1, max_col=2, max_row=max_row):
            for cell in row:
                cell.font = Font(color='0563C1', underline='single')

        # Convert the data into a formatted Table
        table_range = f"A1:{chr(64 + len(columns))}{max_row}"
        data_table = Table(displayName="DataTable", ref=table_range)
        style = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=True
        )
        data_table.tableStyleInfo = style
        worksheet.add_table(data_table)

    def add_data_to_failure(failure_data, worksheet):
        if not failure_data:
            print("No failure data to write to Excel.")
            return

        # Collect columns from the first item
        columns = list(failure_data[0]._fields)
        worksheet.append(columns)

        for item in failure_data:
            worksheet.append(list(item))

        # Create a table in the Failure sheet
        table_range = f"A1:{chr(64 + len(columns))}{len(failure_data) + 1}"
        failure_table = Table(displayName="FailureDataTable", ref=table_range)
        style = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=True
        )
        failure_table.tableStyleInfo = style
        worksheet.add_table(failure_table)

    # ---------------- MAIN LOGIC ----------------

    # 1) Populate the "Scanned PDFs" sheet
    add_data_to_scanned_pdfs(data, scanned_pdfs_ws)

    # 2) Create the "Failure" sheet
    add_data_to_failure(failure_data, failure_ws)

    # 3) Merging a block for instructional text in "Scanned PDFs"
    #    after we've created/filled "DataTable" in that sheet

    #   A) Locate the table named "DataTable"
    if "DataTable" in scanned_pdfs_ws.tables:
        table_obj = scanned_pdfs_ws.tables["DataTable"]
        table_range = table_obj.ref  # e.g. "A1:F20"

        #   B) Determine last data row from table ref
        min_col, min_row, max_col, max_row = range_boundaries(table_range)
        last_data_row = max_row

        #   C) Start 2 rows below the table
        start_merge_row = last_data_row + 2

        #   D) We want to merge 10 columns wide & 10 rows tall, for example
        rows_merged = 10
        cols_merged = 10

        #   E) Let's assume we want to start merging at column 1 (A),
        #      or you can shift columns if needed
        start_col = 1

        end_merge_row = start_merge_row + rows_merged - 1
        end_merge_col = start_col + cols_merged - 1

        #   F) Merge the cells
        scanned_pdfs_ws.merge_cells(
            start_row=start_merge_row,
            start_column=start_col,
            end_row=end_merge_row,
            end_column=end_merge_col
        )

        #   G) Put some instructional text in the top-left of the merged area
        cell = scanned_pdfs_ws.cell(row=start_merge_row, column=start_col)
        cell.value = (
            "Important Instructions:\n\n"
            "1) Please review PDF accessibility requirements at: https://www.calstatela.edu/accessibility\n"
            "2) Cal State LA will provide access to PDF remediation tools for all employees.\n"
            "3) Please update the Priority column if a PDF meets the requirements for low priority. Only focus on RED highlights.\n"
            "4) Pay Attention to the 'fingerprint' column. This is the unique identifier for each PDF. There may be duplicates on your domain.\n"
            "5) If you need assistance with PDF remediation, please contact:\n"
            "   Email: accessibility@calstatela.edu | Phone: 323-343-6170 (ITS Help Desk)\n"
            "6) These scans only look at files hosted on drupal or box, if you feel files are missing please let us know and we can run a new scan.\n"
            "7) For questions, training, or feedback, contact: accessibility@calstatela.edu\n"
        )
        #   H) Optional styling: wrap, center, bold, color, etc.
        cell.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
        cell.font = Font(bold=True, color="FF0000")

    else:
        print("DataTable not found in Scanned PDFs sheet. Skipping merged instructions block.")

    # 4) Save the workbook
    wb.save(file_name)
    print(f"Data written to {file_name} with a table format and merged instructions.")



