from django.urls import path
from . import views

app_name = 'pricing'

urlpatterns = [
    path('test-price/<int:equipment_id>/', views.test_price, name='test_price'),
]
