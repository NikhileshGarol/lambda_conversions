'''
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime
from dateutil.tz import gettz
from googleapiclient.http import BatchHttpRequest
from config import service  # Importing the 'service' object from config.py
from zoneinfo import ZoneInfo  # Use zoneinfo for timezone

# Google Calendar API Setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'serviceaccount.json'  # Path to your service account JSON file

# Mapping of days to Google Calendar API format (SU, MO, TU, WE, TH, FR, SA)
days_mapping = {
    'sunday': 'SU',
    'monday': 'MO',
    'tuesday': 'TU',
    'wednesday': 'WE',
    'thursday': 'TH',
    'friday': 'FR',
    'saturday': 'SA'
}

# Authenticate using the service account
def authenticate_with_service_account():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_next_occurrence(current_date, target_day_code, start_time_str):
    # Days mapping to indices (SU=0, MO=1, TU=2, WE=3, TH=4, FR=5, SA=6)
    days_mapping = {
        'sunday': 'SU',
        'monday': 'MO',
        'tuesday': 'TU',
        'wednesday': 'WE',
        'thursday': 'TH',
        'friday': 'FR',
        'saturday': 'SA'
    }
    
    # Map target day code to its index
    day_indices = list(days_mapping.values())
    target_day_index = day_indices.index(target_day_code)

    # Adjust current day index to match Google Calendar (SU=0 format)
    ist = gettz('Asia/Kolkata')
    current_date = datetime.datetime.utcnow().astimezone(ist)  # Ensure current_date is in IST
    current_day_index = (current_date.weekday() + 1) % 7  # Convert Python weekday (Mon=0) to SU=0 format

    # Parse today's start time in IST
    today_start_time = datetime.datetime.strptime(
        f"{current_date.year}-{current_date.month}-{current_date.day} {start_time_str}",
        "%Y-%m-%d %I:%M %p"
    ).replace(tzinfo=ist)


    # Debug: Print details for verification
    print(f"DEBUG: Current day index: {current_day_index}, Target day index: {target_day_index}")
    print(f"DEBUG: Current date/time: {current_date}, Today start time: {today_start_time}")

    # Case 1: If today is the target day and the time is before the start time
    if current_day_index == target_day_index and current_date < today_start_time:
        print(f"DEBUG: Scheduling for today: {today_start_time}")
        return today_start_time

    # Case 2: If today is the target day but the current time has passed, schedule for next week
    if current_day_index == target_day_index and current_date >= today_start_time:
        print(f"DEBUG: Scheduling for next week: {today_start_time + datetime.timedelta(weeks=1)}")
        return today_start_time + datetime.timedelta(weeks=1)

    # Case 3: If today is not the target day, calculate days ahead
    days_ahead = (target_day_index - current_day_index + 7) % 7
    if days_ahead == 0:
        days_ahead = 7  # Ensure next occurrence is next week if today has passed

    # Calculate the next occurrence date and time
    next_occurrence_date = current_date + datetime.timedelta(days=days_ahead)
    next_occurrence_time = datetime.datetime.strptime(
         f"{next_occurrence_date.year}-{next_occurrence_date.month}-{next_occurrence_date.day} {start_time_str}",
         "%Y-%m-%d %I:%M %p"
         
    ).replace(tzinfo=ist)
    
    # Debug: Print next occurrence
    print(f"DEBUG: Next occurrence time: {next_occurrence_time}")

    return next_occurrence_time

def delete_existing_recurring_event(service, calendar_id, day_code, start_time_str):
    """
    Delete an existing recurring event for the given day and start time.
    """
    try:
        # Query parameters to search for recurring events
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId=calendar_id,
            q='Available Slot',
            timeMin=now,
            singleEvents=False
        ).execute()

        events = events_result.get('items', [])

        for event in events:
            # Check if the recurrence rule matches the desired day code
            recurrence = event.get('recurrence', [])
            if recurrence:
                for rrule in recurrence:
                    if f"BYDAY={day_code}" in rrule:
                        # Check if the event start time matches the desired start time
                        event_start_time = event['start']['dateTime']
                        event_start_time_obj = datetime.datetime.fromisoformat(event_start_time[:-1]).astimezone(utc)

                        target_time = datetime.datetime.strptime(start_time_str, "%I:%M %p").time()
                        if event_start_time_obj.time() == target_time:
                            # Delete the event
                            event_id = event['id']
                            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
                            print(f"DEBUG: Existing event deleted: {event_id}")
                            return

        print("DEBUG: No existing recurring event found to delete.")
    except Exception as e:
        print(f"ERROR: Error deleting existing event: {str(e)}")

def update_recurring_event(service, calendar_id, event_id, recurrence_id, new_start_time_str, new_end_time_str):
    """
    Update an existing recurring event based on the recurrence ID.
    """
    ist = gettz('Asia/Kolkata')

    # Get the current date and time in IST
    current_date = datetime.datetime.now(ist)

    # Calculate the new start and end times based on the provided times
    new_start_time_ist = datetime.datetime.strptime(
        f"{current_date.year}-{current_date.month}-{current_date.day} {new_start_time_str}",
        "%Y-%m-%d %I:%M %p"
    ).replace(tzinfo=ist)

    new_end_time_ist = datetime.datetime.strptime(
        f"{current_date.year}-{current_date.month}-{current_date.day} {new_end_time_str}",
        "%Y-%m-%d %I:%M %p"
    
    ).replace(tzinfo=ist)

    # Convert to UTC for Google Calendar
    new_start_time_utc = new_start_time_ist.astimezone(utc)
    new_end_time_utc = new_end_time_ist.astimezone(utc)

    # Calculate the date 1 month from the start date
    end_date = new_start_time_utc + datetime.timedelta(weeks=4)  # 1 month is approximately 4 weeks

    # Create the recurrence rule for weekly availability with 1 month duration
    rrule = f"RRULE:FREQ=WEEKLY;BYDAY={recurrence_id};UNTIL={end_date.strftime('%Y%m%dT%H%M%SZ')}"

    event_body = {
        'summary': 'Available Slot',
        'description': 'Available Slot.',
        'start': {
            'dateTime': new_start_time_utc.isoformat(),
            'timeZone': 'UTC'
        },
        'end': {
            'dateTime': new_end_time_utc.isoformat(),
            'timeZone': 'UTC'
        },
        'recurrence': [rrule],
        'transparency': 'transparent'
    }

    try:
        # Update the existing recurring event
        updated_event = service.events().update(calendarId=calendar_id, eventId=event_id, body=event_body).execute()
        print(f"DEBUG: Recurring availability slot updated: {updated_event.get('htmlLink')}")

        # Print the recurringEventId if it exists
        if 'recurringEventId' in updated_event:
            print(f"Recurring Event ID: {updated_event['recurringEventId']}")
        else:
            print("This is not part of a recurring event.")
    except Exception as e:
        print(f"ERROR: Error updating recurring event: {str(e)}")
        raise    
def find_existing_recurring_event(service, calendar_id, day_code, start_time_str):
    """
    Search for an existing recurring event based on the day code and start time.
    """
    try:
        # Query parameters to search for recurring events
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId=calendar_id,
            q='Available Slot',
            timeMin=now,
            singleEvents=False
        ).execute()

        events = events_result.get('items', [])

        for event in events:
            # Check if the recurrence rule matches the desired day code
            recurrence = event.get('recurrence', [])
            if recurrence:
                for rrule in recurrence:
                    if f"BYDAY={day_code}" in rrule:
                        # Check if the event start time matches the desired start time
                        event_start_time = event['start']['dateTime']
                        event_start_time_obj = datetime.datetime.fromisoformat(event_start_time[:-1]).astimezone(utc)

                        target_time = datetime.datetime.strptime(start_time_str, "%I:%M %p").time()
                        if event_start_time_obj.time() == target_time:
                            return event

        return None
    except Exception as e:
        print(f"ERROR: Error finding existing event: {str(e)}")
        return None

def set_recurring_availability(service, calendar_id, day_code, start_time_str, end_time_str):
    ist = gettz('Asia/Kolkata')

    # Get the current date and time in IST
    current_date = datetime.datetime.now(ist)

    # Get the next occurrence of the target day with the specified start time
    next_occurrence_ist = get_next_occurrence(current_date, day_code, start_time_str)

    # Parse the end time based on the next occurrence
    end_time_ist = datetime.datetime.strptime(
        f"{next_occurrence_ist.year}-{next_occurrence_ist.month}-{next_occurrence_ist.day} {end_time_str}",
        "%Y-%m-%d %I:%M %p"
    
    ).replace(tzinfo=ist)

    # Convert to UTC for Google Calendar
    start_time_utc = next_occurrence_ist.astimezone(ZoneInfo("UTC"))
    end_time_utc = end_time_ist.astimezone(ZoneInfo("UTC"))

    # Calculate the date 1 month from the start date
    end_date = start_time_utc + datetime.timedelta(weeks=4)  # 1 month is approximately 4 weeks

    # Create the recurrence rule for weekly availability with 1 month duration
    rrule = f"RRULE:FREQ=WEEKLY;BYDAY={day_code};UNTIL={end_date.strftime('%Y%m%dT%H%M%SZ')}"

    # Delete any existing recurring event for the same day and time
    delete_existing_recurring_event(service, calendar_id, day_code, start_time_str)

    # Create a new recurring event with the updated time slot
    event_body = {
        'summary': 'Available Slot',
        'description': 'Available Slot.',
        'start': {
            'dateTime': start_time_utc.isoformat(),
            'timeZone': 'UTC'
        },
        'end': {
            'dateTime': end_time_utc.isoformat(),
            'timeZone': 'UTC'
        },
        'recurrence': [rrule],
        'transparency': 'transparent'
    }

    try:
        # Insert the new event
        created_event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        print(f"DEBUG: Recurring availability slot created: {created_event.get('htmlLink')}")

        # Print the recurringEventId if it exists
        if 'recurringEventId' in created_event:
            print(f"Recurring Event ID: {created_event['recurringEventId']}")
        else:
            print("This is not part of a recurring event.")

    except Exception as e:
        print(f"ERROR: Error creating recurring event: {str(e)}")
        raise

def handle_set_global_availability(calendar_id, availability_data):
    """
    Handle setting global availability, checking if an event already exists and updating it if needed.
    """
    for day_data in availability_data:
        day = day_data.get('day').lower()  # Convert to lowercase
        if day not in days_mapping:
            continue  # Skip if day is not valid (like if it's misspelled)

        day_code = days_mapping[day]  # Get the Google Calendar code for the day
        available_slots = day_data.get('available_slots')

        for slot in available_slots:
            start_time_str = slot.get('start')
            end_time_str = slot.get('end')

            # Check if there's an existing recurring event
            existing_event = find_existing_recurring_event(service, calendar_id, day_code, start_time_str)

            if existing_event:
                # If an event exists, update it with the new details
                print(f"DEBUG: Found existing event for {day_code} at {start_time_str}, updating it.")
                recurrence_id = existing_event.get('recurrenceId', None)
                if recurrence_id:
                    # If recurrenceId is found, update the event
                    update_recurring_event(service, calendar_id, existing_event['id'], recurrence_id, start_time_str, end_time_str)
                else:
                    print(f"DEBUG: Recurrence ID not found, creating a new recurring event.")
                    set_recurring_availability(service, calendar_id, day_code, start_time_str, end_time_str)
            else:
                # If no existing event, create a new one
                print(f"DEBUG: No existing event found for {day_code} at {start_time_str}, creating a new recurring event.")
                set_recurring_availability(service, calendar_id, day_code, start_time_str, end_time_str)


if __name__ == '__main__':
    # Example data for global availability
    calendar_id = "69ee4105e4a2629e968cd45b08209dd29eb348df3148eb2b6da191f01cf542b5@group.calendar.google.com"
    availability_data = [
        {
            'day': 'Monday',
            'available_slots': [
                {'start': '10:00 AM', 'end': '11:00 AM'},
                {'start': '02:00 PM', 'end': '03:00 PM'}
            ]
        },
        {
            'day': 'Wednesday',
            'available_slots': [
                {'start': '10:00 AM', 'end': '11:00 AM'}
            ]
        }
    ]

    # Authenticate and set global availability
    service = authenticate_with_service_account()
    handle_set_global_availability(service, calendar_id, availability_data)
'''
import random
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime
from dateutil.tz import gettz
from appointment2_config import service  # Importing the 'service' object from config.py
from zoneinfo import ZoneInfo  # Use zoneinfo for timezone
from dateutil.parser import parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time
from threading import Lock
from pathlib import Path

