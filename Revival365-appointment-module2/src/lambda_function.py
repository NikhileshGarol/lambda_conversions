import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from doctor_list_events import list_events_by_date
from date_pattern import get_calendar_availability
from week_pattern import get_weekly_availability
from edit_schedule import edit_availability
from Year_schedule import handle_set_global_availability
from empty_calender import delete_all_events
from datetime import datetime


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

# Lambda entry point
def lambda_handler(event, context):
    path = event.get('rawPath', '')
    response = create_response(404, {"error": "Not Found"})

    try:
        if path.startswith("/appointment"):
            response = api_list_events(event)
        elif path.startswith("/date_schedule"):
            response = api_date_pattern(event)
        elif path.startswith("/week_schedule"):
            response = api_week_pattern(event)
        elif path.startswith("/edit_availability"):  # New API endpoint for editing availability
            response = api_edit_availability(event)
        elif path.startswith("/year_schedule"):  # New API endpoint for editing availability
            response = api_year_schedule(event)
        elif path.startswith("/empty_calender"):  # New API endpoint for editing availability
            response = api_delete_all_events(event)
    except Exception as e:
        response = handle_error(e)

    return response


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

def api_date_pattern(event):
    query_params = event.get('queryStringParameters', {})
    calendar_id = query_params.get('calendar_id')
    start_date_str = query_params.get('start_date', '').strip()
    end_date_str = query_params.get('end_date', '').strip()

    print(f"Event: {event}")  # Log the full event
    print(f"start_date_str: {start_date_str}, end_date_str: {end_date_str}")  # Debugging log

    if not calendar_id or not start_date_str or not end_date_str:
        return create_response(400, {"error": "Missing required parameters: calendar_id, start_date, end_date"})

    try:
        print(f"Type of start_date_str: {type(start_date_str)}")  # Log type of date strings
        print(f"Type of end_date_str: {type(end_date_str)}")
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        availability = get_calendar_availability(calendar_id, start_date, end_date)
        return create_response(200, availability)
    except ValueError:
        return create_response(400, {"error": "Invalid date format. Use YYYY-MM-DD."})
    except Exception as e:
        return handle_error(e)
'''
# API to get weekly availability from Google Calendar
def api_week_pattern(event):
    query_params = event.get('queryStringParameters', {})
    calendar_id = query_params.get('calendar_id')

    if not calendar_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"error": "calendar_id is required"})
        }

    try:
        # Get the weekly availability for the given calendar_id
        availability = get_weekly_availability(calendar_id)
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(availability, indent=2)
        }
    except Exception as e:
        return handle_error(e)
        
'''
def api_week_pattern(event):
    query_params = event.get('queryStringParameters', {})
    calendar_id = query_params.get('calendar_id')

    if not calendar_id:
        return create_response(400, {"error": "calendar_id is required"})

    try:
        # Get the weekly availability for the given calendar_id
        availability = get_weekly_availability(calendar_id)
        return create_response(200, availability)
    except Exception as e:
        return handle_error(e)

        
def api_edit_availability(event):
    # Extract the body from the event
    body = event.get('body', '{}')
    
    try:
        # Parse the body as JSON
        body_data = json.loads(body)
        
        # Extract the parameters from the body data
        calendar_id = body_data.get('calendar_id')
        availability_data = body_data.get('availability_data')

        if not calendar_id or not availability_data:
            return create_response(400, {"error": "Missing required parameters: calendar_id, availability_data"})

        # Call the edit_availability function (assumed to be defined elsewhere)
        edit_availability(calendar_id, availability_data)

        return create_response(200, {"message": "Availability updated successfully"})
    except json.JSONDecodeError:
        return create_response(400, {"error": "Invalid JSON in request body"})
    except Exception as e:
        return handle_error(e)

# API to handle global availability for the year
def api_year_schedule(event):
    print("Event received:", event)

    try:
        # Ensure the body is a string before processing it
        body = event.get('body', '{}')

        # If it's a string, load it into a dictionary
        body_dict = json.loads(body)
        calendar_id = body_dict.get('calendar_id')
        availability_data = body_dict.get('availability_data')

        if not calendar_id or not availability_data:
            return create_response(400, {"error": "Missing required parameters: calendar_id, availability_data"})

        # Call the handle_set_global_availability function (assumed to be defined elsewhere)
        handle_set_global_availability(calendar_id, availability_data)

        return create_response(200, {"message": "Global availability updated successfully"})
    
    except Exception as e:
        return handle_error(e)
        
        
def api_delete_all_events(event):
    query_params = event.get('queryStringParameters', {})
    calendar_id = query_params.get('calendar_id')

    if not calendar_id:
        return create_response(400, {"error": "calendar_id is required"})

    try:
        # Call the delete_all_events function with the provided calendar_id
        delete_all_events(calendar_id)
        return create_response(200, {"message": f"All events from calendar {calendar_id} deleted successfully."})
    except Exception as e:
        return handle_error(e)