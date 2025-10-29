# AgroHire - Agricultural Equipment Rental Platform

A comprehensive Django-based web application for hiring agricultural equipment. The platform connects farmers with equipment owners, providing a seamless booking, payment, and management system.

## Features

### Core Functionality
- **User Management**: Role-based access (Farmers, Equipment Owners, Admins)
- **Equipment Management**: Comprehensive equipment listings with images, specifications, and availability
- **Booking System**: Advanced booking with conflict detection and scheduling
- **Dynamic Pricing**: Seasonal and demand-based pricing algorithms
- **Payment Processing**: M-Pesa integration for mobile payments
- **Real-time Notifications**: Email, SMS, and push notifications
- **Review System**: Equipment and service ratings

### Technical Features
- **RESTful API**: Complete API for frontend integration
- **Real-time Updates**: WebSocket support for live notifications
- **Background Tasks**: Celery for automated tasks and notifications
- **Admin Interface**: Comprehensive Django admin for management
- **Mobile Responsive**: Designed for mobile and web access

## Technology Stack

- **Backend**: Django 5.2.5, Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production)
- **Task Queue**: Celery with Redis
- **Real-time**: Django Channels
- **Payment**: M-Pesa API integration
- **Notifications**: Email, SMS, Push notifications
- **Frontend**: REST API ready for React/Vue integration

## Installation

### Prerequisites
- Python 3.10+
- Redis server
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agrohire
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   DATABASE_URL=sqlite:///db.sqlite3
   
   # M-Pesa Configuration
   MPESA_CONSUMER_KEY=your_mpesa_consumer_key
   MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret
   MPESA_BUSINESS_SHORT_CODE=your_business_shortcode
   MPESA_PASSKEY=your_mpesa_passkey
   MPESA_ENVIRONMENT=sandbox
   
   # Redis Configuration
   REDIS_URL=redis://localhost:6379/0
   
   # Email Configuration
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

5. **Run database migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Redis server**
   ```bash
   redis-server
   ```

8. **Start Celery worker (in a new terminal)**
   ```bash
   celery -A agrohire worker -l info
   ```

9. **Start Celery beat (in another terminal)**
   ```bash
   celery -A agrohire beat -l info
   ```

10. **Run the development server**
    ```bash
    python manage.py runserver
    ```

## Project Structure

```
agrohire/
├── agrohire/                 # Main project settings
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── celery.py            # Celery configuration
│   └── asgi.py              # ASGI configuration
├── users/                   # User management app
│   ├── models.py            # Custom User model
│   ├── admin.py             # Admin interface
│   └── urls.py              # User API endpoints
├── equipment/               # Equipment management app
│   ├── models.py            # Equipment models
│   ├── admin.py             # Equipment admin
│   └── urls.py              # Equipment API endpoints
├── bookings/                # Booking system app
│   ├── models.py            # Booking models
│   └── urls.py              # Booking API endpoints
├── pricing/                 # Dynamic pricing app
│   ├── models.py            # Pricing models
│   ├── tasks.py             # Celery tasks
│   └── urls.py              # Pricing API endpoints
├── payments/                # Payment processing app
│   ├── models.py            # Payment models
│   ├── api.py               # M-Pesa integration
│   └── urls.py              # Payment API endpoints
├── notifications/           # Notification system app
│   ├── models.py            # Notification models
│   ├── tasks.py             # Notification tasks
│   ├── utils.py             # SMS/Push utilities
│   └── urls.py              # Notification API endpoints
├── static/                  # Static files
├── media/                   # User uploaded files
├── templates/               # HTML templates
├── requirements.txt         # Python dependencies
└── README.md               # This file
```


### Key API Endpoints

- **Users**: `/api/users/`
- **Equipment**: `/api/equipment/`
- **Bookings**: `/api/bookings/`
- **Payments**: `/api/payments/`
- **Notifications**: `/api/notifications/`

## Admin Interface

Access the Django admin interface at `/admin/` to manage:
- Users and user profiles
- Equipment and equipment types
- Bookings and schedules
- Pricing rules and history
- Payments and transactions
- Notifications and templates

## Configuration

### Production Settings

For production deployment, update `settings.py`:

1. **Database**: Switch to PostgreSQL
2. **Static Files**: Configure static file serving
3. **Security**: Set `DEBUG=False` and configure `ALLOWED_HOSTS`
4. **Email**: Configure production email settings
5. **M-Pesa**: Switch to live environment

### Environment Variables

Key environment variables to configure:

- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `MPESA_*`: M-Pesa API credentials
- `EMAIL_*`: Email configuration

## Celery Tasks

The platform uses Celery for background tasks:

- **Dynamic Pricing**: Hourly pricing updates
- **Notifications**: Automated email/SMS sending
- **Maintenance Alerts**: Equipment maintenance reminders
- **Booking Reminders**: Upcoming booking notifications
- **Payment Reminders**: Pending payment notifications

## Payment Integration

### M-Pesa Integration

The platform integrates with M-Pesa for mobile payments:

1. **STK Push**: Initiate payment requests
2. **Callbacks**: Handle payment confirmations
3. **Refunds**: Process payment refunds
4. **Transaction Logging**: Track all payment activities

### Configuration

Update M-Pesa settings in `settings.py`:
```python
MPESA_CONSUMER_KEY = 'your_consumer_key'
MPESA_CONSUMER_SECRET = 'your_consumer_secret'
MPESA_BUSINESS_SHORT_CODE = 'your_shortcode'
MPESA_PASSKEY = 'your_passkey'
MPESA_ENVIRONMENT = 'sandbox'  # or 'live'
```

## Notification System

### Types of Notifications

- **Email**: Booking confirmations, payment receipts
- **SMS**: Urgent alerts, booking reminders
- **Push**: Real-time updates, status changes
- **In-App**: System notifications, updates

### Configuration

Configure notification preferences in the admin interface or via API.

## Development

### Running Tests
```bash
python manage.py test
```

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up static file serving
- [ ] Configure email settings
- [ ] Set up SSL/HTTPS
- [ ] Configure M-Pesa live credentials
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy



### Planned Features
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Equipment maintenance scheduling
- [ ] Insurance integration
- [ ] Multi-language support
- [ ] Advanced search and filtering
- [ ] Equipment tracking (GPS)
- [ ] Weather integration
- [ ] Crop-specific recommendations
- [ ] Financial reporting