# Adding a lock for thread safety if needed
lock = Lock()
# Google Calendar API Setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
# SERVICE_ACCOUNT_FILE = 'serviceaccount.json'  # Path to your service account JSON file
BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceaccount.json"

def create_service():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('calendar', 'v3', credentials=creds)

# Mapping of days to Google Calendar API format (SU, MO, TU, WE, TH, FR, SA)
days_mapping = {
    'sunday': 'SU',
    'monday': 'MO',
    'tuesday': 'TU',
    'wednesday': 'WE',
    'thursday': 'TH',
    'friday': 'FR',
    'saturday': 'SA'
}


def api_with_retries(api_call, retries=3, base_delay=1):
    for attempt in range(retries):
        try:
            return api_call.execute()
        except Exception as e:
            if "rateLimitExceeded" in str(e) or "userRateLimitExceeded" in str(e):
                if attempt < retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                    print(f"Rate limit exceeded, retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    raise e
            else:
                raise e


# Authenticate using the service account
def authenticate_with_service_account():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service
# Get all events from the calendar
def get_all_events(service, calendar_id):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=2500,
        singleEvents=True,
        orderBy='startTime',
    ).execute()
    
    events = events_result.get('items', [])
    return events

def get_recurring_event_ids_with_day(events, availability_data):
    recurring_event_ids_with_day = []

    def process_event_for_availability(event, availability):
        recurring_event_id = event.get('recurringEventId')
        start_time = event.get('start', {}).get('dateTime') or event.get('start', {}).get('date')
        if recurring_event_id and start_time:
            day_of_week = parse(start_time).strftime('%A')  # Get the day of the week
            if availability['day'].lower() == day_of_week.lower():
                return {
                    'recurring_event_id': recurring_event_id,
                    'day_of_week': day_of_week
                }
        return None

    with ThreadPoolExecutor() as executor:
        futures = []
        for event in events:
            # Submit each event-availability check to the executor
            for availability in availability_data:
                futures.append(executor.submit(process_event_for_availability, event, availability))

        for future in as_completed(futures):
            result = future.result()
            if result:  # Only append non-None results
                recurring_event_ids_with_day.append(result)

    return recurring_event_ids_with_day

