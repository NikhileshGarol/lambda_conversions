from datetime import datetime, time
from dateutil.tz import gettz

def get_timezone():
    """Returns the timezone object for UTC-6:00."""
    return gettz("America/Chicago")  # Change this if needed

def get_ist_timezone():
    """Returns the timezone object for IST (UTC+5:30)."""
    return gettz("Asia/Kolkata")

def get_wake_up_time():
    """Returns today's wake-up time (06:00 AM) in UTC-6 timezone."""
    tz = get_timezone()
    today = datetime.now(tz).date()  # Get today's date in UTC-6
    wake_up_time = datetime.combine(today, time(6, 30), tz)  # Set wake-up time as 06:00 AM with timezone

    return wake_up_time

def get_wake_up_time_in_ist():
    """Converts wake-up time from UTC-6 to IST and returns it."""
    wake_up_time = get_wake_up_time()
    ist_tz = get_ist_timezone()
    wake_up_time_ist = wake_up_time.astimezone(ist_tz)  # Convert to IST

    return wake_up_time_ist

# Example usage
wake_up_ist = get_wake_up_time_in_ist()
print("Wake-Up Time in IST:", wake_up_ist.strftime("%Y-%m-%d %H:%M:%S %Z%z"))
