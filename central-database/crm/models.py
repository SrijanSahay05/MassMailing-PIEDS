from django.db import models

# Create your models here.

class Contact(models.Model):
    STATUS_CHOICES = [
        ('CONTACTED', 'Contacted'),
        ('IN_TALKS', 'In Talks'),
        ('NEGOTIATION', 'Negotiation'),
        ('CLOSED_WIN', 'Closed-Win'),
        ('CLOSED_LOST', 'Closed-Lost'),
    ]
    email = models.EmailField()
    poc_name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    sender = models.EmailField()  # The user who sent the email
    assigned_to = models.EmailField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONTACTED')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the contact mail was sent.", null=True, blank=True)
    gmail_thread_id = models.CharField(max_length=255, null=True, blank=True, help_text="Gmail thread ID for direct linking to the conversation.")

    def __str__(self):
        return f"{self.poc_name}({self.email} || assigned to {self.assigned_to})"
        