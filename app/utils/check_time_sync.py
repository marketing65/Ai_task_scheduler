import urllib.request
import datetime
import time

try:
    print("Fetching current time from Google...")
    response = urllib.request.urlopen('https://www.google.com')
    date_str = response.headers['Date']
    print(f"Google Server Time (UTC): {date_str}")
    
    # Parse Google server time
    # Format: Thu, 21 May 2026 10:36:00 GMT
    server_time = datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
    local_time_utc = datetime.datetime.utcnow()
    
    diff = (local_time_utc - server_time).total_seconds()
    print(f"Local System Time (UTC): {local_time_utc}")
    print(f"Time difference (Local - Server): {diff} seconds")
    
    if abs(diff) > 30:
        print("\n[WARNING] Your system clock is OUT OF SYNC by more than 30 seconds!")
        print("Google OAuth 2.0 rejects tokens if the clock is out of sync by more than 5 minutes.")
        print("Please synchronize your system clock in Windows Settings (Time & Language -> Sync Now).")
    else:
        print("\n[INFO] Your system clock is in sync (within 30 seconds).")
except Exception as e:
    print(f"Failed to compare time: {e}")
