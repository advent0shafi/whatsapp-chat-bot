import requests
from django.conf import settings


class WhatsAppAPI:
    BASE_URL = "https://graph.facebook.com/v21.0"  # Update with the latest version
    TOKEN = settings.TOKEN_WHATSAPP_API
    PHONE_NUMBER_ID = "500236589835913"

    @staticmethod
    def send_message(phone_number, message, options=None):
        try:
            url = f"{WhatsAppAPI.BASE_URL}/{WhatsAppAPI.PHONE_NUMBER_ID}/messages"
            headers = {
                "Authorization": f"Bearer {WhatsAppAPI.TOKEN}",
                "Content-Type": "application/json",
            }
            print('evdie ethieee ------------------>>>>>><<<<<<-----------')
            if options:
                buttons = [
                    {"type": "reply", "reply": {"id": f"option_{i+1}", "title": option}} 
                    for i, option in enumerate(options)
                ]

                payload = {
                    "messaging_product": "whatsapp",
                    "to": phone_number,
                    "type": "interactive",
                    "interactive": {
                        "type": "button",
                        "header": {"type": "text", "text": message},
                        "body": {"text": "Choose one of the following options:"},
                        "action": {"buttons": buttons}
                    }
                }
            else:
                print('evdie ethieee ------------------>>>>>><<<<<<-----------')
                payload = {
                    "messaging_product": "whatsapp",
                    "to": phone_number,
                    "type": "text",
                    "text": {"body": message},
                    }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")
            return None

