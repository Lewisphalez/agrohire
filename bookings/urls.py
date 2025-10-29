from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('bookings/', views.booking_list, name='list'),
    path('bookings/create/', views.booking_create, name='create'),
    path('bookings/<int:pk>/cancel/', views.booking_cancel, name='cancel'),

    path('owner/bookings/', views.owner_bookings, name='owner_list'),
    path('owner/bookings/<int:pk>/confirm/', views.booking_confirm, name='confirm'),
    path('owner/bookings/<int:pk>/reject/', views.booking_reject, name='reject'),
]
