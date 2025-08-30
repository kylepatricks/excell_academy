from django.urls import reverse
from io import BytesIO
from django.utils import timezone
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.conf import settings
import os


def get_report_card_link(student, term, academic_year):
    """Safely get report card link or return None if not exists"""
    try:
        from .models import ReportCard
        report_card = ReportCard.objects.get(
            student=student,
            term=term,
            academic_year=academic_year
        )
        return reverse('report_card_detail', args=[report_card.id])
    except ReportCard.DoesNotExist:
        return None
    except Exception:
        return None
    

# academics/utils.py

def generate_pdf_for_report_card(report_card):
    """Generate PDF for a report card (utility function)"""
    from .models import Grade
    
    # Get grades for this report card period
    grades = Grade.objects.filter(
        student=report_card.student,
        term=report_card.term,
        academic_year=report_card.academic_year
    )
    
    # Calculate statistics
    total_subjects = grades.count()
    total_score = sum(grade.score for grade in grades)
    total_max_score = sum(grade.maximum_score for grade in grades)
    average_percentage = (total_score / total_max_score * 100) if total_max_score > 0 else 0
    
    context = {
        'report_card': report_card,
        'grades': grades,
        'total_subjects': total_subjects,
        'total_score': total_score,
        'total_max_score': total_max_score,
        'average_percentage': average_percentage,
        'school_name': 'Excel International Academy',
        'generation_date': timezone.now().date(),
    }
    
    # Render HTML template
    template = get_template('academics/report_card_pdf.html')
    html = template.render(context)
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)
    
    if not pdf.err:
        # Save PDF to file
        filename = report_card.generate_filename()
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'report_cards', filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
        
        # Update report card with PDF file
        report_card.pdf_file = f'report_cards/{filename}'
        report_card.save()
        return True
    
    return False