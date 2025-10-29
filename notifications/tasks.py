from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Notification, NotificationTemplate, NotificationPreference
from .utils import send_sms, send_push_notification


@shared_task
def send_pending_notifications():
    """
    Send all pending notifications
    """
    try:
        pending_notifications = Notification.objects.filter(
            status='pending'
        ).select_related('recipient', 'template')
        
        sent_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                # Check user preferences
                preferences = get_user_preferences(notification.recipient)
                
                if not preferences.should_send_notification(
                    notification.notification_type, 
                    notification.template.category if notification.template else 'system'
                ):
                    notification.status = 'cancelled'
                    notification.save()
                    continue
                
                # Check quiet hours
                if preferences.is_in_quiet_hours():
                    # Skip sending during quiet hours (except urgent notifications)
                    if notification.template and notification.template.priority != 'urgent':
                        continue
                
                # Send notification based on type
                success = send_notification(notification)
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                notification.mark_as_failed(str(e))
                failed_count += 1
        
        return f"Sent {sent_count} notifications, {failed_count} failed"
        
    except Exception as e:
        return f"Error sending notifications: {str(e)}"


@shared_task
def send_notification_task(notification_id):
    """
    Send a specific notification
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        success = send_notification(notification)
        
        if success:
            return f"Successfully sent notification {notification_id}"
        else:
            return f"Failed to send notification {notification_id}"
            
    except Notification.DoesNotExist:
        return f"Notification {notification_id} not found"
    except Exception as e:
        return f"Error sending notification {notification_id}: {str(e)}"


@shared_task
def send_bulk_notifications(notification_type, template_id, user_ids, context_data=None):
    """
    Send bulk notifications to multiple users
    """
    try:
        template = NotificationTemplate.objects.get(id=template_id)
        
        if context_data is None:
            context_data = {}
        
        # Render template
        rendered_content = template.render_template(context_data)
        
        created_count = 0
        for user_id in user_ids:
            try:
                notification = Notification.objects.create(
                    recipient_id=user_id,
                    notification_type=notification_type,
                    template=template,
                    subject=rendered_content.get('subject', ''),
                    message=rendered_content.get('body', ''),
                    sms_message=rendered_content.get('sms_body', '')
                )
                created_count += 1
                
                # Send immediately
                send_notification_task.delay(notification.id)
                
            except Exception as e:
                print(f"Error creating notification for user {user_id}: {e}")
        
        return f"Created {created_count} notifications"
        
    except NotificationTemplate.DoesNotExist:
        return f"Template {template_id} not found"
    except Exception as e:
        return f"Error sending bulk notifications: {str(e)}"


@shared_task
def send_booking_reminders():
    """
    Send reminders for upcoming bookings
    """
    try:
        from bookings.models import Booking
        from datetime import timedelta
        
        # Get bookings starting in the next 24 hours
        tomorrow = timezone.now() + timedelta(days=1)
        upcoming_bookings = Booking.objects.filter(
            start_date__date=tomorrow.date(),
            status='confirmed'
        ).select_related('user', 'equipment')
        
        sent_count = 0
        for booking in upcoming_bookings:
            try:
                # Create reminder notification
                context_data = {
                    'user_name': booking.user.get_full_name(),
                    'equipment_name': booking.equipment.name,
                    'booking_date': booking.start_date.strftime('%Y-%m-%d'),
                    'booking_time': booking.start_date.strftime('%H:%M'),
                    'booking_number': booking.booking_number
                }
                
                # Send email reminder
                send_booking_reminder_email.delay(booking.id, context_data)
                
                # Send SMS reminder
                send_booking_reminder_sms.delay(booking.id, context_data)
                
                sent_count += 1
                
            except Exception as e:
                print(f"Error sending reminder for booking {booking.id}: {e}")
        
        return f"Sent {sent_count} booking reminders"
        
    except Exception as e:
        return f"Error sending booking reminders: {str(e)}"


@shared_task
def send_payment_reminders():
    """
    Send reminders for pending payments
    """
    try:
        from payments.models import Payment
        
        # Get pending payments older than 24 hours
        yesterday = timezone.now() - timedelta(days=1)
        pending_payments = Payment.objects.filter(
            status='pending',
            created_at__lt=yesterday
        ).select_related('user', 'booking')
        
        sent_count = 0
        for payment in pending_payments:
            try:
                context_data = {
                    'user_name': payment.user.get_full_name(),
                    'amount': payment.amount,
                    'payment_number': payment.payment_number,
                    'booking_number': payment.booking.booking_number
                }
                
                # Send payment reminder
                send_payment_reminder_email.delay(payment.id, context_data)
                send_payment_reminder_sms.delay(payment.id, context_data)
                
                sent_count += 1
                
            except Exception as e:
                print(f"Error sending payment reminder for payment {payment.id}: {e}")
        
        return f"Sent {sent_count} payment reminders"
        
    except Exception as e:
        return f"Error sending payment reminders: {str(e)}"


@shared_task
def send_maintenance_alerts():
    """
    Send maintenance alerts for equipment
    """
    try:
        from equipment.models import Equipment
        
        # Get equipment that needs maintenance
        equipment_needing_maintenance = Equipment.objects.filter(
            is_active=True,
            next_maintenance_date__lte=timezone.now().date()
        ).select_related('owner')
        
        sent_count = 0
        for equipment in equipment_needing_maintenance:
            try:
                context_data = {
                    'owner_name': equipment.owner.get_full_name(),
                    'equipment_name': equipment.name,
                    'maintenance_date': equipment.next_maintenance_date.strftime('%Y-%m-%d')
                }
                
                # Send maintenance alert
                send_maintenance_alert_email.delay(equipment.id, context_data)
                send_maintenance_alert_sms.delay(equipment.id, context_data)
                
                sent_count += 1
                
            except Exception as e:
                print(f"Error sending maintenance alert for equipment {equipment.id}: {e}")
        
        return f"Sent {sent_count} maintenance alerts"
        
    except Exception as e:
        return f"Error sending maintenance alerts: {str(e)}"


@shared_task
def send_booking_reminder_email(booking_id, context_data):
    """
    Send booking reminder email
    """
    try:
        from bookings.models import Booking
        
        booking = Booking.objects.get(id=booking_id)
        
        subject = f"Reminder: Your equipment booking tomorrow - {booking.booking_number}"
        message = f"""
        Dear {booking.user.get_full_name()},
        
        This is a reminder that you have an equipment booking tomorrow:
        
        Equipment: {booking.equipment.name}
        Date: {booking.start_date.strftime('%Y-%m-%d')}
        Time: {booking.start_date.strftime('%H:%M')}
        Booking Number: {booking.booking_number}
        
        Please ensure you're available at the scheduled time.
        
        Best regards,
        AgroHire Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            fail_silently=False
        )
        
        return f"Sent booking reminder email for booking {booking_id}"
        
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"
    except Exception as e:
        return f"Error sending booking reminder email: {str(e)}"


