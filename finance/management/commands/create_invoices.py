# finance/management/commands/create_invoices.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import FeeStructure, Invoice
from accounts.models import Student
import random

class Command(BaseCommand):
    help = 'Create invoices for all active fee structures'

    def handle(self, *args, **options):
        # Get all active fee structures
        fee_structures = FeeStructure.objects.filter(active=True)
        
        if not fee_structures.exists():
            self.stdout.write(self.style.ERROR('No active fee structures found.'))
            return

        total_created = 0
        
        for fee_structure in fee_structures:
            self.stdout.write(f'Processing fee structure: {fee_structure}')
            
            # Get students in the appropriate class
            students = Student.objects.filter(current_class=fee_structure.class_level)
            
            if not students.exists():
                self.stdout.write(self.style.WARNING(f'No students found for class: {fee_structure.class_level}'))
                continue
            
            for student in students:
                # Check if invoice already exists
                if not Invoice.objects.filter(student=student, fee_structure=fee_structure).exists():
                    # Create invoice
                    invoice = Invoice.objects.create(
                        student=student,
                        fee_structure=fee_structure,
                        invoice_number=self.generate_invoice_number(),
                        issue_date=timezone.now().date(),
                        due_date=fee_structure.due_date,
                        amount=fee_structure.amount,
                        status='pending'
                    )
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Created invoice for {student.user.get_full_name()}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {total_created} invoices.'))

    def generate_invoice_number(self):
        """Generate a unique invoice number"""
        return f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}"