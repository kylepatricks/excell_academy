# academics/management/commands/check_report_cards.py
from django.core.management.base import BaseCommand
from academics.models import ReportCard
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Check and fix report card PDF files'

    def handle(self, *args, **options):
        report_cards = ReportCard.objects.filter(is_finalized=True)
        
        fixed_count = 0
        for report_card in report_cards:
            if report_card.pdf_file:
                # Check if file actually exists
                if not os.path.exists(report_card.pdf_file.path):
                    self.stdout.write(f"Missing PDF for report card {report_card.id}")
                    report_card.is_finalized = False
                    report_card.save()
                    fixed_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} report cards with missing PDF files'))