#!/usr/bin/env python3
"""
Migration script to help transition from the old structure to the new modular structure.
"""

import os
import shutil
import sys

def check_files():
    """Check if old files exist and new structure is in place."""
    old_files = ['schedule_scraper.py']
    new_dirs = ['src', 'src/utils', 'src/services']
    
    # Check if old files exist
    old_exists = any(os.path.exists(f) for f in old_files)
    
    # Check if new structure exists
    new_exists = all(os.path.exists(d) for d in new_dirs)
    
    return old_exists, new_exists

def backup_files():
    """Backup old files."""
    if not os.path.exists('backup'):
        os.mkdir('backup')
    
    if os.path.exists('schedule_scraper.py'):
        shutil.copy('schedule_scraper.py', 'backup/schedule_scraper.py')
        print("✅ Backed up schedule_scraper.py")
    
    if os.path.exists('token.pickle'):
        shutil.copy('token.pickle', 'backup/token.pickle')
        print("✅ Backed up token.pickle")
    
    if os.path.exists('credentials.json'):
        shutil.copy('credentials.json', 'src/credentials.json')
        print("✅ Copied credentials.json to new location")
    
    if os.path.exists('.env'):
        shutil.copy('.env', 'src/.env')
        print("✅ Copied .env to new location")

def main():
    """Main migration function."""
    print("\n🔄 Farm Boy Schedule Scraper - Migration Script")
    print("=============================================")
    
    old_exists, new_exists = check_files()
    
    if not old_exists:
        print("\n❌ No old files found to migrate.")
        return
    
    if not new_exists:
        print("\n❌ New directory structure not found.")
        print("Please make sure you've cloned or updated the repository correctly.")
        return
    
    print("\n🔍 Found old files to migrate.")
    
    # Ask for confirmation
    confirm = input("\nDo you want to backup your old files and prepare for the new structure? (y/n): ")
    if confirm.lower() != 'y':
        print("Migration cancelled.")
        return
    
    # Backup files
    backup_files()
    
    print("\n✅ Migration complete!")
    print("\nYou can now use the new modular structure:")
    print("1. Run 'python3 setup_google_calendar.py' to set up Google Calendar")
    print("2. Run 'python3 main.py' to scrape your schedule")
    
    # Ask if they want to delete old files
    delete = input("\nDo you want to delete the old schedule_scraper.py file? (y/n): ")
    if delete.lower() == 'y':
        if os.path.exists('schedule_scraper.py'):
            os.remove('schedule_scraper.py')
            print("✅ Deleted schedule_scraper.py")
    
    print("\n🎉 All done! Enjoy the new modular structure.")

if __name__ == "__main__":
    main() 