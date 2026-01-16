from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pathlib import Path

# Path to your service account credentials
# SERVICE_ACCOUNT_FILE = 'serviceaccount.json'
BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceaccount.json"

# Scopes required for Google Calendar API (full access to manage calendar)
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Authenticate and build the service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)

# Function to delete all events from the calendar
def delete_all_events(calendar_id):
    try:
        # List all events in the calendar
        events_result = service.events().list(
            calendarId=calendar_id,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Check if there are any events
        if not events:
            print("No events found to delete.")
        else:
            print(f"Deleting {len(events)} events...")

            # Delete each event one by one
            for event in events:
                event_id = event['id']
                service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
                print(f"Deleted event: {event.get('summary', 'No title')}")
            print("All events deleted successfully.")
    
    except HttpError as error:
        print(f"An error occurred: {error}")

# Example function call (you can replace this with the actual function call in your code)
def main():
    # Pass the calendar ID as an argument to the delete_all_events function
    calendar_id = 'your_calendar_id_here'  # Replace with the actual calendar ID
    delete_all_events(calendar_id)

# Run the main function
if __name__ == "__main__":
    main()
