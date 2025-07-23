from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("poc_name", "email", "company", "status", "sender", "assigned_to", "created_at", "gmail_thread_id")
    search_fields = ("poc_name", "email", "company", "sender", "assigned_to")
    list_filter = ("status", "sender", "company")
    readonly_fields = ("sender", "gmail_thread_id")
