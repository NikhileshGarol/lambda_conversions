# config.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path

# SERVICE_ACCOUNT_FILE = 'serviceaccount.json'
BASE_DIR = Path(__file__).resolve().parent
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceaccount.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=credentials)
