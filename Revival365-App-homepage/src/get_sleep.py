import requests

def get_sleep_summary(user_id, date):
    url = f"https://devapi.revival365ai.com/data/chart/sleep_readings/{user_id}/{date}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        #print(f"Fetching sleep data for {date}")  # Debugging step
        #print("Raw Sleep Data:", data)  # Debugging step

        if not isinstance(data, dict):  
            print("Invalid response format")
            return None

        # Use `.get()` with default values to prevent KeyErrors
        sleep_summary = {
            "date": date,
            "deep": f"{data.get('deep')}" if data.get('deep') not in [None, 0] else None,
            "light": f"{data.get('light')}" if data.get('light') not in [None, 0] else None,
            "rem": f"{data.get('rem')}" if data.get('rem') not in [None, 0] else None,
            "awake": f"{data.get('awake')}" if data.get('awake') not in [None, 0] else None,
            "totalSleep": f"{data.get('totalSleep')}" if data.get('totalSleep') not in [None, 0] else None
        }

        return sleep_summary
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sleep data: {e}")
        return None