def delete_recurring_events(service, calendar_id, recurring_event_ids_with_day):
    # Deduplicate based on recurring_event_id
    unique_events = {}
    for item in recurring_event_ids_with_day:
        recurring_event_id = item['recurring_event_id']
        if recurring_event_id not in unique_events:
            unique_events[recurring_event_id] = item['day_of_week']

    def delete_event(recurring_event_id, day_of_week):
        # Create a new service instance per thread
        thread_service = create_service()
        try:
            thread_service.events().delete(calendarId=calendar_id, eventId=recurring_event_id).execute()
            return f"Deleted recurring event ID: {recurring_event_id} (Day: {day_of_week})"
        except Exception as e:
            return f"Failed to delete recurring event ID {recurring_event_id}: {e}"

    # Using ThreadPoolExecutor for concurrent deletion
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_event = {
            executor.submit(delete_event, recurring_event_id, day_of_week): recurring_event_id
            for recurring_event_id, day_of_week in unique_events.items()
        }
        for future in as_completed(future_to_event):
            result = future.result()
            print(result)


def get_next_occurrence(current_date, target_day_code, start_time_str):
    # Days mapping to indices (SU=0, MO=1, TU=2, WE=3, TH=4, FR=5, SA=6)
    days_mapping = {
        'sunday': 'SU',
        'monday': 'MO',
        'tuesday': 'TU',
        'wednesday': 'WE',
        'thursday': 'TH',
        'friday': 'FR',
        'saturday': 'SA'
    }
    
    # Map target day code to its index
    day_indices = list(days_mapping.values())
    target_day_index = day_indices.index(target_day_code)

    # Adjust current day index to match Google Calendar (SU=0 format)
    ist = gettz('Asia/Kolkata')
    current_date = datetime.datetime.utcnow().astimezone(ist)  # Ensure current_date is in IST
    current_day_index = (current_date.weekday() + 1) % 7  # Convert Python weekday (Mon=0) to SU=0 format

    # Parse today's start time in IST
    today_start_time = datetime.datetime.strptime(
        f"{current_date.year}-{current_date.month}-{current_date.day} {start_time_str}",
        "%Y-%m-%d %I:%M %p"
    ).replace(tzinfo=ist)


    # Debug: Print details for verification
    print(f"DEBUG: Current day index: {current_day_index}, Target day index: {target_day_index}")
    print(f"DEBUG: Current date/time: {current_date}, Today start time: {today_start_time}")
    
    '''
    # Case 1: If today is the target day and the time is before the start time
    if current_day_index == target_day_index and current_date < today_start_time:
        print(f"DEBUG: Scheduling for today: {today_start_time}")
        return today_start_time
    '''
    # Case 1: If today is the target day, schedule for today
    if current_day_index == target_day_index:
        print(f"DEBUG: Scheduling for today without start time validation.")
        return current_date.replace(hour=today_start_time.hour, minute=today_start_time.minute, second=0, microsecond=0)


    # Case 2: If today is the target day but the current time has passed, schedule for next week
    if current_day_index == target_day_index and current_date >= today_start_time:
        print(f"DEBUG: Scheduling for next week: {today_start_time + datetime.timedelta(weeks=1)}")
        return today_start_time + datetime.timedelta(weeks=1)

    # Case 3: If today is not the target day, calculate days ahead
    days_ahead = (target_day_index - current_day_index + 7) % 7
    if days_ahead == 0:
        days_ahead = 7  # Ensure next occurrence is next week if today has passed

    # Calculate the next occurrence date and time
    next_occurrence_date = current_date + datetime.timedelta(days=days_ahead)
    next_occurrence_time = datetime.datetime.strptime(
         f"{next_occurrence_date.year}-{next_occurrence_date.month}-{next_occurrence_date.day} {start_time_str}",
         "%Y-%m-%d %I:%M %p"
         
    ).replace(tzinfo=ist)
    
    # Debug: Print next occurrence
    print(f"DEBUG: Next occurrence time: {next_occurrence_time}")

    return next_occurrence_time
  
