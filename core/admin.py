# core/admin.py
from django.contrib import admin
from .models import Facility, Application, ContactMessage

admin.site.register(Facility)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('child_name', 'desired_class', 'first_name', 'last_name', 'email', 'status', 'application_date')
    list_filter = ('status', 'desired_class', 'application_date')
    search_fields = ('child_name', 'first_name', 'last_name', 'email')
    readonly_fields = ('application_date',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at', 'is_read', 'responded')
    list_filter = ('is_read', 'responded', 'submitted_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('submitted_at',)