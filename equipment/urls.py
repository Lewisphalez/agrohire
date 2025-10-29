from django.urls import path
from . import views

app_name = 'equipment'

urlpatterns = [
    
    path('equipment/', views.equipment_list, name='list'),
    path('equipment/<int:pk>/', views.equipment_detail, name='detail'),

    path('owner/equipment/', views.my_equipment_list, name='my_list'),
    path('owner/equipment/add/', views.equipment_create, name='create'),
    path('owner/equipment/<int:pk>/edit/', views.equipment_edit, name='edit'),
    path('owner/equipment/<int:pk>/delete/', views.equipment_delete, name='delete'),
]
