import requests
from config import BOT_TOKEN, CHAT_ID
from datetime import datetime


def send_alert(image_path, person_count):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    caption = (
        f"🚨 Guardian AI Alert\n\n"
        f"👤 Persons Detected : {person_count}\n\n"
        f"📅 Time : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
    )

    with open(image_path, "rb") as photo:

        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": caption
            },
            files={
                "photo": photo
            }
        )

    if response.status_code == 200:
        print("Telegram Alert Sent ✅")
    else:
        print(f"Telegram Error: {response.text}")
