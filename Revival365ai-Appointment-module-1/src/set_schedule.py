import json
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from datetime import datetime, timedelta
from collections import defaultdict
from dateutil.tz import gettz
from appointment_config import service  # Importing the 'service' object from config.py


# Define Indian Standard Time (IST)
IST = gettz('Asia/Kolkata')


def set_availability(calendar_id, date, time_slots):
    ist = gettz('Asia/Kolkata')

    for slot in time_slots:
        start_time_str = f"{date} {slot.get('start')}"  # Use the 'start' field
        end_time_str = f"{date} {slot.get('end')}"      # Use the 'end' field
        duration = slot.get('duration')  # Get the duration

        if not start_time_str or not end_time_str or not duration:
            continue


        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %I:%M %p')
        end_time = datetime.strptime(end_time_str, '%Y-%m-%d %I:%M %p')


        # Convert to datetime objects with IST timezone
        start_time = start_time.replace(tzinfo=IST)
        end_time = end_time.replace(tzinfo=IST)

        # Loop to create or update time slots in intervals (e.g., 30 minutes)
        current_start_time = start_time
        while current_start_time < end_time:
            current_end_time = current_start_time + timedelta(minutes=duration)

            # Convert to UTC for Google Calendar API
            start_time_utc = current_start_time.astimezone(gettz('UTC'))
            end_time_utc = current_end_time.astimezone(gettz('UTC'))

            # Check if an availability event already exists
            events_result = service.events().list(calendarId=calendar_id, timeMin=start_time_utc.isoformat(),
                                                  timeMax=end_time_utc.isoformat(), singleEvents=True,
                                                  orderBy='startTime').execute()

            existing_event = None
            for event in events_result.get('items', []):
                if event['summary'] == 'Available Slot' and 'start' in event and 'end' in event:
                    existing_event = event
                    break

            if existing_event:
                # If the event times are different (e.g., changing from 9:00 AM - 12:00 PM to 11:00 AM - 12:00 PM)
                if existing_event['start']['dateTime'] != start_time_utc.isoformat() or existing_event['end']['dateTime'] != end_time_utc.isoformat():
                    # Delete the existing event
                    service.events().delete(calendarId=calendar_id, eventId=existing_event['id']).execute()
                    print(f"Old availability slot removed: {existing_event['htmlLink']}")

                    # Create a new availability event for the updated time slot
                    event = {
                        'summary': 'Available Slot',
                        'description': f'This time slot is available for {duration} minutes.',
                        'start': {'dateTime': start_time_utc.isoformat(), 'timeZone': 'UTC'},
                        'end': {'dateTime': end_time_utc.isoformat(), 'timeZone': 'UTC'},
                        'transparency': 'transparent',
                    }

                    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
                    print(f"New availability slot created: {created_event.get('htmlLink')}")
                else:
                    print(f"No change in availability for {current_start_time.strftime('%I:%M %p')} to {current_end_time.strftime('%I:%M %p')}")
            else:
                # Create a new availability event if no event exists
                event = {
                    'summary': 'Available Slot',
                    'description': f'This time slot is available for {duration} minutes.',
                    'start': {'dateTime': start_time_utc.isoformat(), 'timeZone': 'UTC'},
                    'end': {'dateTime': end_time_utc.isoformat(), 'timeZone': 'UTC'},
                    'transparency': 'transparent',  # Marks the slot as available (free)
                }

                created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
                print(f"Availability set from {current_start_time.strftime('%I:%M %p')} to {current_end_time.strftime('%I:%M %p')} ({duration} minutes): {created_event.get('htmlLink')}")

            # Move to the next slot
            current_start_time = current_end_time

def set_full_day_unavailability(calendar_id, date):
    # Define the timezone for IST (Indian Standard Time)
    ist = gettz('Asia/Kolkata')
    
    # Define the start and end times for the full day
    start_time_str = f"{date} 12:00 AM"  # Corrected start time
    end_time_str = f"{date} 11:59 PM"


    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %I:%M %p')
    end_time = datetime.strptime(end_time_str, '%Y-%m-%d %I:%M %p')

    # Convert the start and end times to datetime objects
    start_time = start_time.replace(tzinfo=IST)
    end_time = end_time.replace(tzinfo=IST)

    # Convert the start and end times to UTC for Google Calendar API compatibility
    start_time_utc = current_start_time.astimezone(gettz('UTC'))
    end_time_utc = current_end_time.astimezone(gettz('UTC'))


    # Fetch all events for the entire day (start_time_utc to end_time_utc)
    events_result = service.events().list(calendarId=calendar_id, timeMin=start_time_utc.isoformat(),
                                          timeMax=end_time_utc.isoformat(), singleEvents=True,
                                          orderBy='startTime').execute()

    # Loop through all events and delete any existing 'Available Slot' events
    for event in events_result.get('items', []):
        if event['summary'] == 'Available Slot':
            # Delete the existing availability event
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            print(f"Deleted existing availability slot: {event['htmlLink']}")

    # Create a new event to mark the entire day as unavailable
    event = {
        'summary': 'Unavailable',
        'description': 'This day is marked as unavailable.',
        'start': {'dateTime': start_time_utc.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_time_utc.isoformat(), 'timeZone': 'UTC'},
        'transparency': 'opaque',  # The day will be considered unavailable
    }

    # Insert the new unavailability event for the entire day
    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    print(f"Marked the entire day as unavailable: {created_event.get('htmlLink')}")
