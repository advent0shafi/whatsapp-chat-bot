from datetime import datetime
import traceback
from django.shortcuts import render
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import WhatsAppAPI
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse, HttpResponse
from django.views import View
import os
from django.conf import settings
from groq import Groq
from .models import RoomBooking, UserInteraction



# API View for sending WhatsApp message
class SendMessageView(APIView):
    def post(self, request):
        options = ["Option 1: Get Info", "Option 2: Support", "Option 3: Contact Us"]
        phone_number = request.data.get("phone_number")
        message = request.data.get("message")
        
        if not phone_number or not message:
            return Response({"error": "Phone number and message are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Sending message with options
        response = WhatsAppAPI.send_message(phone_number, message,options)
        return Response(response)




# Your verify token set in the Facebook Developer console
VERIFY_TOKEN = "537hbfhjsdbfjhbsduhfbwergu"



# Models (Ensure these are implemented in your project)
# from your_app.models import UserInteraction, RoomBooking

class WhatsAppWebhookView(APIView):
    @method_decorator(csrf_exempt)  # Exempt from CSRF protection
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        """Verify the webhook with Facebook"""
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)  # Respond with the challenge token
        return HttpResponse("Forbidden", status=403)

    def post(self, request):
        try:
            data = json.loads(request.body)
            print("Webhook Data:", data)  # Log incoming data for debugging

            # Process incoming messages
            if "entry" in data and data["entry"]:
                for entry in data["entry"]:
                    if "changes" in entry and entry["changes"]:
                        for change in entry["changes"]:
                            if "value" in change and "messages" in change["value"]:
                                messages = change["value"]["messages"]
                                for message in messages:
                                    sender = message.get("from")  # Sender's phone number
                                    text = message.get("text", {}).get("body", "")
                                    print(f"Message from {sender}: {text}")
                                    
                                    # Initialize a combined message with the text from the message
                                    combined_message = text

                                    # Check if the message is a button reply
                                    if 'interactive' in message and 'button_reply' in message['interactive']:
                                        button_reply = message['interactive']['button_reply']
                                        button_id = button_reply.get('id')  # Button ID
                                        button_title = button_reply.get('title')  # Button Title
                                        print(f"Button Reply from {sender}: ID={button_id}, Title={button_title}")

                                        # Add the button reply title to the combined message
                                        combined_message += f" (Button Reply: {button_title})"
                                        
                                    # Handle the combined message with both the text and button reply
                                    response = self.handle_message(sender, combined_message)
                                    return Response(response)

            return Response({"status": "received"}, status=200)
        except Exception as e:
            print("Error processing webhook:", traceback.format_exc())
            return Response({"error": str(e)}, status=500)
    
    def handle_message(self, sender, text):
        """Determine appropriate response based on user input"""
        handlers = {
            "greeting": self.handle_greeting,
            "book_rooms": self.handle_book_room,
            "room_selection": self.handle_room_selection,
            "check_in_date": self.handle_check_in_date,
            "num_guests": self.handle_num_guests,
            "customer_name": self.handle_customer_name,
        }

        # Simplify input handling
        text_lower = text.strip().lower()
        print(text_lower, 'user input')

        # Check for specific commands or keywords
        if any(greeting in text_lower for greeting in ["hi", "hello", "hey"]):
            return handlers["greeting"](sender)
        elif any(room_command in text_lower for room_command in ["book a room", "book"]):
            return handlers["book_rooms"](sender)
        elif any(room in text_lower for room in ["deluxe room", "king room", "executive room", "suite room"]):
            return handlers["room_selection"](sender, text)
        elif any(date in text_lower for date in ["15th dec", "16th dec", "17th dec"]):
            return handlers["check_in_date"](sender, text)
        elif any(guest in text_lower for guest in ["1 adult", "2 adults", "3 adults"]):
            return handlers["num_guests"](sender, text)
        elif text_lower:  # Handle customer name as a fallback
            return handlers["customer_name"](sender, text)
        else:
            return self.handle_fallback(sender)

    def handle_greeting(self, sender):
        """Send greeting message"""
        message = "Hi! Welcome to Liwa Hotel. How can I assist you today?"
        options = ["book a room"]
        return WhatsAppAPI.send_message(sender, message, options)

    def handle_book_room(self, sender):
        """Handle room booking initiation"""
        room_options = ["Deluxe Room", "King Room", "Executive Room"]
        message = "Please select a room type:"
        WhatsAppAPI.send_message(sender, message, room_options)

    def handle_room_selection(self, sender, text):
        """Handle room type selection"""
        message = "Please select your check-in date:"
        options = ["15th Dec", "16th Dec", "17th Dec"]
        UserInteraction.objects.create(phone_number=sender, user_message=text, bot_response=message)
        WhatsAppAPI.send_message(sender, message, options)

    def handle_check_in_date(self, sender, text):
        """Handle check-in date selection"""
        message = "How many guests will be staying?"
        options = ["1 Adult", "2 Adults", "3 Adults"]
        WhatsAppAPI.send_message(sender, message, options)

    def handle_num_guests(self, sender, text):
        """Handle number of guests"""
        message = "Please provide your name."
        options = []  # No options needed for name input
        WhatsAppAPI.send_message(sender, message, options)

    def handle_customer_name(self, sender, text):
        """Handle customer name collection"""
        # Here, you store the user's name
        user_name = text.strip()
        UserInteraction.objects.create(phone_number=sender, user_message="Name: " + user_name, bot_response="Name collected.")
        
        # Send confirmation and finalize the booking
        message = f"Thank you, {user_name}! Your booking is on excutive he will contact you! We look forward to your stay at Liwa Hotels."
        options = []
        WhatsAppAPI.send_message(sender, message, options)

    def handle_fallback(self, sender):
        """Handle unrecognized inputs"""
        message = "Sorry, I didn't understand that. How can I assist you?"
        options = ["Hi", "Book a Room"]
        return WhatsAppAPI.send_message(sender, message, options)
    


def sendReply(phone_numb,text):
    
    phone_number = phone_numb
    message=messageAireading(text)
    if not phone_number or not message:
            return print({"error": "Phone number and message are required"}, status=status.HTTP_400_BAD_REQUEST)
    response = WhatsAppAPI.send_message(phone_number, message)
    return print(response)
    


def messaManualMode(phone_numb, text):
    phone_number = phone_numb
    options = []

    # Initial options for the user
    if text.lower() == "book a room":
        message = "Sure! Please select a room type:\n1. Deluxe Room\n2. Suite\n3. Standard Room"
        options = ["Deluxe Room", "Suite", "Standard Room"]
    elif text.lower() in ["deluxe room", "suite", "standard room"]:
        # Save room type and ask for check-in date
        RoomBooking.objects.create(phone_number=phone_number, room_type=text)
        message = f"You selected {text}. Please provide your check-in date (YYYY-MM-DD):"
    elif is_valid_date(text):  # Check if the input is a valid date
        booking = RoomBooking.objects.filter(phone_number=phone_number).latest('timestamp')
        if not booking.check_in_date:
            booking.check_in_date = text
            booking.save()
            message = "Check-in date saved! Please provide your check-out date (YYYY-MM-DD):"
        else:
            booking.check_out_date = text
            booking.save()
            message = "Check-out date saved! How many guests are staying?"
    elif text.isdigit():  # Number of guests
        booking = RoomBooking.objects.filter(phone_number=phone_number).latest('timestamp')
        booking.num_guests = int(text)
        booking.save()
        message = "Booking almost complete! Any special requests? (Type 'No' if none)"
    elif text.lower() == "no":
        booking = RoomBooking.objects.filter(phone_number=phone_number).latest('timestamp')
        message = f"Thank you! Your booking for a {booking.room_type} is confirmed. Check-in: {booking.check_in_date}, Check-out: {booking.check_out_date}, Guests: {booking.num_guests}."
        options = []  # No buttons
    else:
        message = "Invalid input. Please try again."

    # If options are empty, you can add a default one-button message
    if not options:
        options = ["OK"]

    # Save user interaction
    UserInteraction.objects.create(phone_number=phone_number, user_message=text, bot_response=message)

    # Send the message with or without options
    response = WhatsAppAPI.send_message(phone_number, message, options)
    print(response)
    return response


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def messageAireading(textMessage):
    # Get or set the API key
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise ValueError("API key not found. Ensure it's set in your .env file.")

    # Create a client
    client = Groq()

    # Define the model
    model = "llama-3.1-8b-instant"

    # Dummy data for room availability
    hotel_info = """
    Liwa Hotels is known for its luxurious rooms and exceptional service.
    Room availability:
    - Golden Suite: 3 rooms available - 3000rs
    - Silver Suite: 5 rooms available - 9000 rs
    - Platinum Suite: 2 rooms available -50000 rs
Address: Yashoda Nagar, Yelahanka, Bengaluru, Karnataka 560064
Phone: 096861 12345
Website Link :https://www.liwaahotels.com
    """

    # Define the conversation with system instructions
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant specializing in providing details about Liwa Hotels and assisting with room bookings. "
                "Respond to the user as a hotel booking assistant, following these steps:\n"
                "1. Greet the user and offer to assist with booking a room.\n"
                "2. Ask for the check-in date.\n"
                "3. Ask how many guests will be staying.\n"
                "4. Ask for the guest's name.\n"
                "5. Confirm the booking for the selected check-in date and number of guests.\n"
                "Do not answer queries unrelated to Liwa Hotels. "
                "Always respond with humility and professionalism."
            )
        },
        {
            "role": "assistant",
            "content": hotel_info
        },
        {
            "role": "user",
            "content": textMessage
        }
    ]

    # Send the message and get the response
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=0.7,
        max_tokens=1000,
    )

    # Return the response
    return chat_completion.choices[0].message.content