import csv
import sqlite3


def add_employees_from_csv_file(file_path):
    # Define the connection and cursor
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()

    # Open the CSV file and iterate over its rows
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip the header row
        for row in csv_reader:
            # if row is blank or empty string, skip it
            if not row or row[1] == '':
                continue
            # Prepare last name (assuming the full name is in row[0] and employee_id is in row[1])
            full_name = row[0].split(" ")
            first_name = full_name[0]
            last_name = " ".join(full_name[1:]) if len(full_name) > 1 else ""
            # Insert each row into the database only if employee_id is unique
            cursor.execute("INSERT OR IGNORE INTO site_user (employee_id, first_name, last_name, email)"
                           " VALUES (?, ?, ?, ?)", (row[1], first_name, last_name, row[2]))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


def update_managers_boolean_in_site_user_table(csv_file_path):
    # load managers id numbers from csv file
    with open(csv_file_path, 'r') as file:
        csv_reader = csv.reader(file)
        managers = [row[0] for row in csv_reader]

    # Define the connection and cursor
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()

    for employee_id in managers:
        # Update the is_manager column in the site_user table
        # Use 1 to represent True for the is_manager BOOLEAN column in SQLite
        cursor.execute("UPDATE site_user SET is_manager = 1 WHERE employee_id = ?", (employee_id,))

    # Commit the changes to the database
    conn.commit()

    # Close the database connection
    conn.close()

    print("Managers updated successfully.")


def add_sites_from_site_csv_file(file_path):
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()
    # open csv file
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)

    # print each line in csv reader
        for row in csv_reader:

            for site in row[0].split(","):

                site = site.strip()
                # Strip URL scheme (https:// or http://) if present
                if '://' in site:
                    site = site.split('://', 1)[1]
                # Strip www. prefix
                site = site.replace('www.', '', 1)
                # Normalize path separator: use _ instead of / for DB storage
                domain_name = site.replace('/', '_').strip('_')
                security_group_name = row[1]
                cursor.execute("INSERT INTO drupal_site (domain_name, security_group_name) VALUES (?, ?)", (domain_name, security_group_name))
                conn.commit()
    cursor.close()



def add_employee_and_site_assignments_from_csv_file(file_path):
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()

    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)

        for row in csv_reader:
            sec_group = row[0]
            employee_name = row[1]
            employee_id = row[2]
            employee_email = row[3]

            full_name = employee_name.split(" ")
            first_name = full_name[0]
            last_name = " ".join(full_name[1:]) if len(full_name) > 1 else ""

            # check and insert employee into site_user table if they don't exist, if they do exist return the record
            cursor.execute("INSERT OR IGNORE INTO site_user (employee_id, first_name, last_name, email) VALUES (?, ?, ?, ?)", (employee_id, first_name, last_name, employee_email))

            # get employee record by employee id
            employee = cursor.execute("SELECT * FROM site_user WHERE employee_id = ?", (employee_id,)).fetchone()

            # get site record by security group name
            site = cursor.execute("SELECT * FROM drupal_site WHERE security_group_name = ?", (sec_group,)).fetchone()

            if site is None or employee is None:
                print("Site or employee not found in the database.")
                continue


            # insert employee and site assignment into site_assignment table
            cursor.execute("INSERT INTO site_assignment (site_id, user_id) VALUES (?, ?)", (site[0], employee[0]))

            conn.commit()
        conn.close()


def add_admin_contacts(file_path):
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()

    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        header = next(csv_reader)
        for row in csv_reader:

            print(row)
            site = row[0]
            print("EEEESSSS", site)
            employee_name = row[1]
            employee_email = row[2]
            if site is None or employee_name is None or employee_email is None:
                continue
            generated_id = f"{hash(employee_email) % 1000000000}"


            full_name = employee_name.split(" ")
            first_name = full_name[0]
            last_name = " ".join(full_name[1:]) if len(full_name) > 1 else ""

            print("DFSDF", full_name, first_name,last_name, generated_id, employee_email)

            # Check if email already exists in the site_user table
            email_exists = cursor.execute("SELECT * FROM site_user WHERE email = ?", (employee_email,)).fetchone()
            print("EEEE", site)
            site_id = cursor.execute("SELECT id FROM drupal_site WHERE domain_name = ?", (site,)).fetchone()

            # if site_id is None:
            #     cursor.execute("INSERT INTO drupal_site (domain_name) VALUES (?)", (site,))
            #     site_id = cursor.lastrowid


            if email_exists:
                cursor.execute("UPDATE site_user SET is_manager = 1 WHERE email = ?", (employee_email,))
                print("email_exists", site_id[0], email_exists[0])

                assignment_exists = cursor.execute("SELECT * FROM site_assignment WHERE site_id = ? AND user_id = ?", (site_id[0], email_exists[0]))
                if not assignment_exists:
                    cursor.execute("INSERT INTO site_assignment (site_id, user_id) VALUES (?, ?)", (site_id[0], email_exists[0]))

            if not email_exists:
                cursor.execute("INSERT INTO site_user (employee_id, first_name, last_name, email) VALUES (?, ?, ?, ?)", (generated_id, first_name, last_name, employee_email))
                employee = cursor.execute("SELECT * FROM site_user WHERE email = ?", (employee_email,)).fetchone()

                cursor.execute("INSERT INTO site_assignment (site_id, user_id) VALUES (?, ?)", (site_id[0], employee[0]))

            conn.commit()

        conn.close()




