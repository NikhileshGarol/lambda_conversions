import json
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from dateutil.tz import gettz
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceaccount.json"

def create_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,  # Replace with the path to your service account key
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    service = build('calendar', 'v3', credentials=credentials)
    return service

# Define Indian Standard Time (IST)
IST = gettz('Asia/Kolkata')

def fetch_calendars(service):
    try:
        calendar_list = service.calendarList().list(fields="items(id,summary)").execute()
        return calendar_list.get('items', [])
    except Exception as e:
        print(f"Error fetching calendars: {e}")
        return []

def fetch_events_for_calendar(service, calendar_id, time_min, time_max):
    events = []
    page_token = None
    try:
        while True:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                fields="items(id,summary,start,end,extendedProperties),nextPageToken",
                pageToken=page_token
            ).execute()

            events.extend(events_result.get('items', []))
            page_token = events_result.get('nextPageToken')

            if not page_token:
                break
        return events
    except Exception as e:
        print(f"Error fetching events for calendar '{calendar_id}': {e}")
        return []

def process_calendar_events(calendar, time_min, time_max):
    """Processes events for a specific calendar and returns them in a JSON format."""
    service = create_service()  # Create a separate service object for each thread
    calendar_id = calendar['id']
    events = fetch_events_for_calendar(service, calendar_id, time_min, time_max)

    # Collect events in the required format
    formatted_events = []
    now_ist = datetime.now(IST)  # Current time in IST (timezone-aware)

    for event in events:
        start_utc = event['start'].get('dateTime', event['start'].get('date'))
        start_time = parser.isoparse(start_utc)  # Parse start time (timezone-aware)

        # Convert start time to IST for comparison
        start_time_ist = start_time.astimezone(IST)

        # Skip events that have already started in IST
        if start_time_ist < now_ist:
            continue

        # Convert start and end times to IST and format them
        start_ist = start_time_ist.strftime('%Y-%m-%dT%H:%M:%S')
        end_utc = event['end'].get('dateTime', event['end'].get('date'))
        end_ist = parser.isoparse(end_utc).astimezone(IST)

        # Split the start and end times into date and time separately
        start_date = start_time_ist.strftime('%Y-%m-%d')
        start_time_str = start_time_ist.strftime('%I:%M %p')
        end_date = end_ist.strftime('%Y-%m-%d')
        end_time_str = end_ist.strftime('%I:%M %p')

        event_data = {
            "calendar_id": calendar_id,
            "event_id": event.get('id'),
            "start_date": start_date,
            "start_time": start_time_str,
            "end_date": end_date,
            "end_time": end_time_str,
            "summary": event.get('summary', 'No Title'),
        }

        # Access the patient_id from extendedProperties if available
        extended_properties = event.get('extendedProperties', {}).get('private', {})
        patient_id = extended_properties.get('patient_id', 'N/A')

        event_data["patient_id"] = patient_id
        formatted_events.append(event_data)

    return formatted_events

def list_events_for_next_period(hours=0, minutes=30, max_threads=10):
    total_start_time = time.time()

    now = datetime.utcnow()
    time_min = now.isoformat() + 'Z'
    # Incorporate both hours and minutes into the time frame
    time_max = (now + timedelta(hours=hours, minutes=minutes)).isoformat() + 'Z'

    main_service = create_service()
    calendars = fetch_calendars(main_service)

    if not calendars:
        return json.dumps({
            "events": [],
            "message": "No calendars found.",
            "status": "error"
        })

    # Using ThreadPoolExecutor with a configurable number of threads
    all_events = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        events_per_calendar = executor.map(lambda calendar: process_calendar_events(calendar, time_min, time_max), calendars)
        for events in events_per_calendar:
            all_events.extend(events)

    total_elapsed_time = time.time() - total_start_time
    response = {
        "events": all_events,
        "message": "Events retrieved successfully." if all_events else "No events found.",
        "status": "success" if all_events else "error"
    }

    print(f"\nTotal time taken: {total_elapsed_time:.2f} seconds")
    return json.dumps(response, indent=2)

