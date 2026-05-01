import urllib.request
import json

API_KEY = "sk_994c6bfc2324c316099beb2085c7451f8d5f99ec59e0c3f4"

def list_voices():
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "xi-api-key": API_KEY
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"SUCCESS! Found {len(data['voices'])} voices.")
            for v in data['voices'][:3]:
                print(f"- {v['name']} ({v['voice_id']})")
    except Exception as e:
        print(f"FAILED! Error: {str(e)}")

if __name__ == "__main__":
    list_voices()
