import json
from dateutil import parser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from datetime import datetime, timedelta
from collections import defaultdict
from dateutil.tz import gettz
from appointment2_config import service  # Importing the 'service' object from config.py


# Define Indian Standard Time (IST)
IST = gettz('Asia/Kolkata')

# Function to create a calendar for a doctor
def create_calendar_with_id(id):
    calendar = {
        'summary': f" {id}'s Calendar",
        'description': f"Calendar for  {id}",
        'timeZone': 'Asia/Kolkata',  # Set calendar timezone to IST
    }
    
    try:
        calendar_result = service.calendars().insert(body=calendar).execute()
        return calendar_result['id']
    except HttpError as error:
        print(f"An error occurred while creating the calendar: {error}")
        return None
