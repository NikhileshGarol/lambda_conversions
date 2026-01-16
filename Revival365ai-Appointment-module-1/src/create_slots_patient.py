import json
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from collections import defaultdict
from dateutil.tz import gettz
from appointment_config import service  # Importing the 'service' object from config.py

# Define Indian Standard Time (IST)
IST = gettz('Asia/Kolkata')

def create_event_from_slot(calendar_id, selected_slot_start, selected_slot_end, title, description, selected_date, patient_id):
    try:
        if not all([calendar_id, selected_slot_start, selected_slot_end, selected_date, title, description, patient_id]):
            raise ValueError("All parameters are required and must be non-empty.")

        # Convert times to IST
        if "T" in selected_slot_start:  # If ISO 8601 format
            start_time = datetime.fromisoformat(selected_slot_start).astimezone(IST)
            end_time = datetime.fromisoformat(selected_slot_end).astimezone(IST)
        else:  # Convert from simple time strings
            start_time_str = f"{selected_date} {selected_slot_start}"
            end_time_str = f"{selected_date} {selected_slot_end}"
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)

        # Check if the selected time is in the past
        now = datetime.now(IST)
        if start_time < now:
            raise ValueError("Appointments cannot be created for past dates or times.")

        # Check for existing appointments in the same timeslot
        existing_events = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True
        ).execute()

        for event in existing_events.get('items', []):
            # Skip transparent events
            if event.get('transparency') == 'transparent':
                continue

            # Parse event start and end times
            event_start = parser.isoparse(event['start']['dateTime'])
            event_end = parser.isoparse(event['end']['dateTime'])

            # Check for overlapping times
            if (start_time < event_end and end_time > event_start):
                raise ValueError("An appointment already exists for the selected timeslot.")

        # Prepare event data
        event_payload = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'extendedProperties': {
                'private': {
                    'patient_id': patient_id
                }
            }
        }

        # Log payload for debugging
        print(f"Creating event with payload: {json.dumps(event_payload, indent=2)}")

        # API Call
        created_event = service.events().insert(calendarId=calendar_id, body=event_payload).execute()

        # Validate response
        appointment_id = created_event.get('id')
        if not appointment_id:
            raise Exception("Appointment ID is missing in the response")

        # Return details
        return {
            "appointmentId": appointment_id,
            "start_time": start_time.strftime("%I:%M %p"),
            "end_time": end_time.strftime("%I:%M %p"),
            "status": "confirmed",
            "message": "Your appointment has been successfully booked."
        }

    except HttpError as http_err:
        raise Exception(f"Google API error: {http_err}")
    except ValueError as val_err:
        raise Exception(f"Input validation error: {val_err}")
    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")

'''
 

def create_event_from_slot(calendar_id, selected_slot_start, selected_slot_end, title, description, selected_date, patient_id):
    try:
        # Check if all parameters are provided
        if not all([calendar_id, selected_slot_start, selected_slot_end, selected_date, title, description, patient_id]):
            raise ValueError("All parameters are required and must be non-empty.")

        # Convert times to IST
        if "T" in selected_slot_start:  # If ISO 8601 format
            start_time = datetime.fromisoformat(selected_slot_start).astimezone(IST)
            end_time = datetime.fromisoformat(selected_slot_end).astimezone(IST)
        else:  # Convert from simple time strings
            start_time_str = f"{selected_date} {selected_slot_start}"
            end_time_str = f"{selected_date} {selected_slot_end}"
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %I:%M %p").replace(tzinfo=IST)

        # Authenticate the Google Calendar API service
 
        # Check for existing events in the selected time range
        existing_events = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        # Check if the time slot is available (transparent)
        for event in existing_events.get('items', []):
            if event.get('transparency') == 'transparent':  # Available slot
                print(f"Found an available event. Booking the slot with ID: {event['id']}")
                
                # Update the event to mark it as booked (opaque)
                event_payload = {
                    'summary': title,
                    'description': description,
                    'start': {
                        'dateTime': start_time.isoformat(),
                        'timeZone': 'Asia/Kolkata'
                    },
                    'end': {
                        'dateTime': end_time.isoformat(),
                        'timeZone': 'Asia/Kolkata'
                    },
                    'extendedProperties': {
                        'private': {
                            'patient_id': patient_id
                        }
                    },
                    'transparency': 'opaque'  # Mark the event as booked
                }

                # API Call to update event
                updated_event = service.events().update(calendarId=calendar_id, eventId=event['id'], body=event_payload).execute()

                # Return updated event details
                return {
                    "appointmentId": updated_event.get('id'),
                    "start_time": start_time.strftime("%I:%M %p"),
                    "end_time": end_time.strftime("%I:%M %p"),
                    "status": "confirmed",
                    "message": "Your appointment has been successfully booked."
                }

        # If no existing available event, raise an error
        raise ValueError("The selected time slot is not available.")

    except HttpError as http_err:
        raise Exception(f"Google API error: {http_err}")
    except ValueError as val_err:
        raise Exception(f"Input validation error: {val_err}")
    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")
'''