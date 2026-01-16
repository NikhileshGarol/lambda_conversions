'''
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
from dateutil.tz import gettz
import json

# Google Calendar API setup (replace with your service account details)
SERVICE_ACCOUNT_FILE = 'serviceaccount.json'  # Path to your service account file

# Authenticate with Google Calendar API
def authenticate_google_calendar():
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']  # Adjust the scope as needed
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    service = build('calendar', 'v3', credentials=credentials)
    return service

# Get all events from the calendar
def get_all_events(service, calendar_id):
    now = datetime.utcnow().isoformat() + 'Z'  # Current time in UTC
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=2500,
        singleEvents=True,
        orderBy='startTime',
    ).execute()
    
    events = events_result.get('items', [])
    return events

# Fetch all recurring event IDs dynamically
def get_all_recurring_event_ids(events):
    recurring_event_ids = set()
    for event in events:
        recurring_event_id = event.get('recurringEventId')
        if recurring_event_id:
            recurring_event_ids.add(recurring_event_id)
    
    return list(recurring_event_ids)

# Get events by recurring event ID
def get_events_by_recurring_id(events, recurring_event_id):
    # Filter events based on recurring event ID
    recurring_events = [
        event for event in events 
        if event.get('recurringEventId') == recurring_event_id
    ]
    
    return recurring_events

# Format events into weekly availability
def format_weekly_availability(events):
    ist = gettz('Asia/Kolkata')
    
    weekly_slots = {}
    
    for event in events:
        # Strip 'Z' and parse the datetime string
        start_dt_str = event['start']['dateTime'].rstrip('Z')  # Remove 'Z' at the end
        end_dt_str = event['end']['dateTime'].rstrip('Z')  # Remove 'Z' at the end
        
        # Parse datetime string to datetime object
        start_dt = datetime.strptime(start_dt_str, '%Y-%m-%dT%H:%M:%S')
        end_dt = datetime.strptime(end_dt_str, '%Y-%m-%dT%H:%M:%S')
        
        # Localize to UTC and then convert to IST
        start_dt = start_dt.replace(tzinfo=gettz('UTC')).astimezone(ist)
        end_dt = end_dt.replace(tzinfo=gettz('UTC')).astimezone(ist)
        
        day = start_dt.strftime('%A').lower()
        slot = {
            'start': start_dt.strftime('%I:%M %p'),
            'end': end_dt.strftime('%I:%M %p')
        }
        
        # If the slot already exists for the day, don't add it again
        if day not in weekly_slots:
            weekly_slots[day] = {'day': day, 'available_slots': []}
        
        # Check for duplicate slots before adding
        if slot not in weekly_slots[day]['available_slots']:
            weekly_slots[day]['available_slots'].append(slot)
    
    availability = list(weekly_slots.values())
    return availability

# Updated function to get weekly availability for a specific calendar
def get_weekly_availability(calendar_id):
    service = authenticate_google_calendar()  # Authenticate and get service
    
    # Get all events from the calendar
    events = get_all_events(service, calendar_id)
    
    # Dynamically fetch all recurring event IDs
    recurring_event_ids = get_all_recurring_event_ids(events)
    
    # Dictionary to hold grouped availability by day
    grouped_availability = {
        "monday": [],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": []
    }
    
    if recurring_event_ids:
        for recurring_event_id in recurring_event_ids:
            # Get events based on recurring event ID
            recurring_events = get_events_by_recurring_id(events, recurring_event_id)
            
            # Format the weekly availability based on events
            availability = format_weekly_availability(recurring_events)
            
            # Merge availability into the grouped_availability by day
            for day_avail in availability:
                day = day_avail['day']
                grouped_availability[day].extend(day_avail['available_slots'])
    
    # Convert to a list of dictionaries and remove empty days
    final_availability = [
        {"day": day, "available_slots": slots if slots else []}
        for day, slots in grouped_availability.items()
    ]

    return final_availability

# Example usage
if __name__ == '__main__':
    calendar_id = 'CALENDAR_ID'  # Replace with your calendar ID
    availability = get_weekly_availability(calendar_id)
    
    # Print the grouped availability as JSON
    print(json.dumps(availability, indent=2))
'''

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
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

# Get all events from the calendar
def get_all_events(service, calendar_id):
    now = datetime.utcnow().isoformat() + 'Z'  # Current time in UTC
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=2500,
        singleEvents=True,
        orderBy='startTime',
    ).execute()
    
    events = events_result.get('items', [])
    return events

# Fetch all recurring event IDs dynamically
def get_all_recurring_event_ids(events):
    recurring_event_ids = set()
    for event in events:
        recurring_event_id = event.get('recurringEventId')
        if recurring_event_id:
            recurring_event_ids.add(recurring_event_id)
    
    return list(recurring_event_ids)

# Get events by recurring event ID
def get_events_by_recurring_id(events, recurring_event_id):
    # Filter events based on recurring event ID
    recurring_events = [
        event for event in events 
        if event.get('recurringEventId') == recurring_event_id
    ]
    
    return recurring_events
