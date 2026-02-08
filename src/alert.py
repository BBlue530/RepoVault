import requests
import json

def alert_webhook(DISCORD_WEBHOOK, alert, message):
    payload = {
        "embeds": [{
            "title": f"🚨 {alert}",
            "description": message,
            "color": 16711680
        }]
    }
    response = requests.post(
        DISCORD_WEBHOOK,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )

    if response.status_code not in [200, 204]:
        print("[!] Failed to send alert to webhook!")
        print(f"[!] Title: [{alert}]")
        print(f"[!] Message: [{message}]")