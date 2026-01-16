import json
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from dateutil.tz import gettz
from appointment_config import service  # Importing the 'service' object from config.py

# Define Indian Standard Time (IST)
IST = gettz('Asia/Kolkata')

def list_events_by_date(calendar_id, date=None):
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    try:
        # Fetch events from Google Calendar
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=100,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        if not events:
            return {"status": "no_events", "message": "No upcoming events found.", "events": []}
        
        filtered_events = []

        for event in events:
            # Parse event start and end times
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            if start:
                start = parser.isoparse(start).astimezone(IST)  # Convert to IST
            if end:
                end = parser.isoparse(end).astimezone(IST)  # Convert to IST

            # Skip events without a patient_id
            patient_id = event.get('extendedProperties', {}).get('private', {}).get('patient_id')
            if not patient_id:
                continue

            # Filter events by the provided date, if any
            if date:
                if start.strftime("%Y-%m-%d") != date:
                    continue
            
            # Add event details to the filtered list
            filtered_events.append({
                'appointmentdetails': event.get('description', 'No Title'),
                'date': start.strftime("%Y-%m-%d") if start else "Unknown",
                'starttime': start.strftime("%I:%M %p") if start else "Unknown",
                'endtime': end.strftime("%I:%M %p") if end else "Unknown",
                'id': event['id'],
                'patient_id': patient_id
            })

        if not filtered_events:
            return {"status": "no_events", "message": f"No events found for date {date}.", "events": []}
        
        return {"status": "success", "message": "Events retrieved successfully.", "events": filtered_events}
    except HttpError as error:
        return {"status": "error", "message": f"An error occurred while listing events: {error}", "events": []}
