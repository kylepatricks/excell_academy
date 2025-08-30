# academics/management/commands/generate_missing_pdfs.py
from django.core.management.base import BaseCommand
from academics.models import ReportCard
from django.contrib.auth import get_user_model
from django.utils import timezone
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.conf import settings
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate PDFs for report cards that are finalized but missing PDF files'

    def handle(self, *args, **options):
        # Find report cards that are finalized but missing PDFs
        report_cards = ReportCard.objects.filter(is_finalized=True, pdf_file__isnull=True)
        
        self.stdout.write(f"Found {report_cards.count()} report cards needing PDF generation")
        
        # Get an admin user for permissions
        admin_user = User.objects.filter(user_type='admin', is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found'))
            return
        
        success_count = 0
        for report_card in report_cards:
            try:
                self.generate_pdf_for_report_card(report_card)
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f'Generated PDF for {report_card}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error generating PDF for {report_card}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {success_count} PDFs'))

    def generate_pdf_for_report_card(self, report_card):
        from academics.models import Grade
        
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