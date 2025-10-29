import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrohire.settings')

app = Celery('agrohire')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# Celery Beat Schedule
app.conf.beat_schedule = {
    'check-maintenance-schedule': {
        'task': 'equipment.tasks.check_maintenance_schedule',
        'schedule': 3600.0,  # Every hour
    },
    'update-dynamic-pricing': {
        'task': 'pricing.tasks.update_dynamic_pricing',
        'schedule': 3600.0,  # Every hour
    },
    'send-pending-notifications': {
        'task': 'notifications.tasks.send_pending_notifications',
        'schedule': 300.0,  # Every 5 minutes
    },
    'cleanup-expired-bookings': {
        'task': 'bookings.tasks.cleanup_expired_bookings',
        'schedule': 86400.0,  # Daily
    },
    'generate-daily-reports': {
        'task': 'reports.tasks.generate_daily_reports',
        'schedule': 86400.0,  # Daily at midnight
    },
}
