'''
import json
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from datetime import datetime, timedelta
from collections import defaultdict
from dateutil.tz import gettz
from config import service  # Importing the 'service' object from config.py
IST = gettz('Asia/Kolkata')



# Define Indian Standard Time (IST)

def get_free_slots_grouped_by_day(calendar_id):
    # Define IST timezone and set start and end times
    ist = gettz('Asia/Kolkata')
    utc = gettz('UTC')
    
    # Start and end times for the 7-day range in UTC
    start_time = datetime.utcnow().replace(tzinfo=utc)
    end_time = start_time + timedelta(days=7)

    # Prepare the body for the freeBusy query
    body = {
        "timeMin": start_time.isoformat(),
        "timeMax": end_time.isoformat(),
        "items": [{"id": calendar_id}]
    }

    # Call the freeBusy API using the authenticated 'service'
    free_busy_query = service.freebusy().query(body=body).execute()

    # Get the busy slots from the response
    busy_slots = free_busy_query['calendars'][calendar_id]['busy']

    # Dictionary to store free slots grouped by day
    free_slots_by_day = defaultdict(list)
    
    # Loop through each day in the specified 7-day range
    current_day = start_time.astimezone(ist).replace(hour=9, minute=0, second=0, microsecond=0)

    # Adjust current_day for today to start from the next full hour
    if start_time.astimezone(ist).date() == current_day.date():
        current_hour = start_time.astimezone(ist).replace(minute=0, second=0, microsecond=0)
        next_hour = current_hour + timedelta(hours=1)
        if next_hour.hour < 9:
            current_day = current_day  # Start at 9:00 AM if next_hour is earlier
        else:
            current_day = next_hour

    while current_day < end_time:
        day_end_time = current_day.replace(hour=18)  # 6:00 PM IST for each day

        # Loop through each hour within the current day's remaining working hours
        current_time = current_day
        while current_time < day_end_time:
            next_hour = current_time + timedelta(hours=1)

            # Check if this hour is free by seeing if it overlaps with any busy slots
            is_free = True
            for busy_slot in busy_slots:
                busy_start = parser.isoparse(busy_slot['start']).astimezone(ist)
                busy_end = parser.isoparse(busy_slot['end']).astimezone(ist)
                
                # Check for overlap
                if busy_start < next_hour and busy_end > current_time:
                    is_free = False
                    break

            # If the hour is free, add it to the appropriate day in the dictionary
            if is_free:
                day_key = current_time.strftime("%Y-%m-%d")
                free_slots_by_day[day_key].append({
                    "start": current_time.strftime("%I:%M %p"),
                    "end": next_hour.strftime("%I:%M %p")
                })

            # Move to the next hour
            current_time = next_hour

        # Move to the next day, setting time to 9:00 AM IST
        current_day = (current_day + timedelta(days=1)).replace(hour=9, minute=0)

    # Format the output as a list of dictionaries, each with "date" and "slots"
    free_slots_output = []
    for day, slots in free_slots_by_day.items():
        free_slots_output.append({
            "date": day,
            "slots": slots
        })

    return free_slots_output
'''

import datetime
from dateutil.tz import gettz
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import timedelta
from pathlib import Path
import json

# Google Calendar API Setup
SCOPES = ['https://www.googleapis.com/auth/calendar']
# SERVICE_ACCOUNT_FILE = 'serviceaccount.json'  # Path to your service account JSON file
BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceaccount.json"