def set_recurring_availability(service, calendar_id, day_code, start_time_str, end_time_str):
    ist = gettz('Asia/Kolkata')

    # Get the current date and time in IST
    current_date = datetime.datetime.now(ist)

    # Get the next occurrence of the target day with the specified start time
    next_occurrence_ist = get_next_occurrence(current_date, day_code, start_time_str)

    # Parse the end time based on the next occurrence
    end_time_ist = datetime.datetime.strptime(
        f"{next_occurrence_ist.year}-{next_occurrence_ist.month}-{next_occurrence_ist.day} {end_time_str}",
        "%Y-%m-%d %I:%M %p"
    ).replace(tzinfo=ist)

    # Convert to UTC for Google Calendar
    start_time_utc = next_occurrence_ist.astimezone(ZoneInfo("UTC"))
    end_time_utc = end_time_ist.astimezone(ZoneInfo("UTC"))

    # Calculate the date 1 month from the start date
    end_date = start_time_utc + datetime.timedelta(weeks=52)  # 1 month is approximately 4 weeks

    # Create the recurrence rule for weekly availability with 1 month duration
    rrule = f"RRULE:FREQ=WEEKLY;BYDAY={day_code};UNTIL={end_date.strftime('%Y%m%dT%H%M%SZ')}"

    # Create a new recurring event with the updated time slot
    event_body = {
        'summary': 'Available Slot',
        'description': 'Available Slot.',
        'start': {
            'dateTime': start_time_utc.isoformat(),
            'timeZone': 'UTC'
        },
        'end': {
            'dateTime': end_time_utc.isoformat(),
            'timeZone': 'UTC'
        },
        'recurrence': [rrule],
        'transparency': 'transparent'
    }

    try:
        # Insert the new event
        created_event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        print(f"Recurring availability slot created: {created_event.get('htmlLink')}")
    except Exception as e:
        print(f"ERROR: Failed to create slot for {day_code} {start_time_str}-{end_time_str}: {e}")
        raise
    
    
