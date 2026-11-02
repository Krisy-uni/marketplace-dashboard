import certifi
import ssl
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / "telegram_secrets.json"
LISTINGS = ROOT / "dashboard" / "listings.json"
SEEN = ROOT / "data" / "notified_listings.json"

def send_message(token, chat_id, message):
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "false"
    }).encode()

    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=20, context=ssl.create_default_context(cafile=certifi.where())) as response:
        result = json.load(response)

    return result.get("ok", False)

def main():
    if not SECRETS.exists():
        print("Telegram settings not found.")
        return

    if not LISTINGS.exists():
        print("Dashboard listings not found.")
        return

    secrets = json.loads(SECRETS.read_text())
    token = secrets["bot_token"]
    chat_id = secrets["chat_id"]

    listings = json.loads(LISTINGS.read_text())
    current_ids = {
        str(item["id"]) for item in listings
        if item.get("id")
    }

    SEEN.parent.mkdir(parents=True, exist_ok=True)

    if not SEEN.exists():
        SEEN.write_text(json.dumps(sorted(current_ids), indent=2))
        print(f"First run: saved {len(current_ids)} existing listings.")
        return

    notified = set(json.loads(SEEN.read_text()))
    new_items = [
        item for item in listings
        if item.get("id") and str(item["id"]) not in notified
    ]

    print(f"Found {len(new_items)} new listings.")

    for item in new_items:
        message = (
            f"🛒 New Marketplace Listing\n\n"
            f"{item.get('name', 'Unknown item')}\n"
            f"Price: {item.get('price', 'N/A')}\n"
            f"Location: {item.get('location', 'N/A')}\n\n"
            f"{item.get('url', '')}"
        )

        try:
            if send_message(token, chat_id, message):
                notified.add(str(item["id"]))
                SEEN.write_text(json.dumps(sorted(notified), indent=2))
                print(f"Notified: {item.get('name')}")
        except Exception as exc:
            print(f"Notification failed: {type(exc).__name__}")

if __name__ == "__main__":
    main()
