#!/usr/bin/env python3
"""
Setup Test Environment for CSULA PDF Checker
=============================================

This script helps you set up a test environment with sample data.
Run this script to create a test database and populate it with sample domains,
users, and assignments.

Usage:
    python3 setup_test_environment.py
"""

import csv
import sqlite3
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import configuration
import config

def create_database_tables():
    """Create all necessary database tables."""
    print("\n📊 Creating database tables...")
    
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create sites table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drupal_site (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain_name TEXT NOT NULL UNIQUE,
            page_title TEXT,
            security_group_name TEXT,
            box_folder TEXT
        );
    """)
    
    # Create PDF files table
    cursor.execute("""
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
    """)
    
    # Create PDF report table
    cursor.execute("""
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
            approved_pdf_exporter BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (pdf_hash) REFERENCES drupal_pdf_files(file_hash)
        );
    """)
    
    # Create site users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_user (
            employee_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL,
            is_manager BOOLEAN DEFAULT FALSE
        );
    """)
    
    # Create site assignments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_assignment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY (site_id) REFERENCES drupal_site(id),
            FOREIGN KEY (user_id) REFERENCES site_user(employee_id),
            UNIQUE(site_id, user_id)
        );
    """)
    
    # Create failure tracking table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS failure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            pdf_id TEXT NOT NULL,
            error_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT NOT NULL,
            FOREIGN KEY (site_id) REFERENCES drupal_site(id),
            FOREIGN KEY (pdf_id) REFERENCES drupal_pdf_files(id)
        );
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Database tables created successfully!")


def create_test_sites_csv():
    """Create a test sites.csv file with CSULA domains."""
    print("\n📝 Creating test sites.csv file...")
    
    # Use TEST_DOMAINS from config if USE_TEST_DOMAINS_ONLY is True
    if config.USE_TEST_DOMAINS_ONLY:
        domains = config.TEST_DOMAINS
    else:
        # Default to these domains for production
        domains = [
            "www.calstatela.edu",
            "www-adminfin.calstatela.edu",
            "academicsenate.calstatela.edu",
        ]
    
    # Create security group names from domains
    test_sites = []
    for domain in domains:
        # Normalize domain for database storage (replace / with _)
        normalized_domain = domain.replace('/', '_')
        
        # Convert domain to security group name (e.g., calstatela.edu -> CSULA-d-main-site-content-manager)
        if domain == "calstatela.edu" or domain == "www.calstatela.edu":
            security_group = "CSULA-d-main-site-content-manager"
        elif "adminfin" in domain:
            security_group = "CSULA-d-adminfin-content-manager"
        elif "senate" in domain:
            security_group = "CSULA-d-senate-content-manager"
        elif "publicsafety" in domain:
            security_group = "CSULA-d-publicsafety-content-manager"
        else:
            # Generic security group for other domains
            security_group = f"CSULA-d-{domain.replace('.', '-').replace('/', '-').replace('www-', '')}-content-manager"
        
        test_sites.append((normalized_domain, security_group))
    
    with open(config.SITES_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        for domain, security_group in test_sites:
            writer.writerow([domain, security_group])
    
    print(f"✅ Created {config.SITES_CSV} with {len(test_sites)} test domains")
    return test_sites


def create_test_employees_csv():
    """Create test employees CSV files."""
    print("\n👥 Creating test employees.csv file...")
    
    # Base employee data
    all_employees = [
        ("Pavan Chauhan", "123456", "pchauha5@calstatela.edu"),
        ("Jane Smith", "234567", "jane.smith@calstatela.edu"),
        ("Bob Johnson", "345678", "bob.johnson@calstatela.edu"),
    ]
    
    # Only create employees for the number of domains we have
    num_domains = len(config.TEST_DOMAINS) if config.USE_TEST_DOMAINS_ONLY else 3
    test_employees = all_employees[:num_domains]
    
    with open(config.EMPLOYEES_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Full Name", "Employee ID", "Email"])
        for name, emp_id, email in test_employees:
            writer.writerow([name, emp_id, email])
    
    print(f"✅ Created {config.EMPLOYEES_CSV} with {len(test_employees)} test employees")
    return test_employees


def create_test_managers_csv():
    """Create test managers CSV file."""
    print("\n👔 Creating test managers.csv file...")
    
    # Make the first employee a manager
    test_managers = [("123456",)]
    
    with open(config.MANAGERS_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        for emp_id, in test_managers:
            writer.writerow([emp_id])
    
    print(f"✅ Created {config.MANAGERS_CSV} with {len(test_managers)} test managers")
    return test_managers


def create_test_site_assignments_csv(test_sites, test_employees):
    """Create test site assignments CSV file."""
    print("\n📋 Creating test site_assignments.csv file...")
    
    # Create assignments based on actual sites and employees
    test_assignments = []
    for i, (domain, security_group) in enumerate(test_sites):
        if i < len(test_employees):
            name, emp_id, email = test_employees[i]
            test_assignments.append((security_group, name, emp_id, email))
    
    with open(config.SITE_ASSIGNMENTS_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        for security_group, name, emp_id, email in test_assignments:
            writer.writerow([security_group, name, emp_id, email])
    
    print(f"✅ Created {config.SITE_ASSIGNMENTS_CSV} with {len(test_assignments)} test assignments")
    return test_assignments


def populate_database_from_csv():
    """Populate database with data from CSV files."""
    print("\n💾 Populating database from CSV files...")
    
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Add sites
    sites_added = 0
    with open(config.SITES_CSV, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                domains = row[0].split(',')
                security_group = row[1] if len(row) > 1 else None
                
                for domain in domains:
                    domain = domain.strip().replace("www.", "", 1)
                    cursor.execute(
                        "INSERT OR IGNORE INTO drupal_site (domain_name, security_group_name) VALUES (?, ?)",
                        (domain, security_group)
                    )
                    if cursor.rowcount > 0:
                        sites_added += 1
    
    conn.commit()
    print(f"  ✓ Added {sites_added} sites to database")
    
    # Add employees
    employees_added = 0
    with open(config.EMPLOYEES_CSV, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            if row and len(row) >= 3:
                full_name = row[0]
                employee_id = row[1]
                email = row[2]
                
                name_parts = full_name.split(" ")
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                
                cursor.execute(
                    "INSERT OR IGNORE INTO site_user (employee_id, first_name, last_name, email) VALUES (?, ?, ?, ?)",
                    (employee_id, first_name, last_name, email)
                )
                if cursor.rowcount > 0:
                    employees_added += 1
    
    conn.commit()
    print(f"  ✓ Added {employees_added} employees to database")
    
    # Mark managers
    managers_marked = 0
    with open(config.MANAGERS_CSV, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                employee_id = row[0]
                cursor.execute(
                    "UPDATE site_user SET is_manager = 1 WHERE employee_id = ?",
                    (employee_id,)
                )
                if cursor.rowcount > 0:
                    managers_marked += 1
    
    conn.commit()
    print(f"  ✓ Marked {managers_marked} employees as managers")
    
    # Add site assignments
    assignments_added = 0
    with open(config.SITE_ASSIGNMENTS_CSV, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row and len(row) >= 4:
                security_group = row[0]
                employee_id = row[2]
                
                # Get site ID
                site_result = cursor.execute(
                    "SELECT id FROM drupal_site WHERE security_group_name = ?",
                    (security_group,)
                ).fetchone()
                
                if site_result:
                    site_id = site_result[0]
                    cursor.execute(
                        "INSERT OR IGNORE INTO site_assignment (site_id, user_id) VALUES (?, ?)",
                        (site_id, employee_id)
                    )
                    if cursor.rowcount > 0:
                        assignments_added += 1
    
    conn.commit()
    conn.close()
    print(f"  ✓ Added {assignments_added} site assignments to database")


def display_database_summary():
    """Display a summary of what's in the database."""
    print("\n📊 Database Summary:")
    print("=" * 60)
    
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Count sites
    cursor.execute("SELECT COUNT(*) FROM drupal_site")
    site_count = cursor.fetchone()[0]
    print(f"  Sites: {site_count}")
    
    # Count users
    cursor.execute("SELECT COUNT(*) FROM site_user")
    user_count = cursor.fetchone()[0]
    print(f"  Users: {user_count}")
    
    # Count managers
    cursor.execute("SELECT COUNT(*) FROM site_user WHERE is_manager = 1")
    manager_count = cursor.fetchone()[0]
    print(f"  Managers: {manager_count}")
    
    # Count assignments
    cursor.execute("SELECT COUNT(*) FROM site_assignment")
    assignment_count = cursor.fetchone()[0]
    print(f"  Site Assignments: {assignment_count}")
    
    print("=" * 60)
    
    # Show site details
    print("\n📍 Test Sites:")
    cursor.execute("SELECT id, domain_name, security_group_name FROM drupal_site")
    for site_id, domain, sec_group in cursor.fetchall():
        print(f"  [{site_id}] {domain}")
        print(f"      Security Group: {sec_group}")
        
        # Show assigned users
        cursor.execute("""
            SELECT su.first_name, su.last_name, su.email, su.is_manager
            FROM site_assignment sa
            JOIN site_user su ON sa.user_id = su.employee_id
            WHERE sa.site_id = ?
        """, (site_id,))
        
        assignments = cursor.fetchall()
        if assignments:
            for fname, lname, email, is_mgr in assignments:
                mgr_badge = " [Manager]" if is_mgr else ""
                print(f"      → {fname} {lname}{mgr_badge} ({email})")
        print()
    
    conn.close()


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup Test Environment for CSULA PDF Checker")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print("=" * 70)
    print("CSULA PDF Accessibility Checker - Test Environment Setup")
    print("=" * 70)
    
    # Show current configuration
    config.print_config()
    
    # Ask for confirmation
    print("\n⚠️  This will create/overwrite:")
    print(f"  - Database: {config.DATABASE_PATH}")
    print(f"  - CSV files in: {config.DATA_DIR}")
    print()
    
    if args.force:
        print("⏩ Force mode enabled: Skipping confirmation prompt.")
    else:
        response = input("Continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Setup cancelled.")
            return
    
    try:
        # Step 1: Create database tables
        create_database_tables()
        
        # Step 2: Create test CSV files
        test_sites = create_test_sites_csv()
        test_employees = create_test_employees_csv()
        create_test_managers_csv()
        create_test_site_assignments_csv(test_sites, test_employees)
        
        # Step 3: Populate database from CSV files
        populate_database_from_csv()
        
        # Step 4: Display summary
        display_database_summary()
        
        print("\n" + "=" * 70)
        print("✅ Test environment setup complete!")
        print("=" * 70)
        print("\n📝 Next Steps:")
        print("  1. Review the test data above")
        print("  2. Adjust config.py if needed")
        print("  3. Run: python3 master_functions.py")
        print("  4. Or test individual components")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