def delete_event(event, service, calendar_id):
    event_id = event.get('id')
    
    # Extract start time (either dateTime or date)
    event_start_time = event.get('start', {}).get('dateTime', event.get('start', {}).get('date'))
    
    # Format the start time
    if event_start_time:
        try:
            event_start_time = datetime.datetime.strptime(event_start_time, '%Y-%m-%dT%H:%M:%S%z')
            formatted_start_time = event_start_time.strftime('%Y-%m-%d')
        except ValueError:
            formatted_start_time = event_start_time  # For all-day events or other formats
    else:
        formatted_start_time = "N/A"  # If no start time available
    
    try:
        # Delete the event
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        # Print and return the deletion message with the start date
        print(f"Event deleted: {event.get('htmlLink')} (Start date: {formatted_start_time})")
        return f"Event deleted: {event.get('htmlLink')} (Start date: {formatted_start_time})"
    except Exception as e:
        print(f"Failed to delete event {event_id}: {e}")
        return f"Failed to delete event {event_id}: {e}"

def delete_specific_events_with_threads(service, calendar_id, summary, description, transparency, max_workers=5):
    now = datetime.datetime.utcnow().isoformat() + 'Z'

    # Fetch events from Google Calendar
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=2500,
        singleEvents=True,
        orderBy='startTime',
    ).execute()

    events = events_result.get('items', [])
    
    # Filter events based on summary, description, and transparency
    events_to_delete = [event for event in events if event.get('summary') == summary and 
                        event.get('description') == description and 
                        event.get('transparency') == transparency]
    
    if not events_to_delete:
        print("No events found to delete based on the provided criteria.")
        return

    def delete_event_with_new_service(event):
        # Create a new service instance per thread
        thread_service = create_service()  # Replace this with your actual `create_service` implementation
        try:
            thread_service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            return f"Deleted event ID: {event['id']}"
        except Exception as e:
            return f"Failed to delete event ID {event['id']}: {e}"

    # Using ThreadPoolExecutor for concurrent deletion
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_event = {
            executor.submit(delete_event_with_new_service, event): event
            for event in events_to_delete
        }
        
        # As events are deleted, print the result
        for future in as_completed(future_to_event):
            result = future.result()
            print(result)

    


