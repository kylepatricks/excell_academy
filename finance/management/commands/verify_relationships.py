# finance/management/commands/verify_relationships.py
from django.core.management.base import BaseCommand
from finance.models import Invoice
from accounts.models import Student, Parent

class Command(BaseCommand):
    help = 'Verify that all database relationships are valid'

    def handle(self, *args, **options):
        # Check invoices
        for invoice in Invoice.objects.all():
            try:
                student = invoice.student
                parent = student.parent
                user = parent.user
                self.stdout.write(f"Invoice {invoice.id}: OK")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Invoice {invoice.id}: {e}"))
        
        self.stdout.write(self.style.SUCCESS('Relationship verification completed'))