"""
Calendar service for ICS file creation and Google Calendar integration.
"""

import uuid
import os
import pickle
from datetime import datetime
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from src.utils.date_parser import parse_date_time

def create_ics(shift_data, output_file='schedule.ics'):
    """
    Create an ICS calendar file from shift data.
    
    Args:
        shift_data (list): List of shift dictionaries
        output_file (str, optional): Output file name. Defaults to 'schedule.ics'.
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        current_year = datetime.now().year
        ics_content = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//MyFarmBoy Schedule//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]

        local_tz = pytz.timezone('America/Toronto')
        added_count = 0

        for shift in shift_data:
            if shift.get('status', '').lower() == 'absent':
                print(f"Skipping absent shift: {shift['date']}")
                continue

            start_dt, end_dt = parse_date_time(shift['date'], shift['time'], current_year)
            if not start_dt or not end_dt:
                print(f"Skipping invalid shift: {shift['date']} {shift['time']}")
                continue

            # Format dates according to iCalendar spec
            start_str = start_dt.strftime("%Y%m%dT%H%M%S")
            end_str = end_dt.strftime("%Y%m%dT%H%M%S")
            event_uid = str(uuid.uuid4())
            created_time = datetime.now().strftime("%Y%m%dT%H%M%SZ")

            role = shift.get('role', 'Farm Boy Employee')
            department = shift.get('department', 'Farm Boy')
            summary = f"Work: {role} ({department})"
            description = f"Role: {role}\\nDepartment: {department}\\nDuration: {shift.get('duration', 'N/A')}"

            # Add event to calendar
            ics_content.extend([
                "BEGIN:VEVENT",
                f"UID:{event_uid}",
                f"DTSTAMP:{created_time}",
                f"DTSTART:{start_str}",
                f"DTEND:{end_str}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                f"LOCATION:Farm Boy",
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                "DESCRIPTION:Work shift reminder",
                "TRIGGER:-PT30M",  # 30 minutes before
                "END:VALARM",
                "END:VEVENT"
            ])
            added_count += 1
            print(f"Added to ICS: {summary} on {start_dt.strftime('%Y-%m-%d %H:%M')}")

        ics_content.append("END:VCALENDAR")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(ics_content))

        print(f"ICS file created: {output_file} with {added_count} events")
        print("\nTo import into Google Calendar:")
        print("1. Go to https://calendar.google.com/")
        print("2. Click the '+' next to 'Other calendars'")
        print("3. Select 'Import'")
        print("4. Upload the generated ICS file")
        return True
    except Exception as e:
        print(f"Error creating ICS file: {str(e)}")
        return False

def get_google_calendar_service():
    """
    Get Google Calendar API service using OAuth 2.0.
    
    Returns:
        service: Google Calendar API service or None if authentication fails
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # If credentials.json doesn't exist, guide the user
            if not os.path.exists('credentials.json'):
                print("Error: credentials.json file not found!")
                print("Please download your OAuth 2.0 credentials from Google Cloud Console:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a project and enable the Google Calendar API")
                print("3. Create OAuth 2.0 credentials (Desktop app)")
                print("4. Download the credentials.json file and place it in this directory")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/calendar'])
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

def add_events_to_google_calendar(shift_data, calendar_id=None):
    """
    Add shift events to Google Calendar.
    
    Args:
        shift_data (list): List of shift dictionaries
        calendar_id (str, optional): Google Calendar ID. Defaults to primary calendar.
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get calendar service
        service = get_google_calendar_service()
        if service is None:
            return False
            
        if calendar_id is None:
            calendar_id = 'primary'  # Use primary calendar if none specified

        timezone = 'America/Toronto'
        current_year = datetime.now().year
        added_count = 0
        
        # Check if calendar exists and is accessible
        try:
            calendar_info = service.calendarList().get(calendarId=calendar_id).execute()
            print(f"Using calendar: {calendar_info.get('summary', calendar_id)}")
        except Exception as e:
            print(f"Warning: Could not access calendar {calendar_id}. Error: {e}")
            print("Will attempt to use primary calendar instead.")
            calendar_id = 'primary'

        for shift in shift_data:
            if shift.get('status', '').lower() == 'absent':
                print(f"Skipping absent shift for Google Calendar: {shift['date']}")
                continue

            start_dt, end_dt = parse_date_time(shift['date'], shift['time'], current_year)
            if not start_dt or not end_dt:
                print(f"Skipping invalid shift for Google Calendar: {shift['date']} {shift['time']}")
                continue
                
            role = shift.get('role', 'Farm Boy Employee')
            department = shift.get('department', 'Farm Boy')
            summary = f"Work: {role} ({department})"
            description = f"Role: {role}\nDepartment: {department}\nDuration: {shift.get('duration', 'N/A')}"

            event = {
                'summary': summary,
                'location': 'Farm Boy',
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': timezone,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 30}
                    ]
                }
            }

            try:
                created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
                added_count += 1
                print(f"✅ Added to Google Calendar: {summary} on {start_dt.strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                print(f"Failed to add event {summary} on {start_dt}: {e}")
                
        print(f"Successfully added {added_count} events to Google Calendar")
        return added_count > 0
    except Exception as e:
        print(f"Failed to add events to Google Calendar: {e}")
        print("Make sure you have:")
        print("1. A valid credentials.json file with Google Calendar API access")
        print("2. Proper permissions for the calendar you're trying to access")
        return False 