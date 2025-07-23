from django.urls import path
from . import views

urlpatterns = [
    path('contacts/', views.create_contact, name='create_contact'),
    path('contacts/list/', views.user_contacts, name='user_contacts'),
    path('contacts/<int:pk>/status/', views.update_status, name='update_status'),
] 