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

 # Function to delete an event from the selected calendar
def delete_event(calendar_id, event_id):
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"message": f"Event with ID {event_id} has been deleted."}
    except HttpError as error:
        if error.resp.status == 404:
            return {"error": f"Error: Event ID {event_id} not found."}
        else:
            return {"error": f"An error occurred: {error}"}

