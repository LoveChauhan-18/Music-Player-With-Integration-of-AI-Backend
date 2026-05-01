import requests
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

print("CURRENT DIR:", os.getcwd())

API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

headers = {
    "xi-api-key": str(API_KEY),
    "Content-Type": "application/json"
}

print("API_KEY VALUE:", API_KEY)
print("HEADERS:", headers)


data = {
    "text": "Bhai ab ye pakka chalega 🔥",
    "model_id": "eleven_multilingual_v2"
}

print("Calling API...")

response = requests.post(url, json=data, headers=headers)

print("STATUS:", response.status_code)

# 🔥 DEBUG
if response.status_code != 200:
    print("ERROR RESPONSE:", response.text)
else:
    with open("output.mp3", "wb") as f:
        f.write(response.content)
    print("Audio saved ✅")