'''
# Format events into weekly availability
def format_weekly_availability(events):
    ist = gettz('Asia/Kolkata')
    
    weekly_slots = {}
    
    for event in events:
        # Strip 'Z' and parse the datetime string
        start_dt_str = event['start']['dateTime'].rstrip('Z')  # Remove 'Z' at the end
        end_dt_str = event['end']['dateTime'].rstrip('Z')  # Remove 'Z' at the end
        
        # Parse datetime string to datetime object
        start_dt = datetime.fromisoformat(start_dt_str)  # Automatically handles timezone
        end_dt = datetime.fromisoformat(end_dt_str)  # Automatically handles timezone
        
        # Convert to IST
        start_dt = start_dt.astimezone(ist)
        end_dt = end_dt.astimezone(ist)

        day = start_dt.strftime('%A').lower()
        slot = {
            'start': start_dt.strftime('%I:%M %p'),
            'end': end_dt.strftime('%I:%M %p')
        }
        
        # If the slot already exists for the day, don't add it again
        if day not in weekly_slots:
            weekly_slots[day] = {'day': day, 'available_slots': []}
        
        # Check for duplicate slots before adding
        if slot not in weekly_slots[day]['available_slots']:
            weekly_slots[day]['available_slots'].append(slot)
    
    availability = list(weekly_slots.values())
    return availability

'''
def format_weekly_availability(events):
    ist = gettz('Asia/Kolkata')  # Indian Standard Time
    weekly_slots = {}

    for event in events:
        # Parse and convert times to datetime objects
        start_dt = datetime.fromisoformat(event['start']['dateTime'].rstrip('Z')).astimezone(ist)
        end_dt = datetime.fromisoformat(event['end']['dateTime'].rstrip('Z')).astimezone(ist)

        # Get the day and format the slot
        day = start_dt.strftime('%A').lower()
        slot = {
            'start': start_dt.strftime('%I:%M %p'),
            'end': end_dt.strftime('%I:%M %p')
        }

        # Initialize the day if not present
        if day not in weekly_slots:
            weekly_slots[day] = {'day': day, 'available_slots': []}
        
        # Avoid duplicates and add slot
        if slot not in weekly_slots[day]['available_slots']:
            weekly_slots[day]['available_slots'].append(slot)

    # Sort slots by time for each day
    for day in weekly_slots:
        weekly_slots[day]['available_slots'].sort(
            key=lambda slot: datetime.strptime(slot['start'], '%I:%M %p')
        )

    return list(weekly_slots.values())
'''
# New function to get the weekly availability
# Updated function to get weekly availability for a specific calendar
def get_weekly_availability(calendar_id):
    service = authenticate_google_calendar()  # Authenticate and get service
    
    # Get all events from the calendar
    events = get_all_events(service, calendar_id)
    
    # Dynamically fetch all recurring event IDs
    recurring_event_ids = get_all_recurring_event_ids(events)
    
    # Dictionary to hold grouped availability by day
    grouped_availability = {
        "monday": [],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": []
    }
    
    if recurring_event_ids:
        for recurring_event_id in recurring_event_ids:
            # Get events based on recurring event ID
            recurring_events = get_events_by_recurring_id(events, recurring_event_id)
            
            # Format the weekly availability based on events
            availability = format_weekly_availability(recurring_events)
            
            # Merge availability into the grouped_availability by day
            for day_avail in availability:
                day = day_avail['day']
                grouped_availability[day].extend(day_avail['available_slots'])
    
    # Convert to a list of dictionaries and remove empty days
    final_availability = [
        {"day": day, "available_slots": slots if slots else []}
        for day, slots in grouped_availability.items()
    ]

    return final_availability

'''

def get_weekly_availability(calendar_id):
    service = authenticate_google_calendar()  # Authenticate and get service
    
    # Get all events from the calendar
    events = get_all_events(service, calendar_id)
    
    # Dynamically fetch all recurring event IDs
    recurring_event_ids = get_all_recurring_event_ids(events)
    
    # Dictionary to hold grouped availability by day
    grouped_availability = {
        "monday": [],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": []
    }

    if recurring_event_ids:
        for recurring_event_id in recurring_event_ids:
            # Get events based on recurring event ID
            recurring_events = get_events_by_recurring_id(events, recurring_event_id)
            
            # Format the weekly availability based on events
            availability = format_weekly_availability(recurring_events)
            
            # Merge availability into the grouped_availability by day
            for day_avail in availability:
                day = day_avail['day']
                grouped_availability[day].extend(day_avail['available_slots'])
    
    # Sort and consolidate slots for each day
    final_availability = []
    for day, slots in grouped_availability.items():
        # Remove duplicates and sort slots
        unique_sorted_slots = sorted(
            {tuple(slot.items()) for slot in slots},
            key=lambda slot: datetime.strptime(dict(slot)['start'], '%I:%M %p')
        )
        # Append to final availability
        final_availability.append({
            "day": day,
            "available_slots": [dict(slot) for slot in unique_sorted_slots]
        })

    return final_availability

# Example usage
if __name__ == '__main__':
    calendar_id = '0e50291240ce2feebec0676e3e21fa78b8633db289ea2ec02d51ee36ca8cb7e8@group.calendar.google.com'  # Replace or pass as argument
    availability = get_weekly_availability(calendar_id)
    
    # Print the grouped availability as JSON
    print(json.dumps(availability, indent=2))
