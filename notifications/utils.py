import requests
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification, NotificationTemplate


def send_sms(phone_number, message):
    """
    Send SMS using external SMS service
    This is a placeholder implementation - replace with actual SMS service
    """
    try:
        # Example implementation for a generic SMS service
        # Replace with your preferred SMS provider (e.g., Twilio, Africa's Talking, etc.)
        
        # For development/testing, just log the SMS
        if settings.DEBUG:
            print(f"SMS to {phone_number}: {message}")
            return True
        
        # Production SMS service implementation
        # Example with a generic SMS API:
        """
        sms_data = {
            'to': phone_number,
            'message': message,
            'api_key': settings.SMS_API_KEY,
            'sender_id': settings.SMS_SENDER_ID
        }
        
        response = requests.post(
            settings.SMS_API_URL,
            json=sms_data,
            headers={'Authorization': f'Bearer {settings.SMS_API_KEY}'}
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"SMS sending failed: {response.text}")
            return False
        """
        
        # For now, return True to simulate successful SMS sending
        return True
        
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False


def send_push_notification(user, title, message, data=None):
    """
    Send push notification to user
    This is a placeholder implementation - replace with actual push notification service
    """
    try:
        # Example implementation for push notifications
        # Replace with your preferred push notification service (e.g., Firebase, OneSignal, etc.)
        
        # For development/testing, just log the push notification
        if settings.DEBUG:
            print(f"Push notification to {user.username}: {title} - {message}")
            return True
        
        # Production push notification implementation
        # Example with Firebase Cloud Messaging:
        """
        if not user.fcm_token:
            return False
        
        fcm_data = {
            'to': user.fcm_token,
            'notification': {
                'title': title,
                'body': message,
                'icon': '/static/images/logo.png',
                'click_action': '/notifications'
            },
            'data': data or {}
        }
        
        response = requests.post(
            'https://fcm.googleapis.com/fcm/send',
            json=fcm_data,
            headers={
                'Authorization': f'key={settings.FCM_SERVER_KEY}',
                'Content-Type': 'application/json'
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('success', 0) > 0
        else:
            print(f"Push notification failed: {response.text}")
            return False
        """
        
        # For now, return True to simulate successful push notification
        return True
        
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False


def send_in_app_ws(user, message, notification_id=None):
    """Broadcast a message over Channels to a user's notification group."""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user.id}",
            {
                'type': 'notification_message',
                'message': message,
                'notification_id': notification_id,
                'timestamp': ''
            }
        )
    except Exception as e:
        print(f"WS notify error: {e}")


def create_in_app_notification(recipient, subject, body, category='booking'):
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type='in_app',
        subject=subject or '',
        message=body,
        status='sent'
    )
    send_in_app_ws(recipient, body, notification_id=notification.id)
    return notification


def send_bulk_sms(phone_numbers, message):
    """
    Send bulk SMS to multiple phone numbers
    """
    try:
        success_count = 0
        failed_count = 0
        
        for phone_number in phone_numbers:
            if send_sms(phone_number, message):
                success_count += 1
            else:
                failed_count += 1
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'total_count': len(phone_numbers)
        }
        
    except Exception as e:
        print(f"Error sending bulk SMS: {e}")
        return {
            'success_count': 0,
            'failed_count': len(phone_numbers),
            'total_count': len(phone_numbers),
            'error': str(e)
        }


def send_bulk_push_notifications(users, title, message, data=None):
    """
    Send bulk push notifications to multiple users
    """
    try:
        success_count = 0
        failed_count = 0
        
        for user in users:
            if send_push_notification(user, title, message, data):
                success_count += 1
            else:
                failed_count += 1
        
        return {
            'success_count': success_count,
            'failed_count': failed_count,
            'total_count': len(users)
        }
        
    except Exception as e:
        print(f"Error sending bulk push notifications: {e}")
        return {
            'success_count': 0,
            'failed_count': len(users),
            'total_count': len(users),
            'error': str(e)
        }


def validate_phone_number(phone_number):
    """
    Validate phone number format
    """
    import re
    
    # Remove any non-digit characters except +
    cleaned_number = re.sub(r'[^\d+]', '', phone_number)
    
    # Check if it's a valid phone number format
    # This is a basic validation - you might want to use a more robust library
    if cleaned_number.startswith('+'):
        # International format
        if len(cleaned_number) >= 10 and len(cleaned_number) <= 15:
            return cleaned_number
    else:
        # Local format (assuming Kenya)
        if len(cleaned_number) == 9 and cleaned_number.startswith(('7', '1')):
            return f"+254{cleaned_number}"
        elif len(cleaned_number) == 10 and cleaned_number.startswith('0'):
            return f"+254{cleaned_number[1:]}"
    
    return None


def format_phone_number(phone_number, country_code='+254'):
    """
    Format phone number to standard format
    """
    import re
    
    # Remove any non-digit characters
    digits_only = re.sub(r'[^\d]', '', phone_number)
    
    if len(digits_only) == 9:
        # Local format (7xxxxxxxx)
        return f"{country_code}{digits_only}"
    elif len(digits_only) == 10 and digits_only.startswith('0'):
        # Local format with leading 0 (07xxxxxxxx)
        return f"{country_code}{digits_only[1:]}"
    elif len(digits_only) == 12 and digits_only.startswith('254'):
        # Already in international format
        return f"+{digits_only}"
    else:
        # Return as is if format is unclear
        return phone_number


def get_sms_balance():
    """
    Get SMS balance from service provider
    """
    try:
        # Example implementation - replace with actual SMS service API
        """
        response = requests.get(
            f"{settings.SMS_API_URL}/balance",
            headers={'Authorization': f'Bearer {settings.SMS_API_KEY}'}
        )
        
        if response.status_code == 200:
            return response.json().get('balance', 0)
        else:
            return None
        """
        
        # Placeholder return
        return 1000
        
    except Exception as e:
        print(f"Error getting SMS balance: {e}")
        return None


def get_sms_delivery_status(message_id):
    """
    Get SMS delivery status
    """
    try:
        # Example implementation - replace with actual SMS service API
        """
        response = requests.get(
            f"{settings.SMS_API_URL}/status/{message_id}",
            headers={'Authorization': f'Bearer {settings.SMS_API_KEY}'}
        )
        
        if response.status_code == 200:
            return response.json().get('status', 'unknown')
        else:
            return 'unknown'
        """
        
        # Placeholder return
        return 'delivered'
        
    except Exception as e:
        print(f"Error getting SMS delivery status: {e}")
        return 'unknown'
