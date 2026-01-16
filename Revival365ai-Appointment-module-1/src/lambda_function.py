import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from doctor_list_events import list_events_by_date
from free_slots_patient import get_available_slots
from create_slots_patient import create_event_from_slot
from list_patient_events import list_events_patient
from create_calendar import create_calendar_with_id
from delete_event import delete_event
from schedular_function import list_events_for_next_period
from set_schedule import set_availability, set_full_day_unavailability


def create_response(status_code, data):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST',

        },
        'body': json.dumps(data)
    }

# Utility function to handle and log errors


def handle_error(e, status_code=500):
    logging.error(f"Error occurred: {str(e)}")
    return create_response(status_code, {"error": str(e)})

# Helper to parse event body whether it's already a dict or a JSON string


def parse_body(event):
    raw = event.get('body', None)
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if raw == '':
            return {}
        return json.loads(raw)
    if isinstance(raw, (bytes, bytearray)):
        return json.loads(raw.decode('utf-8'))
    raise ValueError('Invalid body type')

# Helper to parse event body whether it's already a dict or a JSON string


def parse_body(event):
    raw = event.get('body', None)
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if raw == '':
            return {}
        return json.loads(raw)
    if isinstance(raw, (bytes, bytearray)):
        return json.loads(raw.decode('utf-8'))
    raise ValueError('Invalid body type')

# Lambda entry point


def lambda_handler(event, context):
    path = event.get('rawPath', '')
    response = create_response(404, {"error": "Not Found"})

    try:
        if path.startswith("/appointment"):
            response = api_list_events(event)
        elif path == "/calendar":
            response = api_create_calendar(event)
        elif path.startswith("/slots/available"):
            response = api_free_slots(event)
        elif path.startswith("/create_appointment"):
            response = api_add_event_from_slot(event)
        elif path.startswith("/delete_appointment"):
            response = api_delete_event(event)
        elif path.startswith("/patient_appointment"):
            response = api_list_events_patient(event)
        # New route for the scheduler function
        elif path.startswith("/upcoming_events"):
            response = api_scheduler(event)
        elif path == "/set_availability":  # Handle set availability
            response = api_set_availability(event)
    except Exception as e:
        response = handle_error(e)

    return response


'''
# API to get free slots grouped by day
def api_free_slots(event):
    calendar_id = event.get('queryStringParameters', {}).get('calendar_id')
    if not calendar_id:
        return create_response(400, {"error": "calendar_id is required"})
    try:
        free_slots = get_free_slots_grouped_by_day(calendar_id)
        return create_response(200, {"free_slots": free_slots})
    except Exception as e:
        return handle_error(e)
'''


def api_free_slots(event):
    """
    API endpoint to get free slots grouped by day.

    Args:
        event (dict): Event object from the API gateway containing query parameters.

    Returns:
        dict: API response with status code and free slots or error message.
    """
    # Extract query parameters from the event object
    query_params = event.get('queryStringParameters', {})
    calendar_id = query_params.get('calendar_id')
    # Optional: defaults to next 7 days in get_available_slots
    date = query_params.get('date')
    duration = query_params.get('duration')

    if not calendar_id:
        return create_response(400, {"error": "calendar_id is required"})

    try:
        # If duration is provided, ensure it is an integer
        if duration:
            try:
                duration = int(duration)
            except ValueError:
                return create_response(400, {"error": "duration must be an integer"})

        # Fetch free slots using get_available_slots with all parameters
        available_slots = get_available_slots(
            calendar_id, date=date, duration=duration or 60)
        return create_response(200, {"free_slots": available_slots.get("free_slots", [])})
    except Exception as e:
        return handle_error(e)


# API to list events by date
def api_list_events(event):
    query_params = event.get('queryStringParameters', {})
    calendar_id = query_params.get('calendar_id')
    date = query_params.get('date')

    if not calendar_id:
        return create_response(400, {"error": "calendar_id is required"})
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return create_response(400, {"error": "Invalid date format. Please use YYYY-MM-DD."})

    try:
        response = list_events_by_date(calendar_id, date)
        if response["status"] == "success":
            return create_response(200, response)
        elif response["status"] == "no_events":
            return create_response(404, response)
        else:
            return create_response(500, response)
    except Exception as e:
        return handle_error(e)

# API to create a calendar


def api_create_calendar(event):
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return handle_error("Invalid JSON body", 400)

    id = body.get('id')
    if not id:
        return create_response(400, {"error": "id is required"})

    try:
        calendar_id = create_calendar_with_id(id)
        if calendar_id:
            return create_response(200, {"calendar_id": calendar_id})
        else:
            return create_response(500, {"error": "Failed to create calendar"})
    except Exception as e:
        return handle_error(e)

# API to add an event from a slot


