"""
Date and time parsing utilities for schedule data.
"""

from datetime import datetime, timedelta
import re
import pytz

def parse_date_time(date_str, time_str, current_year=None):
    """
    Parse date and time strings from Farm Boy schedule format.
    
    Args:
        date_str (str): Date string in format "Weekday, Month Day(st/nd/rd/th)"
        time_str (str): Time string in format "H:MM AM/PM to H:MM AM/PM"
        current_year (int, optional): Year to use for the date. Defaults to current year.
        
    Returns:
        tuple: (start_datetime, end_datetime) or (None, None) if parsing fails
    """
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