def authenticate_with_service_account():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_existing_availability_slots(service, calendar_id, date):
    ist = gettz('Asia/Kolkata')
    print(f"Fetching existing availability slots for calendar_id: {calendar_id} on date: {date}")
    try:
        start_of_day = datetime.datetime.strptime(date, '%Y-%m-%d').replace(hour=0, minute=0, tzinfo=ist)
        end_of_day = start_of_day.replace(hour=23, minute=59)
    except ValueError:
        return {"free_slots": []}

    # Convert to UTC for Google Calendar API
    start_time_utc = start_of_day.astimezone(datetime.timezone.utc)
    end_time_utc = end_of_day.astimezone(datetime.timezone.utc)

    # Fetch events for the day
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_time_utc.isoformat(),
        timeMax=end_time_utc.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    available_slots = []
    booked_events = []

    # Separate available slots and booked events
    for event in events:
        description = event.get('description', '')
        transparency = event.get('transparency', '')
        start_time = datetime.datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00')).astimezone(ist)
        end_time = datetime.datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00')).astimezone(ist)

        if description == 'Available Slot.' and transparency == 'transparent':
            available_slots.append((start_time, end_time))
        else:
            booked_events.append((start_time, end_time))

    # Subtract booked times from available slots
    free_slots = []
    for slot_start, slot_end in available_slots:
        temp_slots = [(slot_start, slot_end)]  # Start with the full slot

        for book_start, book_end in booked_events:
            new_temp_slots = []
            for temp_start, temp_end in temp_slots:
                # No overlap
                if book_end <= temp_start or book_start >= temp_end:
                    new_temp_slots.append((temp_start, temp_end))
                else:
                    # Overlapping booked event, split the available slot
                    if temp_start < book_start:
                        new_temp_slots.append((temp_start, book_start))
                    if book_end < temp_end:
                        new_temp_slots.append((book_end, temp_end))
            temp_slots = new_temp_slots

        # Add remaining free slots
        free_slots.extend(temp_slots)

    # Format the free slots for output
    formatted_slots = []
    for slot_start, slot_end in free_slots:
        formatted_slots.append({
            'start': slot_start.strftime('%I:%M %p'),
            'end': slot_end.strftime('%I:%M %p')
        })

    return {"free_slots": [{"date": date, "slots": formatted_slots}]}


def split_time_slots(start_time, end_time, duration_minutes):
    slots = []
    
    # Adjust start_time to only round up if not already aligned
    def align_to_next_15(dt):
        if dt.minute % 15 == 0:  # Already aligned
            return dt
        else:
            # Round up to the next 15-minute interval
            minutes = ((dt.minute // 15) + 1) * 15
            if minutes >= 60:
                dt += timedelta(hours=1)
                minutes = 0
            return dt.replace(minute=minutes, second=0, microsecond=0)

    # Align start and end times
    start_time = align_to_next_15(start_time)
    end_time = align_to_next_15(end_time)

    current_time = start_time

    # Split the time range into smaller chunks based on the duration
    while current_time < end_time:
        next_slot_end = current_time + timedelta(minutes=duration_minutes)
        
        # Ensure the end time does not exceed the rounded end_time
        if next_slot_end > end_time:
            break

        slots.append({
            'start': current_time.strftime('%I:%M %p'),
            'end': next_slot_end.strftime('%I:%M %p')
        })

        current_time = next_slot_end

    return slots

    
 
def get_available_slots(calendar_id, date=None, duration=60):
    ist = gettz('Asia/Kolkata')

    if not calendar_id:
        raise ValueError("Calendar ID is required")

    # Get availability for the next 7 days if no date is provided
    if not date:
        today = datetime.datetime.now(ist).date()
        dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
        #tomorrow = datetime.datetime.now(ist).date() + timedelta(days=1)
        #dates = [(tomorrow + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    else:
        dates = [date]

    service = authenticate_with_service_account()

    free_slots = []
    now = datetime.datetime.now(ist)  # Current time in IST

    for date in dates:
        existing_slots = get_existing_availability_slots(service, calendar_id, date)
        combined_day_slots = []

        for day_slots in existing_slots.get('free_slots', []):
            for slot in day_slots['slots']:
                # Parse the slot with proper year and date
                slot_date = datetime.datetime.strptime(day_slots['date'], '%Y-%m-%d').date()
                slot_start = datetime.datetime.strptime(slot['start'], '%I:%M %p').replace(
                    year=slot_date.year, month=slot_date.month, day=slot_date.day, tzinfo=ist
                )
                slot_end = datetime.datetime.strptime(slot['end'], '%I:%M %p').replace(
                    year=slot_date.year, month=slot_date.month, day=slot_date.day, tzinfo=ist
                )

                # Debugging print statements
                print(f"Original Slot: {slot_start} - {slot_end}")

                # Filter out slots in the past for today's date
                if date == now.strftime('%Y-%m-%d'):
                    if slot_end <= now:
                        print(f"Excluding slot {slot_start} - {slot_end} (already passed)")
                        continue
                    if slot_start < now:
                        print(f"Adjusting start time for slot {slot_start} - {slot_end} to {now}")
                        slot_start = now

                # Add valid slots after adjustment
                if slot_start < slot_end:
                    split_slots = split_time_slots(slot_start, slot_end, duration)
                    combined_day_slots.extend(split_slots)
                else:
                    print(f"Skipping invalid slot: {slot_start} - {slot_end}")

            if combined_day_slots:
                free_slots.append({
                    'date': day_slots['date'],
                    'slots': combined_day_slots
                })

    return {"free_slots": free_slots}
