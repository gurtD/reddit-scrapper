import os
from twilio.rest import Client

def send(message):
    account_sid = os.getenv("TWILIO_SID")
    auth_token = os.getenv("TWILIO_AUTH")
    client = Client(account_sid, auth_token)

    message = client.messages \
                    .create(
                        body=message,
                        from_=os.getenv("FROM_PHONE_NUMBER"),
                        to=os.getenv("TO_PHONE_NUMBER")
                    )

    print(message.sid)