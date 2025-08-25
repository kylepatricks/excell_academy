# finance/management/commands/generate_invoices.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import FeeStructure, Invoice
from accounts.models import Student
import random

class Command(BaseCommand):
    help = 'Generate invoices for all active fee structures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fee-structure',
            type=int,
            help='ID of specific fee structure to generate invoices for',
        )

    def handle(self, *args, **options):
        if options['fee_structure']:
            fee_structures = FeeStructure.objects.filter(id=options['fee_structure'])
        else:
            fee_structures = FeeStructure.objects.all()

        for fee_structure in fee_structures:
            self.generate_invoices_for_structure(fee_structure)

    def generate_invoices_for_structure(self, fee_structure):
        """Generate invoices for all students in the class level"""
        students = Student.objects.filter(current_class=fee_structure.class_level)
        
        created_count = 0
        for student in students:
            # Check if invoice already exists for this fee structure and student
            existing_invoice = Invoice.objects.filter(
                student=student,
                fee_structure=fee_structure
            ).first()

            if not existing_invoice:
                # Generate unique invoice number
                invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                
                invoice = Invoice.objects.create(
                    student=student,
                    fee_structure=fee_structure,
                    invoice_number=invoice_number,
                    issue_date=timezone.now().date(),
                    due_date=fee_structure.due_date,
                    amount=fee_structure.amount,
                    status='pending'
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created invoice #{invoice_number} for {student.user.get_full_name()}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Created {created_count} invoices for {fee_structure}')
        )