def check_if_pdf_file_exists(pdf_uri, parent_uri, drupal_site_id, pdf_hash):

    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()

    exists = cursor.execute("SELECT * FROM drupal_pdf_files WHERE pdf_uri = ? AND parent_uri = ? AND drupal_site_id = ? AND file_hash = ?",
                   (pdf_uri, parent_uri, drupal_site_id, pdf_hash)).fetchone()

    conn.close()

    return True if exists else False


def get_site_id_from_domain_name(domain_name):
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()
    site_id = cursor.execute("SELECT id FROM drupal_site WHERE domain_name = ?", (domain_name,)).fetchone()
    conn.close()
    return site_id[0] if site_id else None


import sqlite3

def add_pdf_file_to_database(pdf_uri, parent_uri, drupal_site_id, violation_dict, overwrite=False):
    # connect
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()

    # unpack violation_dict safely
    violations            = violation_dict.get("violations", 0)
    failed_checks         = violation_dict.get("failed_checks", 0)
    tagged                = violation_dict.get("tagged", True)
    check_for_image_only  = violation_dict.get("check_for_image_only", False)
    pdf_text_type         = violation_dict.get("pdf_text_type", "")
    metadata              = violation_dict.get("metadata", {}) or {}
    title_set             = metadata.get("title")
    language_set          = metadata.get("language")
    approved_pdf_exporter = metadata.get("approved_pdf_exporter", False)
    doc_data              = violation_dict.get("doc_data", {}) or {}
    page_count            = doc_data.get("pages", 0)
    file_hash             = violation_dict.get("file_hash", "")
    has_form              = violation_dict.get("has_form", False)

    # --- upsert pdf_report ---
    cursor.execute(
        "SELECT 1 FROM pdf_report WHERE pdf_hash = ?",
        (file_hash,)
    )
    report_exists = cursor.fetchone() is not None

    # if a report exists, update it, otherwise insert a new one
    if report_exists:
        if overwrite:
            cursor.execute("""
                           UPDATE pdf_report
                           SET violations             = ?,
                               failed_checks          = ?,
                               tagged                 = ?,
                               check_for_image_only   = ?,
                               pdf_text_type          = ?,
                               title_set              = ?,
                               language_set           = ?,
                               page_count             = ?,
                               has_form               = ?,
                               approved_pdf_exporter  = ?
                           WHERE pdf_hash = ?
                           """, (
                               violations,
                               failed_checks,
                               tagged,
                               check_for_image_only,
                               pdf_text_type,
                               title_set,
                               language_set,
                               page_count,
                               has_form,
                               approved_pdf_exporter,
                               file_hash
                           ))
            conn.commit()
        else:
            print("PDF report already exists in the database.")
    else:
        cursor.execute("""
                       INSERT INTO pdf_report (
                           violations,
                           failed_checks,
                           tagged,
                           check_for_image_only,
                           pdf_text_type,
                           title_set,
                           language_set,
                           page_count,
                           pdf_hash,
                           has_form,
                           approved_pdf_exporter
                       ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                       """, (
                           violations,
                           failed_checks,
                           tagged,
                           check_for_image_only,
                           pdf_text_type,
                           title_set,
                           language_set,
                           page_count,
                           file_hash,
                           has_form,
                           approved_pdf_exporter
                       ))
        conn.commit()

    # --- upsert drupal_pdf_files ---
    # Check for existing PDF by URI only (not hash) to prevent duplicates
    cursor.execute(
        "SELECT 1 FROM drupal_pdf_files WHERE pdf_uri = ? AND parent_uri = ?",
        (pdf_uri, parent_uri)
    )
    file_exists = cursor.fetchone() is not None




    if file_exists:
        if overwrite:
            cursor.execute("""
                           UPDATE drupal_pdf_files
                           SET drupal_site_id = ?,
                               file_hash      = ?
                           WHERE pdf_uri       = ?
                             AND parent_uri    = ?
                           """, (
                               drupal_site_id,
                               file_hash,
                               pdf_uri,
                               parent_uri
                           ))
            conn.commit()
        else:
            print("PDF file already exists in the database.")
    else:
        cursor.execute("""
                       INSERT INTO drupal_pdf_files (
                           pdf_uri,
                           parent_uri,
                           drupal_site_id,
                           file_hash
                       ) VALUES (?,?,?,?)
                       """, (
                           pdf_uri,
                           parent_uri,
                           drupal_site_id,
                           file_hash
                       ))
        conn.commit()

    conn.close()


