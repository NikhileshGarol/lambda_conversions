from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil.tz import gettz
import json
from pathlib import Path

# Google Calendar API setup (replace with your service account details)
# SERVICE_ACCOUNT_FILE = 'serviceaccount.json'  # Path to your service account file
BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceaccount.json"
# Authenticate with Google Calendar API
def authenticate_google_calendar():
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']  # Adjust the scope as needed
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    service = build('calendar', 'v3', credentials=credentials)
    return service

# Get all events from the calendar for a specific date range
def get_all_events(service, calendar_id, start_date, end_date):
    # Convert datetime objects to ISO format without appending extra T00:00:00
    time_min = start_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    time_max = end_date.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
    
    
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        maxResults=2500,
        singleEvents=True,
        orderBy='startTime',
    ).execute()
    
    events = events_result.get('items', [])
    return events


'''
# Format weekly availability for a range of dates
def format_weekly_availability(events, start_date, end_date):
    ist = gettz('Asia/Kolkata')
    
    # Create a dictionary for all dates in the range
    daily_slots = {}
    current_date = start_date
    while current_date <= end_date:  # Inclusive of the end_date
        date_str = current_date.strftime('%Y-%m-%d')
        daily_slots[date_str] = {'date': date_str, 'available_slots': []}
        current_date += timedelta(days=1)
    
    for event in events:
        # Check if the event start has 'dateTime' and format it properly
        if 'dateTime' in event['start'] and 'dateTime' in event['end']:
            # Convert the start and end datetime from ISO 8601 format to datetime objects
            start_dt_str = event['start']['dateTime']
            end_dt_str = event['end']['dateTime']
            
            # Convert the event times from ISO format to datetime objects
            start_dt = datetime.strptime(start_dt_str, '%Y-%m-%dT%H:%M:%S%z')
            end_dt = datetime.strptime(end_dt_str, '%Y-%m-%dT%H:%M:%S%z')
            
            # Convert the event times to IST
            start_dt = start_dt.astimezone(ist)
            end_dt = end_dt.astimezone(ist)

            # Format the date
            date = start_dt.strftime('%Y-%m-%d')

            # Only add events that fall within the start_date and end_date range
            if start_dt.date() >= start_date.date() and start_dt.date() <= end_date.date():
                slot = {
                    'start': start_dt.strftime('%I:%M %p'),
                    'end': end_dt.strftime('%I:%M %p')
                }
                
                # Add the slot to the appropriate date
                if date in daily_slots and slot not in daily_slots[date]['available_slots']:
                    daily_slots[date]['available_slots'].append(slot)
    
    # Return the availability for the range, even if empty
    availability = list(daily_slots.values())
    
    # Ensure dates with no slots are shown with an empty list of available slots
    for day in availability:
        if not day['available_slots']:
            day['available_slots'] = []

    return {'availability': availability}
'''

# Filter events with 'transparency' field set to 'transparent'
def format_weekly_availability(events, start_date, end_date):
    ist = gettz('Asia/Kolkata')
    
    # Create a dictionary for all dates in the range
    daily_slots = {}
    current_date = start_date
    while current_date <= end_date:  # Inclusive of the end_date
        date_str = current_date.strftime('%Y-%m-%d')
        daily_slots[date_str] = {'date': date_str, 'available_slots': []}
        current_date += timedelta(days=1)
    
    for event in events:
        # Only process events with transparency set to 'transparent'
        if event.get('transparency') == 'transparent':
            # Check if the event start has 'dateTime' and format it properly
            if 'dateTime' in event['start'] and 'dateTime' in event['end']:
                # Convert the start and end datetime from ISO 8601 format to datetime objects
                start_dt_str = event['start']['dateTime']
                end_dt_str = event['end']['dateTime']
                
                # Convert the event times from ISO format to datetime objects
                start_dt = datetime.strptime(start_dt_str, '%Y-%m-%dT%H:%M:%S%z')
                end_dt = datetime.strptime(end_dt_str, '%Y-%m-%dT%H:%M:%S%z')
                
                # Convert the event times to IST
                start_dt = start_dt.astimezone(ist)
                end_dt = end_dt.astimezone(ist)

                # Format the date
                date = start_dt.strftime('%Y-%m-%d')

                # Only add events that fall within the start_date and end_date range
                if start_dt.date() >= start_date.date() and start_dt.date() <= end_date.date():
                    slot = {
                        'start': start_dt.strftime('%I:%M %p'),
                        'end': end_dt.strftime('%I:%M %p')
                    }
                    
                    # Add the slot to the appropriate date
                    if date in daily_slots and slot not in daily_slots[date]['available_slots']:
                        daily_slots[date]['available_slots'].append(slot)
    
    # Return the availability for the range, even if empty
    availability = list(daily_slots.values())
    
    # Ensure dates with no slots are shown with an empty list of available slots
    for day in availability:
        if not day['available_slots']:
            day['available_slots'] = []

    return {'availability': availability}



# New function to get the calendar availability
def get_calendar_availability(calendar_id, start_date, end_date):
    service = authenticate_google_calendar()  # Authenticate and get service
    
    # Get all events from the calendar within the specified date range
    events = get_all_events(service, calendar_id, start_date, end_date)
    
    # Format the weekly availability based on all recurring events
    availability = format_weekly_availability(events, start_date, end_date)
    
    return availability


if __name__ == '__main__':
    # Define your calendar ID and start/end dates from query parameters
    calendar_id = 'a604e4e96fd83379f517a11211e6db649994e9fb3a24bccc673abb02cf4afd15@group.calendar.google.com'
    start_date_str = "2024-12-23"  # Example start date from query params
    end_date_str = "2024-12-28"    # Example end date from query params
    
    # Convert the string dates to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Get the availability by calling the function with the calendar ID
    availability = get_calendar_availability(calendar_id, start_date, end_date)
    
    # Print the availability as JSON
    print(json.dumps(availability, indent=2))
