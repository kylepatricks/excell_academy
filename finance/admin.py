# finance/admin.py
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import FeeStructure, Invoice, Payment
from .management.commands.generate_invoices import Command as GenerateInvoicesCommand


@admin.action(description='Generate invoices for selected fee structures')
def generate_invoices(modeladmin, request, queryset):
    for fee_structure in queryset:
        cmd = GenerateInvoicesCommand()
        cmd.generate_invoices_for_structure(fee_structure)
    
    modeladmin.message_user(request, f"Invoices generated for {queryset.count()} fee structures")
    return HttpResponseRedirect(reverse('admin:finance_invoice_changelist'))

class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['class_level', 'academic_year', 'term', 'amount', 'due_date']
    list_filter = ['class_level', 'academic_year', 'term']
    actions = [generate_invoices]

admin.site.register(FeeStructure)
admin.site.register(Invoice)
admin.site.register(Payment)