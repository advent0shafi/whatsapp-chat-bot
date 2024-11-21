from django.contrib import admin
from django.urls import path
from .views import SendMessageView,WhatsAppWebhookView


urlpatterns = [
    path('send-message/', SendMessageView.as_view(), name='send-message'),
    path('webhook/', WhatsAppWebhookView.as_view(), name='webhook'),  # Trailing slash is critical
]

