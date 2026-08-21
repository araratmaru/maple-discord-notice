import os
import requests

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

data = {
    "content": "✅ GitHub Actions からのWebhookテストです"
}

response = requests.post(
    WEBHOOK_URL,
    json=data,
    timeout=30
)

print("status_code:", response.status_code)
print("response:", response.text)

response.raise_for_status()
