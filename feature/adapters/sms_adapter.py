from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from typing import Optional
import os
from dotenv import load_dotenv


class SMSAdapter:
    def __init__(self):
        load_dotenv()
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER')

        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Missing Twilio credentials. Please check your .env file")

        self.client = Client(self.account_sid, self.auth_token)

    def send_sms(self, to_number: str, message: str) -> Optional[str]:
        try:
            message = self.client.messages.create(
                from_=self.from_number,
                body=message,
                to=to_number
            )
            return message.sid
        except TwilioRestException as e:
            print(f"Error sending SMS: {str(e)}")
            return None

    @staticmethod
    def format_otp_message(otp: str) -> str:
        return f"Your verification code is: {otp}. Valid for 5 minutes."