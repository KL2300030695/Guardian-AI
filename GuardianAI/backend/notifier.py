"""
notifier.py — Guardian AI Telegram Alert (Phase 11)
────────────────────────────────────────────────────
Phase 11: Alert message now includes camera name + location.
"""

import requests
from config import BOT_TOKEN, CHAT_ID
from datetime import datetime


def send_alert(
    image_path:      str,
    person_count:    int,
    camera_name:     str = "Camera",
    camera_location: str = "",
) -> bool:
    """
    Send a Telegram photo alert with camera details.

    Returns True on success, False on failure.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    # Build location string
    loc_str = f" ({camera_location})" if camera_location else ""

    caption = (
        f"🚨 Guardian AI — Unknown Person Detected!\n\n"
        f"📍 Camera : {camera_name}{loc_str}\n"
        f"👤 Persons : {person_count}\n"
        f"🕒 Time   : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
    )

    try:
        with open(image_path, "rb") as photo:
            response = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "caption": caption,
                },
                files={"photo": photo},
                timeout=10,
            )

        if response.status_code == 200:
            print(f"[Telegram] Alert sent ✅ — {camera_name}")
            return True
        else:
            print(f"[Telegram] Error: {response.text}")
            return False

    except Exception as e:
        print(f"[Telegram] Exception: {e}")
        return False
