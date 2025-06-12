"""
Calendar service for ICS file creation and Google Calendar integration.
"""

import uuid
import os
import pickle
from datetime import datetime, timedelta
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from src.utils.date_parser import parse_date_time

# Define timezone
TIMEZONE = pytz.timezone('America/Toronto')

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

def find_duplicate_events(service, calendar_id, date):
    """
    Find duplicate Farm Boy work events on a specific date.
    
    Args:
        service: Google Calendar API service
        calendar_id (str): Calendar ID
        date (datetime): The date to check for duplicates
        
    Returns:
        list: List of duplicate event IDs
    """
    try:
        # Set time boundaries for the day (in UTC)
        start_of_day = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_of_day = datetime(date.year, date.month, date.day, 23, 59, 59)
        
        # Convert to timezone-aware datetimes
        start_of_day = TIMEZONE.localize(start_of_day).isoformat()
        end_of_day = TIMEZONE.localize(end_of_day).isoformat()
        
        # Get all events for the day
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Group events by start time and summary
        event_groups = {}
        for event in events:
            # Only process Farm Boy work events
            if 'Work:' in event.get('summary', '') and event.get('location', '') == 'Farm Boy':
                start_time = event['start'].get('dateTime', '')
                summary = event.get('summary', '')
                
                # Create a key for grouping
                key = f"{start_time}_{summary}"
                
                if key not in event_groups:
                    event_groups[key] = []
                
                event_groups[key].append(event)
        
        # Find duplicates (groups with more than one event)
        duplicates = []
        for key, group in event_groups.items():
            if len(group) > 1:
                # Keep the first event, mark the rest as duplicates
                for event in group[1:]:
                    duplicates.append(event['id'])
                    print(f"Found duplicate: {event.get('summary')} on {event['start'].get('dateTime')}")
        
        return duplicates
    
    except Exception as e:
        print(f"Error finding duplicate events: {e}")
        return []

def remove_duplicate_events(service, calendar_id, event_ids):
    """
    Remove duplicate events from the calendar.
    
    Args:
        service: Google Calendar API service
        calendar_id (str): Calendar ID
        event_ids (list): List of event IDs to remove
        
    Returns:
        int: Number of events removed
    """
    removed_count = 0
    
    for event_id in event_ids:
        try:
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            removed_count += 1
            print(f"Removed duplicate event (ID: {event_id})")
        except Exception as e:
            print(f"Error removing event {event_id}: {e}")
    
    return removed_count

def check_event_exists(service, calendar_id, start_time, end_time, summary):
    """
    Check if an event with similar time and summary already exists in the calendar.
    
    Args:
        service: Google Calendar API service
        calendar_id (str): Calendar ID
        start_time (datetime): Event start time
        end_time (datetime): Event end time
        summary (str): Event summary/title
        
    Returns:
        bool: True if a similar event exists, False otherwise
    """
    try:
        # Make sure start_time and end_time are timezone-aware
        if start_time.tzinfo is None:
            start_time = TIMEZONE.localize(start_time)
        if end_time.tzinfo is None:
            end_time = TIMEZONE.localize(end_time)
        
        # Define time range to search (1 hour before and after the event)
        time_min = (start_time - timedelta(hours=1)).isoformat()
        time_max = (end_time + timedelta(hours=1)).isoformat()
        
        # Search for events in the time range
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Check if any event matches our criteria
        for event in events:
            event_summary = event.get('summary', '')
            
            # If summary contains "Work: " and the location is "Farm Boy", consider it a potential match
            if 'Work:' in event_summary and event.get('location', '') == 'Farm Boy':
                # Get start and end times
                event_start = event['start'].get('dateTime')
                event_end = event['end'].get('dateTime')
                
                if event_start and event_end:
                    # Convert to datetime objects with timezone handling
                    event_start_dt = datetime.fromisoformat(event_start)
                    event_end_dt = datetime.fromisoformat(event_end)
                    
                    # Check if times overlap (with 30 minute tolerance)
                    time_diff_start = abs((start_time - event_start_dt).total_seconds()) / 60
                    time_diff_end = abs((end_time - event_end_dt).total_seconds()) / 60
                    
                    if time_diff_start < 30 and time_diff_end < 30:
                        print(f"Found existing event: {event_summary} at {event_start}")
                        return True
        
        return False
    except Exception as e:
        print(f"Error checking for existing events: {e}")
        # In case of error, assume event doesn't exist
        return False