@shared_task
def send_booking_reminder_sms(booking_id, context_data):
    """
    Send booking reminder SMS
    """
    try:
        from bookings.models import Booking
        
        booking = Booking.objects.get(id=booking_id)
        
        message = f"Reminder: Your {booking.equipment.name} booking is tomorrow at {booking.start_date.strftime('%H:%M')}. Booking: {booking.booking_number}"
        
        if booking.user.phone_number:
            success = send_sms(booking.user.phone_number, message)
            if success:
                return f"Sent booking reminder SMS for booking {booking_id}"
            else:
                return f"Failed to send booking reminder SMS for booking {booking_id}"
        else:
            return f"No phone number for user {booking.user.id}"
        
    except Booking.DoesNotExist:
        return f"Booking {booking_id} not found"
    except Exception as e:
        return f"Error sending booking reminder SMS: {str(e)}"


@shared_task
def send_payment_reminder_email(payment_id, context_data):
    """
    Send payment reminder email
    """
    try:
        from payments.models import Payment
        
        payment = Payment.objects.get(id=payment_id)
        
        subject = f"Payment Reminder - {payment.payment_number}"
        message = f"""
        Dear {payment.user.get_full_name()},
        
        This is a reminder that you have a pending payment:
        
        Amount: KES {payment.amount}
        Payment Number: {payment.payment_number}
        Booking Number: {payment.booking.booking_number}
        
        Please complete your payment to confirm your booking.
        
        Best regards,
        AgroHire Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[payment.user.email],
            fail_silently=False
        )
        
        return f"Sent payment reminder email for payment {payment_id}"
        
    except Payment.DoesNotExist:
        return f"Payment {payment_id} not found"
    except Exception as e:
        return f"Error sending payment reminder email: {str(e)}"


@shared_task
def send_payment_reminder_sms(payment_id, context_data):
    """
    Send payment reminder SMS
    """
    try:
        from payments.models import Payment
        
        payment = Payment.objects.get(id=payment_id)
        
        message = f"Payment reminder: KES {payment.amount} pending for booking {payment.booking.booking_number}. Please complete payment."
        
        if payment.user.phone_number:
            success = send_sms(payment.user.phone_number, message)
            if success:
                return f"Sent payment reminder SMS for payment {payment_id}"
            else:
                return f"Failed to send payment reminder SMS for payment {payment_id}"
        else:
            return f"No phone number for user {payment.user.id}"
        
    except Payment.DoesNotExist:
        return f"Payment {payment_id} not found"
    except Exception as e:
        return f"Error sending payment reminder SMS: {str(e)}"


@shared_task
def send_maintenance_alert_email(equipment_id, context_data):
    """
    Send maintenance alert email
    """
    try:
        from equipment.models import Equipment
        
        equipment = Equipment.objects.get(id=equipment_id)
        
        subject = f"Maintenance Alert - {equipment.name}"
        message = f"""
        Dear {equipment.owner.get_full_name()},
        
        Your equipment requires maintenance:
        
        Equipment: {equipment.name}
        Maintenance Date: {equipment.next_maintenance_date.strftime('%Y-%m-%d')}
        
        Please schedule maintenance to ensure your equipment remains in good condition.
        
        Best regards,
        AgroHire Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[equipment.owner.email],
            fail_silently=False
        )
        
        return f"Sent maintenance alert email for equipment {equipment_id}"
        
    except Equipment.DoesNotExist:
        return f"Equipment {equipment_id} not found"
    except Exception as e:
        return f"Error sending maintenance alert email: {str(e)}"


