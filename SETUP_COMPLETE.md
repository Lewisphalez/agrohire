### Home Page
- **URL**: http://localhost:8000/
- **Features**: Modern landing page with equipment showcase

### Admin Interface
- **URL**: http://localhost:8000/admin/
- **Admin Credentials**: 
  - Username: `admin`
  - Password: `admin123`

### Equipment Owner Account
- **Username**: `equipment_owner`
- **Password**: `password123`


### Equipment Types
- Tractor (Base rate: KES 5,000/day)
- Harvester (Base rate: KES 8,000/day)
- Planter (Base rate: KES 3,000/day)
- Irrigation System (Base rate: KES 2,000/day)


### Users
- Admin user with full access
- Equipment owner with sample equipment

### 3. Configure External Services
- **M-Pesa**: Update credentials in settings.py for payment processing
- **Email**: Configure SMTP settings for email notifications
- **SMS**: Integrate with SMS service provider
- **Push Notifications**: Set up Firebase or similar service

### 4. Start Background Services
```bash
# Start Redis server
redis-server

# Start Celery worker (in new terminal)
celery -A agrohire worker -l info

# Start Celery beat (in another terminal)
celery -A agrohire beat -l info
```

## 🛠 Development Commands

### Database Operations
```bash
# Create new migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py create_sample_data
```

### Server Management
```bash
# Start development server
python manage.py runserver

# Start with specific port
python manage.py runserver 0.0.0.0:8000
```

### Celery Tasks
```bash
# Start worker
celery -A agrohire worker -l info

# Start beat scheduler
celery -A agrohire beat -l info

# Monitor tasks
celery -A agrohire flower
```