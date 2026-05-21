import json

with open("app/ai-driven-task-scheduler-4a465b6fdc65.json", "r") as f:
    data = json.load(f)

private_key = data.get("private_key", "")
print("Private Key Type:", type(private_key))
print("Private Key Length:", len(private_key))
print("First 100 characters:", repr(private_key[:100]))
print("Does it contain double-escaped newlines (\\\\n)?", "\\n" in private_key)
print("Does it contain actual newlines (\\n)?", "\n" in private_key)
