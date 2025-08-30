# academics/management/commands/recalculate_positions.py
from django.core.management.base import BaseCommand
from academics.models import ReportCard, Grade
from django.utils import timezone

class Command(BaseCommand):
    help = 'Recalculate class positions for existing report cards'

    def add_arguments(self, parser):
        parser.add_argument(
            '--term',
            help='Specific term to recalculate',
        )
        parser.add_argument(
            '--academic-year',
            help='Specific academic year to recalculate',
        )

    def handle(self, *args, **options):
        term = options.get('term')
        academic_year = options.get('academic_year')
        
        # Get report cards to process
        report_cards = ReportCard.objects.all()
        if term:
            report_cards = report_cards.filter(term=term)
        if academic_year:
            report_cards = report_cards.filter(academic_year=academic_year)
        
        # Group by class and term
        classes_processed = set()
        
        for report_card in report_cards:
            class_key = (report_card.student.current_class, report_card.term, report_card.academic_year)
            
            if class_key in classes_processed:
                continue
                
            self.recalculate_class_positions(
                report_card.student.current_class,
                report_card.term,
                report_card.academic_year
            )
            classes_processed.add(class_key)
        
        self.stdout.write(self.style.SUCCESS(f'Recalculated positions for {len(classes_processed)} classes'))

    def recalculate_class_positions(self, class_obj, term, academic_year):
        """Recalculate positions for a specific class and term"""
        students = class_obj.students.all()
        student_performances = []
        
        for student in students:
            # Get grades for this term
            grades = Grade.objects.filter(
                student=student,
                term=term,
                academic_year=academic_year
            )
            
            if grades.exists():
                total_score = sum(grade.score for grade in grades)
                total_max = sum(grade.maximum_score for grade in grades)
                percentage = (total_score / total_max) * 100 if total_max > 0 else 0
                
                student_performances.append({
                    'student': student,
                    'percentage': percentage
                })
        
        # Sort by percentage descending
        student_performances.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Assign positions (handle ties)
        current_position = 1
        previous_percentage = None
        skip_count = 0
        
        for i, performance in enumerate(student_performances):
            # Handle ties
            if (previous_percentage is not None and 
                abs(performance['percentage'] - previous_percentage) < 0.1):
                skip_count += 1
            else:
                current_position += skip_count
                skip_count = 1
            
            # Update report card
            ReportCard.objects.filter(
                student=performance['student'],
                term=term,
                academic_year=academic_year
            ).update(class_position=current_position)
            
            previous_percentage = performance['percentage']
        
        self.stdout.write(f'Recalculated positions for {class_obj} {term} {academic_year}')