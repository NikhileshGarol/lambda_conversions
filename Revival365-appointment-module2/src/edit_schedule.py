import datetime
from dateutil.tz import gettz
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pathlib import Path

# Google Calendar API Setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
# SERVICE_ACCOUNT_FILE = 'serviceaccount.json'  # Path to your service account JSON file
BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceaccount.json"

def authenticate_with_service_account():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service
'''
def set_availability(service, calendar_id, date, time_slots):
    ist = gettz('Asia/Kolkata')

    for slot in time_slots:
        start_time_str = f"{date} {slot.get('start')}"  # Use the 'start' field
        end_time_str = f"{date} {slot.get('end')}"  # Use the 'end' field

        if not start_time_str or not end_time_str:
            continue

        # Convert to datetime objects with IST timezone
        start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=ist)
        end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=ist)

        # Convert to UTC for Google Calendar API
        start_time_utc = start_time.astimezone(gettz('UTC'))
        end_time_utc = end_time.astimezone(gettz('UTC'))

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
            if (existing_event['start']['dateTime'] != start_time_utc.isoformat() or
                    existing_event['end']['dateTime'] != end_time_utc.isoformat()):
                service.events().delete(calendarId=calendar_id, eventId=existing_event['id']).execute()
                print(f"Old availability slot removed: {existing_event['htmlLink']}")

                # Create a new availability event for the updated time slot
                event = {
                    'summary': 'Available Slot',
                    'description': f'This time slot is available.',
                    'start': {'dateTime': start_time_utc.isoformat(), 'timeZone': 'UTC'},
                    'end': {'dateTime': end_time_utc.isoformat(), 'timeZone': 'UTC'},
                    'transparency': 'transparent',
                }
                created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
                print(f"New availability slot created: {created_event.get('htmlLink')}")
            else:
                print(f"No change in availability for {start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}")
        else:
            event = {
                'summary': 'Available Slot',
                'description': f'Available Slot.',
                'start': {'dateTime': start_time_utc.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end_time_utc.isoformat(), 'timeZone': 'UTC'},
                'transparency': 'transparent',
            }
            created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
            print(f"Availability set from {start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}: {created_event.get('htmlLink')}")
'''
def set_availability(service, calendar_id, date, time_slots):
    ist = gettz('Asia/Kolkata')

    # First, remove any existing availability events for the given date
    events_result = service.events().list(calendarId=calendar_id, timeMin=f"{date}T00:00:00+05:30",
                                          timeMax=f"{date}T23:59:59+05:30", singleEvents=True, orderBy='startTime').execute()

    for event in events_result.get('items', []):
        if event['summary'] == 'Available Slot':
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            print(f"Deleted existing availability slot: {event['htmlLink']}")

    # Now add the new slots
    for slot in time_slots:
        start_time_str = f"{date} {slot.get('start')}"  # Use the 'start' field
        end_time_str = f"{date} {slot.get('end')}"  # Use the 'end' field

        if not start_time_str or not end_time_str:
            continue

        # Convert to datetime objects with IST timezone
        start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=ist)
        end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=ist)

        # Convert to UTC for Google Calendar API
        start_time_utc = start_time.astimezone(gettz('UTC'))
        end_time_utc = end_time.astimezone(gettz('UTC'))

        # Create the new availability slot
        event = {
            'summary': 'Available Slot',
            'description': f'Available Slot.',
            'start': {'dateTime': start_time_utc.isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': end_time_utc.isoformat(), 'timeZone': 'UTC'},
            'transparency': 'transparent',
        }
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Availability set from {start_time.strftime('%I:%M %p')} to {end_time.strftime('%I:%M %p')}: {created_event.get('htmlLink')}")

'''
def set_full_day_unavailability(service, calendar_id, date):
    ist = gettz('Asia/Kolkata')

    start_time_str = f"{date} 12:00 AM"
    end_time_str = f"{date} 11:59 PM"

    start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=ist)
    end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=ist)

    start_time_utc = start_time.astimezone(gettz('UTC'))
    end_time_utc = end_time.astimezone(gettz('UTC'))

    events_result = service.events().list(calendarId=calendar_id, timeMin=start_time_utc.isoformat(),
                                          timeMax=end_time_utc.isoformat(), singleEvents=True,
                                          orderBy='startTime').execute()

    for event in events_result.get('items', []):
        if event['summary'] == 'Available Slot':
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            print(f"Deleted existing availability slot: {event['htmlLink']}")

    event = {
        'summary': 'Unavailable',
        'description': 'This day is marked as unavailable.',
        'start': {'dateTime': start_time_utc.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_time_utc.isoformat(), 'timeZone': 'UTC'},
        'transparency': 'opaque',
    }

    created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
    print(f"Marked the entire day as unavailable: {created_event.get('htmlLink')}")
'''
def set_full_day_unavailability(service, calendar_id, date):
    ist = gettz('Asia/Kolkata')

    # Define start and end times for the day in IST
    start_time_str = f"{date} 12:00 AM"
    end_time_str = f"{date} 11:59 PM"

    # Convert string to datetime and set timezone to IST
    start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=ist)
    end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%d %I:%M %p').replace(tzinfo=ist)

    # Convert IST time to UTC
    start_time_utc = start_time.astimezone(gettz('UTC'))
    end_time_utc = end_time.astimezone(gettz('UTC'))

    print(f"Start Time (UTC): {start_time_utc}, End Time (UTC): {end_time_utc}")

    # Fetch events within the specified time range
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_time_utc.isoformat(),
        timeMax=end_time_utc.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    # Debugging: Check if events were returned
    if not events_result.get('items', []):
        print(f"No events found for {date}.")
    else:
        print(f"Found {len(events_result.get('items', []))} events for {date}.")

    # Loop through the events and delete 'Unavailable' events
    for event in events_result.get('items', []):
        print(f"Checking event: {event.get('summary')} at {event.get('start').get('dateTime')}")
        if event['summary'] == 'Available Slot':  # Change condition to match the event summary
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            print(f"Deleted event: {event['htmlLink']}")

    print(f"All events for {date} have been processed.")



def edit_availability(calendar_id, availability_data):
    service = authenticate_with_service_account()

    for day in availability_data:
        date = day.get('date')
        available_slots = day.get('available_slots')

        if available_slots == [] or available_slots == "not available":
            set_full_day_unavailability(service, calendar_id, date)
        elif available_slots:
            set_availability(service, calendar_id, date, available_slots)

# Example function call
if __name__ == '__main__':
    calendar_id = "your_calendar_id@example.com"  # Replace with your calendar ID
    availability_data = [
        {
            "date": "2024-12-25",
            "available_slots": [{"start": "10:00 AM", "end": "12:00 PM"}]
        },
        {
            "date": "2024-12-26",
            "available_slots": "not available"
        }
    ]
    edit_availability(calendar_id, availability_data)