def handle_set_global_availability(calendar_id, availability_data, max_workers=5):
    events = get_all_events(service, calendar_id)

    # Fetch recurring event IDs with the day of the week based on availability
    recurring_event_ids_with_day = get_recurring_event_ids_with_day(events, availability_data)
    delete_recurring_events(service, calendar_id, recurring_event_ids_with_day)
    
    
    
     # Set the criteria for deletion
    summary = "Available Slot"
    description = "Available Slot."
    transparency = "transparent"
    
    # Call the function to delete the events with threading
    delete_specific_events_with_threads(service, calendar_id, summary, description, transparency)
    

    def set_availability_task(day_code, start_time_str, end_time_str):
        thread_service = create_service()
        try:
            set_recurring_availability(thread_service, calendar_id, day_code, start_time_str, end_time_str)
        except Exception as e:
            print(f"ERROR: Failed to set availability for {day_code} {start_time_str}-{end_time_str}: {e}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for day_data in availability_data:
            day = day_data.get('day').lower()
            if day not in days_mapping:
                print(f"Skipping invalid day: {day}")
                continue

            day_code = days_mapping[day]
            available_slots = day_data.get('available_slots')

            for slot in available_slots:
                start_time_str = slot.get('start')
                end_time_str = slot.get('end')

                if not start_time_str or not end_time_str:
                    print(f"Skipping slot with missing time: {slot}")
                    continue

                futures.append(executor.submit(set_availability_task, day_code, start_time_str, end_time_str))

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Thread failed: {e}")
'''
if __name__ == '__main__':
    # Example data for global availability
    calendar_id = "a604e4e96fd83379f517a11211e6db649994e9fb3a24bccc673abb02cf4afd15@group.calendar.google.com"
    availability_data = [
    {
        'day': 'Monday',
        'available_slots': [
            {'start': '09:00 AM', 'end': '10:00 AM'},
            {'start': '11:30 AM', 'end': '12:30 PM'},
            {'start': '03:00 PM', 'end': '04:00 PM'}
        ]
    },
    {
        'day': 'Tuesday',
        'available_slots': [
            {'start': '09:00 AM', 'end': '10:00 AM'},
            {'start': '11:30 AM', 'end': '12:30 PM'},
            {'start': '03:00 PM', 'end': '04:00 PM'}
        ]
    },
    {
        'day': 'Wednesday',
        'available_slots': [
            {'start': '09:00 AM', 'end': '10:00 AM'},
            {'start': '11:30 AM', 'end': '12:30 PM'},
            {'start': '03:00 PM', 'end': '04:00 PM'}
        ]
    },
    {
        'day': 'Thursday',
        'available_slots': [
            {'start': '09:00 AM', 'end': '10:00 AM'},
            {'start': '11:30 AM', 'end': '12:30 PM'},
            {'start': '03:00 PM', 'end': '04:00 PM'}
        ]
    },
    {
        'day': 'Friday',
        'available_slots': [
            {'start': '09:00 AM', 'end': '10:00 AM'},
            {'start': '11:30 AM', 'end': '12:30 PM'},
            {'start': '03:00 PM', 'end': '04:00 PM'}
        ]
    },
    {
        'day': 'Saturday',
        'available_slots': [
            {'start': '10:00 AM', 'end': '11:00 AM'},
            {'start': '01:30 PM', 'end': '02:30 PM'},
            {'start': '04:00 PM', 'end': '05:00 PM'}
        ]
    },
    {
        'day': 'Sunday',
        'available_slots': [
            {'start': '11:00 AM', 'end': '12:00 PM'},
            {'start': '02:00 PM', 'end': '03:00 PM'},
            {'start': '04:30 PM', 'end': '05:30 PM'}
        ]
    }
]

    # Authenticate and set global availability
service = authenticate_with_service_account()
handle_set_global_availability(calendar_id, availability_data)
'''