def compare_and_remove_updated_pdfs():
    """
    when the full pdf scan is run, duplicates are added if the file hash is different but the url + domain are the same.
    We need to look at similar url + domain combinations and mark as removed all that are older than the current.

    :return:
    """

    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()




def get_all_sites_domain_names():
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()
    sites = cursor.execute("SELECT domain_name FROM drupal_site").fetchall()
    conn.close()

    return [site[0] for site in sites]


def get_site_id_by_domain_name(domain_name):
    """
    Get site ID from database by domain name.
    Handles conversion from folder names (with dashes) to database domain names.
    
    Examples:
        Folder: calstatela-edu_publicsafety_campus-safety-report
        Database: calstatela.edu_publicsafety_campus-safety-report
        
        Only converts dashes to dots in the domain part (before first underscore)
    """
    # Split on first underscore to separate domain from path
    if '_' in domain_name:
        parts = domain_name.split('_', 1)
        # Convert dashes to dots only in the domain part
        domain_part = parts[0].replace('-', '.')
        # Reconstruct with original path part
        domain_name = f"{domain_part}_{parts[1]}"
    else:
        # No underscore, just convert all dashes (simple domain)
        domain_name = domain_name.replace('-', '.')

    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()
    site_id = cursor.execute("SELECT id FROM drupal_site WHERE domain_name = ?", (domain_name,)).fetchone()
    conn.close()
    return site_id[0] if site_id else None




def check_if_pdf_report_exists(pdf_uri, parent_uri):

    # first check if a pdf exists with the pdf_uri and parent_uri
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()
    pdf_file = cursor.execute("SELECT * FROM drupal_pdf_files WHERE pdf_uri = ? AND parent_uri = ?", (pdf_uri, parent_uri)).fetchone()

    if pdf_file:
        # if a pdf exists, check if a report exists for the pdf. We are looking for a hash match so
        # if a file name stays the same but it is made accessible it will still not find a new report.
        pdf_hash = pdf_file[5] if len(pdf_file) > 5 else None
        
        # Skip analysis if hash exists and has a report
        if pdf_hash:
            report = cursor.execute("SELECT * FROM pdf_report WHERE pdf_hash = ?", (pdf_hash,)).fetchone()
            if report:
                conn.close()
                return True
        
        # If PDF file exists but no hash or no report, still return True to skip re-analysis
        # This prevents infinite re-processing of the same PDF
        conn.close()
        return True
    
    conn.close()
    return False


def add_pdf_report_failure(pdf_uri, parent_uri, site_id, error_message):

        conn = sqlite3.connect('drupal_pdfs.db')
        cursor = conn.cursor()

        # get pdf_id from pdf table with pdf_uri and parent_uri
        print(pdf_uri, parent_uri, site_id, error_message)

        pdf_id = cursor.execute("SELECT * FROM drupal_pdf_files WHERE pdf_uri = ? AND parent_uri = ?", (pdf_uri, parent_uri)).fetchone()
        print(pdf_id)
        if pdf_id:
            pdf_id = pdf_id[0]

            # add record to failure table
            cursor.execute("INSERT INTO failure (site_id, pdf_id, error_message) VALUES (?, ?, ?)", (site_id, pdf_id, error_message))
            conn.commit()
            conn.close()
        else:
            # Use pdf_uri as pdf_id if PDF not in system
            cursor.execute("INSERT INTO failure (site_id, pdf_id, error_message) VALUES (?, ?, ?)", (site_id, pdf_uri, error_message))
            conn.commit()
            conn.close()
            print("No PDF in system add raw failure")


def truncate_reports_table():
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pdf_report")
    cursor.execute("DELETE FROM failure")
    conn.commit()
    conn.close()


def mark_pdf_as_removed(pdf_uri, parent_uri):
    """
    Marks a PDF as removed in the database by setting its status to 'removed'.
    """
    conn = sqlite3.connect('drupal_pdfs.db')
    cursor = conn.cursor()

    # Get the PDF file ID
    pdf_file = cursor.execute("SELECT id FROM drupal_pdf_files WHERE pdf_uri = ? AND parent_uri = ?", (pdf_uri, parent_uri)).fetchone()

    if pdf_file:
        pdf_file_id = pdf_file[0]
        # Update the status of the PDF file to 'removed'
        cursor.execute("UPDATE drupal_pdf_files SET removed = 1 WHERE id = ?", (pdf_file_id,))
        conn.commit()
    else:
        print(f"No PDF found with URI: {pdf_uri} and Parent URI: {parent_uri}")

    conn.close()



def import_box_folders():


    conn = sqlite3.connect("drupal_pdfs.db")
    cursor = conn.cursor()

    sql = '''
    UPDATE drupal_site
    SET box_folder = ?
    WHERE domain_name = ?;
    '''

    with open(r"box_folders.csv", "r", encoding='utf-8') as f:
        csvreader = csv.reader(f)
        next(csvreader, None)

        for item in csvreader:
            cursor.execute(sql, (item[1], item[0]))

    conn.commit()
    conn.close()

