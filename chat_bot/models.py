from django.db import models

# Create your models here.
from django.db import models

class UserInteraction(models.Model):
    phone_number = models.CharField(max_length=15)
    user_message = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class RoomBooking(models.Model):
    phone_number = models.CharField(max_length=15)
    room_type = models.CharField(max_length=50)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    num_guests = models.IntegerField()
    special_requests = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
