import json
from app.config import settings

# Load original from JSON file
with open("app/ai-driven-task-scheduler-4a465b6fdc65.json", "r") as f:
    json_creds = json.load(f)

# Load from config
env_creds = settings.get_google_credentials()

print("Comparing credential dictionaries:")
for k, v in json_creds.items():
    env_v = env_creds.get(k)
    is_match = v == env_v
    print(f"Key: {k:<30} | Match: {str(is_match):<6} | JSON: {repr(v)[:50]} | ENV: {repr(env_v)[:50]}")
