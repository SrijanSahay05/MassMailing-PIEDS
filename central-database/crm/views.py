from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Contact
from .serializers import ContactSerializer
import logging
from django.db import models

# Create your views here.

@api_view(['POST'])
def create_contact(request):
    serializer = ContactSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def user_contacts(request):
    user_email = request.GET.get('user_email')
    contacts = Contact.objects.filter(models.Q(sender=user_email) | models.Q(assigned_to=user_email))
    serializer = ContactSerializer(contacts, many=True)
    return Response(serializer.data)

@api_view(['PATCH'])
def update_status(request, pk):
    print(f"PATCH /contacts/{pk}/status/ - data: {request.data}")
    try:
        contact = Contact.objects.get(pk=pk)
        print(f"Updating contact: {contact.email} (id={contact.id})")
    except Contact.DoesNotExist:
        print(f"Contact with id={pk} does not exist.")
        return Response({'error': 'Not found'}, status=404)
    contact.status = request.data.get('status', contact.status)
    contact.save()
    print(f"Updated status to: {contact.status}")
    return Response({'success': True})