@shared_task
def send_maintenance_alert_sms(equipment_id, context_data):
    """
    Send maintenance alert SMS
    """
    try:
        from equipment.models import Equipment
        
        equipment = Equipment.objects.get(id=equipment_id)
        
        message = f"Maintenance alert: {equipment.name} requires maintenance on {equipment.next_maintenance_date.strftime('%Y-%m-%d')}."
        
        if equipment.owner.phone_number:
            success = send_sms(equipment.owner.phone_number, message)
            if success:
                return f"Sent maintenance alert SMS for equipment {equipment_id}"
            else:
                return f"Failed to send maintenance alert SMS for equipment {equipment_id}"
        else:
            return f"No phone number for equipment owner {equipment.owner.id}"
        
    except Equipment.DoesNotExist:
        return f"Equipment {equipment_id} not found"
    except Exception as e:
        return f"Error sending maintenance alert SMS: {str(e)}"


def send_notification(notification):
    """
    Send a notification based on its type
    """
    try:
        if notification.notification_type == 'email':
            return send_email_notification(notification)
        elif notification.notification_type == 'sms':
            return send_sms_notification(notification)
        elif notification.notification_type == 'push':
            return send_push_notification_task(notification)
        elif notification.notification_type == 'in_app':
            return send_in_app_notification(notification)
        else:
            notification.mark_as_failed("Unknown notification type")
            return False
            
    except Exception as e:
        notification.mark_as_failed(str(e))
        return False


def send_email_notification(notification):
    """
    Send email notification
    """
    try:
        if not notification.recipient.email:
            notification.mark_as_failed("No email address")
            return False
        
        send_mail(
            subject=notification.subject,
            message=notification.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False
        )
        
        notification.mark_as_sent()
        return True
        
    except Exception as e:
        notification.mark_as_failed(str(e))
        return False


def send_sms_notification(notification):
    """
    Send SMS notification
    """
    try:
        if not notification.recipient.phone_number:
            notification.mark_as_failed("No phone number")
            return False
        
        message = notification.sms_message or notification.message
        success = send_sms(notification.recipient.phone_number, message)
        
        if success:
            notification.mark_as_sent()
            return True
        else:
            notification.mark_as_failed("SMS sending failed")
            return False
            
    except Exception as e:
        notification.mark_as_failed(str(e))
        return False


def send_push_notification_task(notification):
    """
    Send push notification
    """
    try:
        message = notification.sms_message or notification.message
        success = send_push_notification(notification.recipient, notification.subject, message)
        
        if success:
            notification.mark_as_sent()
            return True
        else:
            notification.mark_as_failed("Push notification sending failed")
            return False
            
    except Exception as e:
        notification.mark_as_failed(str(e))
        return False


def send_in_app_notification(notification):
    """
    Send in-app notification
    """
    try:
        # For in-app notifications, we just mark them as sent
        # The frontend will fetch and display them
        notification.mark_as_sent()
        return True
        
    except Exception as e:
        notification.mark_as_failed(str(e))
        return False


def get_user_preferences(user):
    """
    Get user notification preferences, create default if not exists
    """
    try:
        return user.notification_preferences
    except NotificationPreference.DoesNotExist:
        return NotificationPreference.objects.create(user=user)
