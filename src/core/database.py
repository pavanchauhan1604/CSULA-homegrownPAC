import sqlite3
import csv
# Define the connection and cursor
conn = sqlite3.connect('drupal_pdfs.db')
cursor = conn.cursor()

# Define SQL commands to create three tables
create_pdf_table = """
CREATE TABLE IF NOT EXISTS drupal_pdf_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_uri TEXT NOT NULL,
    parent_uri TEXT NOT NULL,
    scanned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    drupal_site_id INTEGER NOT NULL,
    file_hash TEXT,
    pdf_returns_404 Boolean DEFAULT FALSE,
    parent_returns_404 Boolean DEFAULT FALSE,
    FOREIGN KEY (drupal_site_id) REFERENCES drupal_site(id)
);
"""

create_site_table = """
CREATE TABLE IF NOT EXISTS drupal_site (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain_name TEXT NOT NULL,
    page_title TEXT,
    security_group_name TEXT,
    box_folder TEXT

);
"""

create_site_user = """
CREATE TABLE IF NOT EXISTS site_user (
    employee_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL,
    is_manager BOOLEAN DEFAULT FALSE
    

);
"""



create_pdf_report = """
CREATE TABLE IF NOT EXISTS pdf_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_hash TEXT UNIQUE NOT NULL,
    violations INTEGER NOT NULL,
    failed_checks INTEGER NOT NULL,
    tagged BOOLEAN DEFAULT FALSE,
    check_for_image_only BOOLEAN DEFAULT FALSE,
    pdf_text_type TEXT,
    title_set BOOLEAN DEFAULT FALSE,
    language_set BOOLEAN DEFAULT FALSE,
    page_count INTEGER,
    has_form BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (pdf_hash) REFERENCES drupal_pdf_files(file_hash)
);
"""



create_site_assignment = """
CREATE TABLE IF NOT EXISTS site_assignment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    FOREIGN KEY (site_id) REFERENCES drupal_site(id),
    FOREIGN KEY (user_id) REFERENCES site_user(employee_id),
    UNIQUE(site_id, user_id)
);
"""


create_report_failure = """

CREATE TABLE IF NOT EXISTS failure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    pdf_id TEXT NOT NULL,
    error_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT NOT NULL,
    FOREIGN KEY (site_id) REFERENCES drupal_site(id),
    FOREIGN KEY (pdf_id) REFERENCES drupal_pdf_files(id)

);

"""




# cursor.execute(create_pdf_table)
# cursor.execute(create_pdf_report)
# cursor.execute(create_site_table)
# cursor.execute(create_site_user)
# cursor.execute(create_site_assignment)
# cursor.execute(create_report_failure)
#
#
# # Commit the changes and close the connection
# conn.commit()
# conn.close()

print("Database and tables created successfully.")





