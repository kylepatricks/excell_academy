# finance/management/commands/debug_fees.py
from django.core.management.base import BaseCommand
from finance.models import FeeStructure
from accounts.models import Student
from academics.models import Class

class Command(BaseCommand):
    help = 'Debug fee structures and student relationships'

    def handle(self, *args, **options):
        self.stdout.write("=== FEE STRUCTURES DEBUG ===")
        
        # List all fee structures
        fee_structures = FeeStructure.objects.all()
        self.stdout.write(f"Total fee structures: {fee_structures.count()}")
        
        for fs in fee_structures:
            self.stdout.write(f"\nFee Structure: {fs}")
            self.stdout.write(f"  Class Level: {fs.class_level}")
            self.stdout.write(f"  Class Level ID: {fs.class_level_id}")
            
            if fs.class_level:
                # Count students in this class
                students_count = Student.objects.filter(current_class=fs.class_level).count()
                self.stdout.write(f"  Students in class: {students_count}")
            else:
                self.stdout.write("  WARNING: No class level assigned!")

        # List all classes and their student counts
        self.stdout.write("\n=== CLASSES AND STUDENTS ===")
        classes = Class.objects.all()
        for cls in classes:
            student_count = Student.objects.filter(current_class=cls).count()
            self.stdout.write(f"Class {cls}: {student_count} students")