# finance/utils.py
from django.shortcuts import get_object_or_404
from finance.models import Invoice
  
def get_safe_invoice(invoice_id, user):
    """Safely get invoice with proper relationship checking"""
    try:
        return get_object_or_404(Invoice, id=invoice_id, student__parent__user=user)
    except ValueError:
        # Handle invalid invoice ID format
        return None
    except Invoice.DoesNotExist:
        # Invoice doesn't exist or user doesn't have access
        return None