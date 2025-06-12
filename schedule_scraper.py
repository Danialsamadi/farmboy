from selenium import webdriver
from selenium.webdriver.safari.service import Service
from selenium.webdriver.safari.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import time
import sys
from datetime import datetime, timedelta
import re
import uuid
import pytz
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
# Load environment variables
load_dotenv()

def setup_driver():
    try:
        safari_options = Options()
        safari_options.set_capability('platformName', 'mac')
        safari_options.set_capability('browserName', 'safari')
        service = Service()
        driver = webdriver.Safari(service=service, options=safari_options)
        return driver
    except Exception as e:
        print(f"Error setting up Safari driver: {str(e)}")
        print("\nPlease make sure you have:")
        print("1. Safari installed")
        print("2. Remote Automation enabled in Safari > Develop menu")
        print("3. Required Python packages installed (pip install -r requirements.txt)")
        sys.exit(1)

def login(driver, email, password):
    try:
        print("Navigating to login page...")
        driver.get('https://myfarmboy.ca/login')
        wait = WebDriverWait(driver, 10)

        print("Looking for email field...")
        email_field = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '#__layout > div > div > form > div > div:nth-child(1) > input'
        )))

        print("Looking for password field...")
        password_field = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, '#__layout > div > div > form > div > div:nth-child(2) > input'
        )))

        email_field.clear()
        email_field.send_keys(email)
        password_field.clear()
        time.sleep(1)
        password_field.send_keys(password)
        time.sleep(1)

        print("Looking for Sign In button...")
        sign_in_button = wait.until(EC.element_to_be_clickable((
            By.CSS_SELECTOR, 'button.w-full.px-6.py-2.mt-4.bg-green-10.rounded-lg'
        )))

        print("Clicking Sign In button...")
        driver.execute_script("arguments[0].click();", sign_in_button)
        print("Waiting for login to complete...")
        time.sleep(5)

        if '/login' in driver.current_url:
            print("Login failed - still on login page")
            try:
                error_message = driver.find_element(By.CLASS_NAME, 'error-message')
                print(f"Error message: {error_message.text}")
            except:
                print("No error message found")
            return False

        print("Successfully logged in!")
        return True
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return False

def scrape_schedule(driver):
    try:
        print("Navigating to schedule page...")
        driver.get('https://myfarmboy.ca/schedule')
        wait = WebDriverWait(driver, 10)

        print("Waiting for schedule content to load...")
        wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, 'div.rounded-md.p-3.my-3.bg-gray-50'
        )))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        schedule_cards = soup.find_all('div', class_='rounded-md p-3 my-3 bg-gray-50')
        print(f"Found {len(schedule_cards)} schedule cards")

        schedule_text = []
        shift_data = []

        for card in schedule_cards:
            try:
                day_element = card.find_previous('h3', class_='text-lg')
                day = day_element.get_text(strip=True) if day_element else "Day not found"

                time_div = card.find('div', class_='font-bold')
                time_text = time_div.get_text(strip=True) if time_div else "Time not found"

                status_div = card.find('div', class_='rounded-sm')
                status = status_div.get_text(strip=True) if status_div else "Active"

                role_div = card.find('div', string=lambda text: text and 'Role:' in text)
                role = role_div.find('span', class_='capitalize').get_text(strip=True) if role_div else "Role not found"

                department_div = card.find('div', string=lambda text: text and 'Department:' in text)
                department = department_div.find('span', class_='capitalize').get_text(strip=True) if department_div else "Department not found"

                duration_p = card.find('p', class_='text-xl font-bold')
                duration = duration_p.get_text(strip=True) if duration_p else "Duration not found"

                shift_info = (
                    f"Date: {day}\n"
                    f"Time: {time_text}\n"
                    f"Status: {status}\n"
                    f"Role: {role}\n"
                    f"Department: {department}\n"
                    f"Duration: {duration}\n"
                    f"{'-'*30}"
                )

                shift_data.append({
                    'date': day,
                    'time': time_text,
                    'status': status,
                    'role': role,
                    'department': department,
                    'duration': duration
                })

                schedule_text.append(shift_info)
                print(f"Processed shift for {day} - Status: {status}")
            except Exception as e:
                print(f"Error parsing card: {str(e)}")
                continue

        if not schedule_text:
            print("No schedule data found")
            return None, None

        return '\n\n'.join(schedule_text), shift_data
    except Exception as e:
        print(f"Scraping failed: {str(e)}")
        return None, None

def parse_date_time(date_str, time_str, current_year=None):
    try:
        if current_year is None:
            current_year = datetime.now().year

        date_match = re.match(r'([A-Za-z]+),\s+([A-Za-z]+)\s+(\d+)(st|nd|rd|th)?', date_str)
        if not date_match:
            raise ValueError(f"Unrecognized date format: {date_str}")

        weekday, month_str, day = date_match.groups()[0:3]

        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }

        month = months.get(month_str, None)
        if month is None:
            raise ValueError(f"Invalid month: {month_str}")

        time_match = re.match(r'(\d+):(\d+)\s*([AP]M)\s*to\s*(\d+):(\d+)\s*([AP]M)', time_str)
        if not time_match:
            raise ValueError(f"Unrecognized time format: {time_str}")

        start_hour, start_min, start_ampm, end_hour, end_min, end_ampm = time_match.groups()

        start_hour = int(start_hour)
        if start_ampm == 'PM' and start_hour < 12:
            start_hour += 12
        elif start_ampm == 'AM' and start_hour == 12:
            start_hour = 0

        end_hour = int(end_hour)
        if end_ampm == 'PM' and end_hour < 12:
            end_hour += 12
        elif end_ampm == 'AM' and end_hour == 12:
            end_hour = 0

        start_time = datetime(current_year, month, int(day), start_hour, int(start_min))
        end_time = datetime(current_year, month, int(day), end_hour, int(end_min))

        if end_time <= start_time:
            end_time += timedelta(days=1)

        return start_time, end_time
    except Exception as e:
        print(f"Error parsing date/time: {str(e)}")
        return None, None

def create_ics(shift_data, output_file='schedule.ics'):
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
    """Get Google Calendar API service using OAuth 2.0"""
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
            calendar_info = service.calendars().get(calendarId=calendar_id).execute()
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

def main():
    email = os.getenv("FARMBOY_EMAIL")
    password = os.getenv("FARMBOY_PASSWORD")
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID")  # Optional: specific calendar ID

    if not email or not password:
        print("Missing FARMBOY_EMAIL or FARMBOY_PASSWORD in .env file.")
        return

    driver = setup_driver()

    if login(driver, email, password):
        schedule_text, shift_data = scrape_schedule(driver)
        if schedule_text and shift_data:
            with open("schedule.txt", "w", encoding="utf-8") as f:
                f.write(schedule_text)
            print("Saved schedule text to schedule.txt")

            if create_ics(shift_data, "schedule.ics"):
                print("ICS file created successfully.")
            else:
                print("ICS creation failed.")
                
            print("\nAttempting to add events directly to Google Calendar...")
            if add_events_to_google_calendar(shift_data, calendar_id):
                print("All events added to Google Calendar.")
            else:
                print("Failed to add events to Google Calendar.")
        else:
            print("No schedule data to process.")
    else:
        print("Login failed.")

    driver.quit()

if __name__ == "__main__":
    main()
