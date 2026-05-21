import json
from app.config import settings

# Load original from JSON file
with open("app/ai-driven-task-scheduler-4a465b6fdc65.json", "r") as f:
    json_data = json.load(f)
json_pk = json_data.get("private_key", "")

# Load from env and run our unescaping logic
env_pk = settings.GOOGLE_PRIVATE_KEY
if env_pk:
    env_pk = env_pk.replace("\\n", "\n")

print("JSON Key Length:", len(json_pk))
print("ENV Key Length:", len(env_pk))
print("Are they identical?", json_pk == env_pk)

if json_pk != env_pk:
    print("Finding first mismatch...")
    for i, (c1, c2) in enumerate(zip(json_pk, env_pk)):
        if c1 != c2:
            print(f"Mismatch at index {i}: JSON={repr(c1)}, ENV={repr(c2)}")
            break
