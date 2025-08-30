# finance/models.py
import uuid
from django.db import models
from django.db import models
from django.utils import timezone


class FeeStructure(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    class_level = models.ForeignKey('academics.Class', on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.CharField(max_length=9)
    term = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)


    class Meta:
        unique_together = ('class_level', 'academic_year', 'term')
    
    def __str__(self):
        return f"{self.class_level} - {self.term} {self.academic_year}: ${self.amount}"


class Invoice(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=(
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue')
    ), default='pending')
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.student}"

    # Add Paystack reference field
    paystack_reference = models.CharField(max_length=100, blank=True, unique=True)
    
    
    def generate_paystack_reference(self):
        """Generate a unique Paystack reference"""
        if not self.paystack_reference or self.paystack_reference.startswith('TEMP_'):
            timestamp = int(timezone.now().timestamp())
            unique_id = uuid.uuid4().hex[:8].upper()
            self.paystack_reference = f"INV_{self.id}_{timestamp}_{unique_id}"
        return self.paystack_reference
    
    def save(self, *args, **kwargs):
        # Generate reference if not set
        if not self.paystack_reference:
            self.generate_paystack_reference()
        super().save(*args, **kwargs)

    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.student}"


class Payment(models.Model):

    PAYMENT_METHOD_CHOICES = (
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('paystack', 'Paystack'),
        ('cash', 'Cash'),
        ('bank_deposit', 'Bank Deposit'),
    )
    id = models.AutoField(primary_key=True, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='paystack')

    transaction_id = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=50, unique=True)
    confirmed_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Payment #{self.receipt_number} - {self.invoice}"
    
    original_reference = models.CharField(max_length=100, blank=True)  # Add this field
    
    def save(self, *args, **kwargs):
        if not self.original_reference and self.paystack_reference:
            # Extract original reference from the timestamp-appended reference
            parts = self.paystack_reference.split('_')
            if len(parts) > 3:  # If it has timestamp parts
                self.original_reference = '_'.join(parts[0:-1])
            else:
                self.original_reference = self.paystack_reference
        super().save(*args, **kwargs)

        
    # Add Paystack-specific fields
    paystack_reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    paystack_authorization = models.JSONField(null=True, blank=True)  # Store authorization data for recurring payments
    paystack_transfer_code = models.CharField(max_length=100, blank=True)  # For refunds
    