"""
Main module for the Farm Boy Schedule Scraper.
"""

import os
from dotenv import load_dotenv
import sys

from src.utils.browser import setup_driver
from src.services.farmboy_service import login, scrape_schedule
from src.services.calendar_service import create_ics, add_events_to_google_calendar

def main():
    """
    Main function to run the Farm Boy Schedule Scraper.
    """
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    email = os.getenv("FARMBOY_EMAIL")
    password = os.getenv("FARMBOY_PASSWORD")
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID")  # Optional: specific calendar ID

    if not email or not password:
        print("Missing FARMBOY_EMAIL or FARMBOY_PASSWORD in .env file.")
        return

    # Set up the browser driver
    driver = setup_driver()

    try:
        # Log in to Farm Boy
        if login(driver, email, password):
            # Scrape the schedule
            schedule_text, shift_data = scrape_schedule(driver)
            
            if schedule_text and shift_data:
                # Save schedule as text
                with open("schedule.txt", "w", encoding="utf-8") as f:
                    f.write(schedule_text)
                print("Saved schedule text to schedule.txt")

                # Create ICS file
                if create_ics(shift_data, "schedule.ics"):
                    print("ICS file created successfully.")
                else:
                    print("ICS creation failed.")
                    
                # Add events to Google Calendar
                print("\nAttempting to add events directly to Google Calendar...")
                if add_events_to_google_calendar(shift_data, calendar_id):
                    print("All events added to Google Calendar.")
                else:
                    print("Failed to add events to Google Calendar.")
            else:
                print("No schedule data to process.")
        else:
            print("Login failed.")
    finally:
        # Always close the browser
        driver.quit()

if __name__ == "__main__":
    main() 