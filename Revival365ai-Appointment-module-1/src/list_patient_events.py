'''
import json
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from dateutil.tz import gettz
from config import service  # Importing the 'service' object from config.py

# Define Indian Standard Time (IST)
IST = gettz('Asia/Kolkata')
 


def list_events_patient(date=None, patient_id=None, calendar_id=None):
    try:
        # If no calendar ID is provided, return an error
        if not calendar_id:
            return {
                "status": "error",
                "message": "No calendar ID provided.",
                "events": []
            }

        # Determine timeMin based on whether a specific date is provided
        if date:
            # Convert the given date to a datetime object
            start_of_day = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=IST)
            end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
            time_min = start_of_day.isoformat()
            time_max = end_of_day.isoformat()
        else:
            # Fetch all events from a sufficiently old date
            time_min = datetime(1970, 1, 1).isoformat() + 'Z'
            time_max = None

        # Fetch events from the calendar
        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,  # Only include this if a date is provided
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
        except HttpError as error:
            return {
                "status": "error",
                "message": f"Error fetching events from calendar {calendar_id}: {error}",
                "events": []
            }

        # Filter events by patient_id and optionally by date
        filtered_events = []
        for event in events:
            # Parse start and end times
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            if start:
                start = parser.isoparse(start).astimezone(IST)
            if end:
                end = parser.isoparse(end).astimezone(IST)

            # Get event date
            event_date = start.strftime("%Y-%m-%d") if start else None

            # Check filters
            event_patient_id = event.get('extendedProperties', {}).get('private', {}).get('patient_id')
            if patient_id and event_patient_id != patient_id:
                continue  # Skip events that don't match the patient_id
            if date and event_date != date:
                continue  # Skip events that don't match the date

            # Append the event to the filtered list
            filtered_events.append({
                'appointmentdetails': event.get('summary', 'No Title'),
                'starttime': start.strftime("%I:%M %p") if start else "Unknown",
                'endtime': end.strftime("%I:%M %p") if end else "Unknown",
                'id': event['id'],
                'patient_id': event_patient_id or 'Not Provided',
                'calendar_id': calendar_id,
                'event_date': event_date  # Add event date to the response
            })

        # Return results
        if not filtered_events:
            return {
                "status": "no_events",
                "message": f"No events found for date {date} and patient_id {patient_id}.",
                "events": []
            }

        return {
            "status": "success",
            "message": "Events retrieved successfully.",
            "events": filtered_events
        }
    except HttpError as error:
        return {
            "status": "error",
            "message": f"An error occurred while listing events: {error}",
            "events": []
        }
'''


from datetime import datetime
from dateutil import parser
from dateutil.tz import gettz
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from appointment_config import service  # Importing the 'service' object from config.py

# Define Indian Standard Time (IST)
IST = gettz('Asia/Kolkata')

def list_events_patient(date=None, patient_id=None, calendar_id=None):
    try:
        # If no calendar ID is provided, return an error
        if not calendar_id:
            return {
                "status": "error",
                "message": "No calendar ID provided.",
                "events": []
            }

        # Determine timeMin based on whether a specific date is provided
        if date:
            # Convert the given date to a datetime object
            start_of_day = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=IST)
            end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
            time_min = start_of_day.isoformat()
            time_max = end_of_day.isoformat()
        else:
            # Fetch all events from a sufficiently old date
            time_min = datetime(1970, 1, 1).isoformat() + 'Z'
            time_max = None

        # Fetch events from the calendar
        try:
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,  # Only include this if a date is provided
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
        except HttpError as error:
            return {
                "status": "error",
                "message": f"Error fetching events from calendar {calendar_id}: {error}",
                "events": []
            }

        # Get the current time
        current_time = datetime.now(IST)

        # Filter events by patient_id and only include upcoming events
        filtered_events = []
        for event in events:
            # Parse start and end times
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            if start:
                start = parser.isoparse(start).astimezone(IST)
            if end:
                end = parser.isoparse(end).astimezone(IST)

            # Only include upcoming events
            if end and end < current_time:
                continue  # Skip events that have already passed

            # Get event date
            event_date = start.strftime("%Y-%m-%d") if start else None

            # Check filters
            event_patient_id = event.get('extendedProperties', {}).get('private', {}).get('patient_id')
            if patient_id and event_patient_id != patient_id:
                continue  # Skip events that don't match the patient_id
            if date and event_date != date:
                continue  # Skip events that don't match the date

            # Append the event to the filtered list
            filtered_events.append({
                'appointmentdetails': event.get('summary', 'No Title'),
                'starttime': start.strftime("%I:%M %p") if start else "Unknown",
                'endtime': end.strftime("%I:%M %p") if end else "Unknown",
                'id': event['id'],
                'patient_id': event_patient_id or 'Not Provided',
                'calendar_id': calendar_id,
                'event_date': event_date  # Add event date to the response
            })

        # Return results
        if not filtered_events:
            return {
                "status": "no_events",
                "message": f"No upcoming events found for date {date} and patient_id {patient_id}.",
                "events": []
            }

        return {
            "status": "success",
            "message": "Upcoming events retrieved successfully.",
            "events": filtered_events
        }
    except HttpError as error:
        return {
            "status": "error",
            "message": f"An error occurred while listing events: {error}",
            "events": []
        }
