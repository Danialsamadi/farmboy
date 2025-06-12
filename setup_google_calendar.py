#!/usr/bin/env python3
"""
Google Calendar API Setup Script
This script helps you set up and test your Google Calendar API credentials.
"""

import os
import sys
import pickle
import webbrowser
from datetime import datetime, timedelta

# Import from our modular structure
from src.services.calendar_service import get_google_calendar_service

def check_credentials_file():
    """Check if credentials.json exists in the current directory."""
    if not os.path.exists('credentials.json'):
        print("\n❌ Error: credentials.json file not found!")
        print("\nPlease follow these steps to get your credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable the Google Calendar API")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search for 'Google Calendar API' and enable it")
        print("4. Create OAuth credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth client ID'")
        print("   - Select 'Desktop app' as the application type")
        print("   - Name your OAuth client")
        print("   - Download the credentials JSON file")
        print("5. Rename the downloaded file to 'credentials.json'")
        print("   and place it in the same directory as this script")
        
        open_console = input("\nWould you like to open the Google Cloud Console now? (y/n): ")
        if open_console.lower() == 'y':
            webbrowser.open('https://console.cloud.google.com/')
        
        return False
    return True

def test_calendar_access(service):
    """Test access to the Google Calendar API by listing calendars."""
    try:
        print("\n🔍 Testing calendar access...")
        calendar_list = service.calendarList().list().execute()
        
        print("\n✅ Successfully connected to Google Calendar API!")
        print("\nAvailable calendars:")
        
        for calendar in calendar_list['items']:
            print(f"- {calendar['summary']} (ID: {calendar['id']})")
            
        return True
    except Exception as e:
        print(f"\n❌ Error accessing Google Calendar: {e}")
        return False

def create_test_event(service):
    """Create a test event in the primary calendar."""
    try:
        # Ask user if they want to create a test event
        create_event = input("\nWould you like to create a test event in your primary calendar? (y/n): ")
        if create_event.lower() != 'y':
            return True
        
        # Create event 1 hour from now, lasting 30 minutes
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=30)
        
        event = {
            'summary': 'Test Event - Farm Boy Schedule',
            'location': 'Farm Boy',
            'description': 'This is a test event created by the Farm Boy Schedule Scraper setup script.',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Toronto',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Toronto',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }
        
        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"\n✅ Test event created successfully!")
        print(f"Event link: {event.get('htmlLink')}")
        
        # Ask if they want to delete the test event
        delete_event = input("\nWould you like to delete this test event? (y/n): ")
        if delete_event.lower() == 'y':
            service.events().delete(calendarId='primary', eventId=event['id']).execute()
            print("✅ Test event deleted.")
        
        return True
    except Exception as e:
        print(f"\n❌ Error creating test event: {e}")
        return False

def main():
    """Main function to set up and test Google Calendar API."""
    print("\n🔧 Google Calendar API Setup Script 🔧")
    print("======================================")
    
    # Check if credentials.json exists
    if not check_credentials_file():
        return
    
    try:
        # Get calendar service using our modular service
        print("\n🔑 Authenticating with Google...")
        service = get_google_calendar_service()
        
        if service is None:
            print("\n❌ Authentication failed.")
            return
        
        # Test calendar access
        if not test_calendar_access(service):
            return
        
        # Create test event
        create_test_event(service)
        
        print("\n✅ Setup complete! You're ready to use the Farm Boy Schedule Scraper.")
        print("Run 'python main.py' to scrape your schedule and add it to your calendar.")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        return

if __name__ == "__main__":
    main() 