def api_add_event_from_slot(event):
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError as e:
        return handle_error("Invalid JSON body", 400)

    required_fields = ['start', 'end', 'title', 'description', 'date']
    if not all(body.get(field) for field in required_fields):
        return create_response(400, {
            "responseType": "appointmentError",
            "status": "failed",
            "message": "Missing required fields. Please provide all necessary information."
        })

    calendar_id = event.get('queryStringParameters', {}).get('calendar_id')
    if not calendar_id:
        return create_response(400, {"error": "calendar_id is required"})

    try:
        response = create_event_from_slot(
            calendar_id=calendar_id,
            selected_slot_start=body['start'],
            selected_slot_end=body['end'],
            title=body['title'],
            description=body['description'],
            selected_date=body['date'],
            patient_id=body.get('patient_id', "Unknown")
        )
        return create_response(201, response)
    except Exception as e:
        return handle_error(e)

# API to delete an event


def api_delete_event(event):
    try:
        # Parse the body and retrieve the parameters
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON body"})

    # Retrieve calendar_id and event_id from the body
    calendar_id = body.get('calendar_id')
    event_id = body.get('event_id')

    # Validate required parameters
    if not calendar_id:
        return create_response(400, {"error": "calendar_id is required"})
    if not event_id:
        return create_response(400, {"error": "event_id is required"})

    try:
        # Attempt to delete the event
        response = delete_event(calendar_id, event_id)
        if 'error' in response:
            return create_response(500, response)
        else:
            return create_response(200, response)
    except Exception as e:
        return handle_error(e)


def api_list_events_patient(event):
    # Extract query parameters from the event
    query_params = event.get('queryStringParameters', {})

    # Debug: Print query parameters to check what is being received
    print(f"Query Parameters: {query_params}")

    # Extract 'date' and 'patient_id' directly from query_params
    date = query_params.get("date")
    patient_id = query_params.get("patient_id")
    calendar_id = query_params.get("calendar_id")
    # Debug: Print individual values for date and patient_id
    print(f"Date: {date}, Patient ID: {patient_id}")

    # Validate the date format
    if date:
        try:
            # Check if the date is in the correct format (YYYY-MM-DD)
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return create_response(400, {"error": "Invalid date format. Please use YYYY-MM-DD."})

    try:
        # Call the function that lists events for the patient
        response = list_events_patient(date, patient_id, calendar_id)

        # Handle the response from list_events_patient
        if response["status"] == "success":
            return create_response(200, response)
        elif response["status"] == "no_events":
            return create_response(404, response)
        else:
            return create_response(500, response)

    except Exception as e:
        # Handle any unexpected errors
        return handle_error(e)


def api_scheduler(event):
    query_params = event.get('queryStringParameters', {})

    # Extract optional query parameters for hours, minutes, and max_threads
    hours = int(query_params.get('hours', 0))  # Default to 0 if not provided
    minutes = int(query_params.get('minutes', 30))  # Default to 30 minutes
    max_threads = int(query_params.get('max_threads', 30)
                      )  # Default to 10 threads
    count = query_params.get('count')

    try:
        # Call the scheduler function
        response = list_events_for_next_period(
            hours=hours, minutes=minutes, max_threads=max_threads)

        # If the response is a string, assume it's JSON and parse it into a dictionary
        if isinstance(response, str):
            # Convert string response to a dictionary
            response = json.loads(response)

        # Now you can check the 'status' key safely
        if response.get("status") == "success":
            return create_response(200, response)  # Return success status
        elif response.get("status") == "no_events":
            # Return "not found" if no events
            return create_response(404, response)
        else:
            # Return server error for any other status
            return create_response(500, response)

    except Exception as e:
        # Handle any unexpected errors
        return handle_error(e)


def api_set_availability(event):
    try:
        # Parse the JSON body from the event
        body = parse_body(event)
    except (json.JSONDecodeError, ValueError):
        return handle_error("Invalid JSON body", 400)

    # Extract 'calendar_id' and 'availability' from the body
    calendar_id = body.get('calendar_id')
    availability_data = body.get('availability')

    # Validate that 'calendar_id' and 'availability' are present
    if not calendar_id or not availability_data:
        return create_response(400, {"error": "calendar_id and availability are required"})

    try:
        # Loop through each day's availability data
        for day in availability_data:
            date = day.get('date')
            available_slots = day.get('available_slots')

            # Check for unavailable days
            if not available_slots or available_slots in ([], "not available"):
                set_full_day_unavailability(calendar_id, date)
            elif available_slots:
                # Set availability for the provided slots
                set_availability(calendar_id, date, available_slots)
            else:
                print(f"No available slots provided for {date}")

        # Success response
        return create_response(200, {"message": "Availability set successfully"})

    except Exception as e:
        return handle_error(str(e), 500)
