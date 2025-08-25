# academics/management/commands/test_grades.py
from django.core.management.base import BaseCommand
from academics.models import Grade, Subject
from accounts.models import Student
from django.utils import timezone

class Command(BaseCommand):
    help = 'Test grade creation and display'

    def handle(self, *args, **options):
        # Get a student and subject to test with
        student = Student.objects.first()
        subject = Subject.objects.first()
        
        if not student or not subject:
            self.stdout.write(self.style.ERROR('No students or subjects found. Please run populate_data first.'))
            return
        
        # Create a test grade
        grade, created = Grade.objects.get_or_create(
            student=student,
            subject=subject,
            term='First Term',
            academic_year='2023-2024',
            defaults={
                'score': 85.5,
                'maximum_score': 100
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created test grade for {student}: {grade.score}/{grade.maximum_score}'))
        else:
            self.stdout.write(self.style.WARNING(f'Grade already exists for {student}: {grade.score}/{grade.maximum_score}'))
        
        # Show all grades for this student
        grades = Grade.objects.filter(student=student)
        self.stdout.write(f'\nAll grades for {student}:')
        for g in grades:
            self.stdout.write(f'  - {g.subject}: {g.score}/{g.maximum_score} ({g.percentage()}%) - {g.term} {g.academic_year}')