def clean_duplicate_events(service, calendar_id, dates):
    """
    Clean up duplicate Farm Boy work events for the given dates.
    
    Args:
        service: Google Calendar API service
        calendar_id (str): Calendar ID
        dates (list): List of dates to check for duplicates
        
    Returns:
        int: Number of duplicate events removed
    """
    total_removed = 0
    
    for date in dates:
        duplicate_ids = find_duplicate_events(service, calendar_id, date)
        if duplicate_ids:
            removed = remove_duplicate_events(service, calendar_id, duplicate_ids)
            total_removed += removed
            print(f"Removed {removed} duplicate events on {date.strftime('%Y-%m-%d')}")
    
    return total_removed

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

        current_year = datetime.now().year
        added_count = 0
        skipped_count = 0
        
        # Check if calendar exists and is accessible
        try:
            calendar_info = service.calendarList().get(calendarId=calendar_id).execute()
            print(f"Using calendar: {calendar_info.get('summary', calendar_id)}")
        except Exception as e:
            print(f"Warning: Could not access calendar {calendar_id}. Error: {e}")
            print("Will attempt to use primary calendar instead.")
            calendar_id = 'primary'
        
        # Collect all dates to check for duplicates
        shift_dates = []
        for shift in shift_data:
            start_dt, _ = parse_date_time(shift['date'], shift['time'], current_year)
            if start_dt and start_dt.date() not in shift_dates:
                shift_dates.append(start_dt.date())
        
        # Clean up any existing duplicates before adding new events
        if shift_dates:
            print("\n🧹 Checking for existing duplicate events...")
            removed_count = clean_duplicate_events(service, calendar_id, shift_dates)
            if removed_count > 0:
                print(f"✅ Removed {removed_count} duplicate events")
            else:
                print("✅ No duplicate events found")

        print("\n📅 Processing shifts...")
        for shift in shift_data:
            if shift.get('status', '').lower() == 'absent':
                print(f"Skipping absent shift for Google Calendar: {shift['date']}")
                continue

            start_dt, end_dt = parse_date_time(shift['date'], shift['time'], current_year)
            if not start_dt or not end_dt:
                print(f"Skipping invalid shift for Google Calendar: {shift['date']} {shift['time']}")
                continue
            
            # Ensure datetimes are timezone-aware
            if start_dt.tzinfo is None:
                start_dt = TIMEZONE.localize(start_dt)
            if end_dt.tzinfo is None:
                end_dt = TIMEZONE.localize(end_dt)
                
            role = shift.get('role', 'Farm Boy Employee')
            department = shift.get('department', 'Farm Boy')
            summary = f"Work: {role} ({department})"
            description = f"Role: {role}\nDepartment: {department}\nDuration: {shift.get('duration', 'N/A')}"

            # Check if event already exists
            if check_event_exists(service, calendar_id, start_dt, end_dt, summary):
                print(f"⏭️ Skipping duplicate event: {summary} on {start_dt.strftime('%Y-%m-%d %H:%M')}")
                skipped_count += 1
                continue

            event = {
                'summary': summary,
                'location': 'Farm Boy',
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': TIMEZONE.zone,
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': TIMEZONE.zone,
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
                
        print(f"\nSuccessfully added {added_count} events to Google Calendar")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} events that already existed in the calendar")
        return added_count > 0 or skipped_count > 0
    except Exception as e:
        print(f"Failed to add events to Google Calendar: {e}")
        print("Make sure you have:")
        print("1. A valid credentials.json file with Google Calendar API access")
        print("2. Proper permissions for the calendar you're trying to access")
        return False 