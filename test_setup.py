#!/usr/bin/env python3
"""
Quick Test Script for CSULA PDF Checker
Run this to test the workflow with a single domain
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "core"))
sys.path.insert(0, str(project_root / "src" / "data_management"))
sys.path.insert(0, str(project_root / "src" / "communication"))

def test_configuration():
    """Test that configuration is valid"""
    print("\n" + "="*70)
    print("STEP 1: Testing Configuration")
    print("="*70)
    
    try:
        import config
        config.print_config()
        config.validate_config()
        print("\n✅ Configuration is valid!")
        return True
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        return False


def test_database():
    """Test database connection and contents"""
    print("\n" + "="*70)
    print("STEP 2: Testing Database")
    print("="*70)
    
    try:
        import sqlite3
        import config
        
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check sites
        cursor.execute("SELECT COUNT(*) FROM drupal_site")
        site_count = cursor.fetchone()[0]
        print(f"  Sites in database: {site_count}")
        
        # List sites
        cursor.execute("SELECT id, domain_name FROM drupal_site")
        print("\n  Domains configured:")
        for site_id, domain in cursor.fetchall():
            print(f"    [{site_id}] {domain}")
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM site_user")
        user_count = cursor.fetchone()[0]
        print(f"\n  Users in database: {user_count}")
        
        conn.close()
        
        print("\n✅ Database is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_verapdf():
    """Test that VeraPDF is installed"""
    print("\n" + "="*70)
    print("STEP 3: Testing VeraPDF Installation")
    print("="*70)
    
    try:
        import subprocess
        import config
        
        # Use configured command or default to 'verapdf'
        cmd = config.VERAPDF_COMMAND if hasattr(config, 'VERAPDF_COMMAND') else 'verapdf'
        
        # If command is a path with spaces, it might need handling, but subprocess.run handles list args well.
        # If config.VERAPDF_COMMAND is a string path, we should use it.
        
        print(f"  Testing command: {cmd}")
        
        result = subprocess.run([cmd, '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        
        if result.returncode == 0:
            print(f"  {result.stdout.strip()}")
            print("\n✅ VeraPDF is installed!")
            return True
        else:
            print(f"\n⚠️  VeraPDF returned error code: {result.returncode}")
            return False
            
    except FileNotFoundError:
        print("\n❌ VeraPDF is NOT installed!")
        print("   Install from: https://verapdf.org/")
        return False
    except Exception as e:
        print(f"\n❌ VeraPDF test error: {e}")
        return False


def test_spider_generation():
    """Test spider generation for test domains"""
    print("\n" + "="*70)
    print("STEP 4: Testing Spider Generation")
    print("="*70)
    
    try:
        spider_dir = project_root / "crawlers" / "sf_state_pdf_scan" / "sf_state_pdf_scan" / "spiders"
        
        if not spider_dir.exists():
            print(f"❌ Spider directory not found: {spider_dir}")
            return False
        
        # Count existing spiders
        spiders = list(spider_dir.glob("*_spider.py"))
        print(f"  Existing spiders: {len(spiders)}")
        
        for spider in spiders:
            print(f"    - {spider.name}")
        
        if len(spiders) == 0:
            print("\n  ⚠️  No spiders found. Run: python3 config/sites.py")
            print("     (This will be done in the full workflow)")
        else:
            print(f"\n✅ Found {len(spiders)} spider(s)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Spider test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_output_directories():
    """Test that output directories exist and are writable"""
    print("\n" + "="*70)
    print("STEP 5: Testing Output Directories")
    print("="*70)
    
    try:
        import config
        
        dirs_to_check = [
            ("Output", config.OUTPUT_DIR),
            ("Reports", config.OUTPUT_REPORTS_DIR),
            ("Scans", config.PDF_SITES_FOLDER),
            ("Temp", config.TEMP_DIR),
            ("Backups", config.OUTPUT_BACKUPS_DIR),
        ]
        
        all_ok = True
        for name, dir_path in dirs_to_check:
            if dir_path.exists():
                # Test write permission
                test_file = dir_path / ".test_write"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    print(f"  ✓ {name}: {dir_path} (writable)")
                except:
                    print(f"  ✗ {name}: {dir_path} (NOT writable)")
                    all_ok = False
            else:
                print(f"  ✗ {name}: {dir_path} (does not exist)")
                all_ok = False
        
        if all_ok:
            print("\n✅ All output directories are ready!")
        else:
            print("\n⚠️  Some output directories have issues")
        
        return all_ok
        
    except Exception as e:
        print(f"\n❌ Output directory test error: {e}")
        return False


def show_next_steps():
    """Show what to do next"""
    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    
    print("""
To run the complete workflow:

1. Generate spiders for your domains:
   cd crawlers/sf_state_pdf_scan
   python3 ../../config/sites.py

2. Run the spiders to find PDFs:
   python3 run_all_spiders.py

3. Analyze the PDFs:
   cd ../..
   python3 master_functions.py

4. Generate reports:
   (Reports are generated as part of master_functions.py)

5. Check results:
   ls -lh output/scans/
   ls -lh output/reports/

For detailed instructions, see: RUN_WORKFLOW.md

For a quick single-site test:
   See RUN_WORKFLOW.md section "Simplified Test Run"
""")


def main():
    """Run all tests"""
    print("="*70)
    print("CSULA PDF Accessibility Checker - Quick Test")
    print("="*70)
    print("This will verify your setup is ready to run the workflow")
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_configuration()))
    results.append(("Database", test_database()))
    results.append(("VeraPDF", test_verapdf()))
    results.append(("Spider Generation", test_spider_generation()))
    results.append(("Output Directories", test_output_directories()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 All tests passed! Ready to run the workflow.")
        show_next_steps()
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before proceeding.")
        print("   See CONFIG_SETUP.md for troubleshooting help.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
