from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Contact
from .serializers import ContactSerializer
import logging
from django.db import models
from math import ceil

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
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    contacts_qs = Contact.objects.filter(models.Q(sender=user_email) | models.Q(assigned_to=user_email)).order_by('-sent_at')
    total = contacts_qs.count()
    total_pages = ceil(total / page_size) if page_size else 1
    start = (page - 1) * page_size
    end = start + page_size
    contacts = contacts_qs[start:end]
    serializer = ContactSerializer(contacts, many=True)
    return Response({
        'results': serializer.data,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    })

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
