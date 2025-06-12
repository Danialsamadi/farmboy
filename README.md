# Farm Boy Schedule Scraper

This script automates the process of scraping your work schedule from MyFarmBoy and adding it to your Google Calendar.

## Project Structure

The project has been organized into a modular structure:

```
farmboy/
├── main.py                  # Main entry point
├── setup_google_calendar.py # Google Calendar setup utility
├── requirements.txt         # Python dependencies
├── .env.sample              # Sample environment variables
├── credentials.json.sample  # Sample Google API credentials
└── src/                     # Source code package
    ├── main.py              # Main application logic
    ├── utils/               # Utility modules
    │   ├── browser.py       # Browser setup utilities
    │   └── date_parser.py   # Date parsing utilities
    └── services/            # Service modules
        ├── farmboy_service.py  # Farm Boy login and scraping
        └── calendar_service.py # Calendar operations
```

## Setup Instructions

### 1. Install Required Packages

```bash
pip3 install -r requirements.txt
```

### 2. Create a .env File

Create a file named `.env` in the same directory as the script with the following content:

```
FARMBOY_EMAIL=your_farmboy_email@example.com
FARMBOY_PASSWORD=your_farmboy_password
GOOGLE_CALENDAR_ID=optional_specific_calendar_id
```

### 3. Set Up Google Calendar API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Calendar API for your project:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API" and enable it
4. Configure the OAuth consent screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" user type
   - Fill in the required fields (App name, User support email, Developer contact information)
   - For scopes, add the Google Calendar API with read/write access
   - Save and continue
5. **IMPORTANT: Add yourself as a test user**
   - On the OAuth consent screen page, scroll down to "Test users"
   - Click "Add users"
   - Add your Google email address
   - Save changes
6. Create OAuth credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Name your OAuth client (e.g., "Farm Boy Schedule")
   - Click "Create"
7. Download the credentials JSON file
8. Rename the downloaded file to `credentials.json` and place it in the same directory as the script

### 4. Safari WebDriver Setup

1. Open Safari
2. Go to Safari > Settings > Advanced
3. Check "Show Develop menu in menu bar"
4. Go to Develop > Allow Remote Automation

## Usage

### 1. Set Up Google Calendar Connection

First, run the setup script to configure Google Calendar access:

```bash
python3 setup_google_calendar.py
```

**When prompted to log in:**
- You'll see a warning screen saying "Google hasn't verified this app"
- Click "Continue" or "Advanced" and then "Go to [your project name] (unsafe)"
- This is normal for personal projects that haven't gone through Google's verification process
- Since you added yourself as a test user, you can proceed safely

### 2. Run the Schedule Scraper

After setting up the Google Calendar connection, run the main script:

```bash
python3 main.py
```

The script will:
1. Log into your MyFarmBoy account
2. Scrape your work schedule
3. Save it as a text file (`schedule.txt`)
4. Create an ICS calendar file (`schedule.ics`)
5. Add your shifts directly to your Google Calendar

## Features

- Scrapes your Farm Boy work schedule
- Saves the schedule as a text file
- Creates an ICS calendar file that can be imported into any calendar app
- Directly adds shifts to your Google Calendar
- Adds reminders 30 minutes before each shift

## Troubleshooting

### Google Calendar Access Issues

If you encounter errors like "Error 403: access_denied":
1. Make sure you've added your email as a test user in the Google Cloud Console
2. Delete the `token.pickle` file if it exists and run the setup script again
3. When authenticating, click "Continue" or "Advanced" > "Go to [project] (unsafe)"

### Authentication Errors

If you see "Error 401: deleted_client":
1. Your OAuth client may have been deleted or is invalid
2. Create a new OAuth client in the Google Cloud Console
3. Download the new credentials and replace your existing `credentials.json` file
4. Delete the `token.pickle` file and run the setup script again

### Safari WebDriver Issues

If you have problems with Safari automation:
1. Make sure you have "Allow Remote Automation" enabled in Safari's Develop menu
2. Restart Safari and try again

### General Issues

- Make sure your `.env` file contains the correct Farm Boy login credentials
- Ensure all required packages are installed
- Check that your `credentials.json` file is in the correct format and location 