from app.config import settings

pk = settings.GOOGLE_PRIVATE_KEY
print("Length of raw loaded key:", len(pk))
print("First 50 characters:", repr(pk[:50]))
print("Last 50 characters:", repr(pk[-50:]))
print("Starts with quote:", pk.startswith('"'))
print("Ends with quote:", pk.endswith('"'))
