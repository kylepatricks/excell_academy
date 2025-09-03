# academics/management/commands/promote_students.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from academics.models import Grade, Promotion, Class
from accounts.models import Student
from django.db.models import Avg, Q
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class Command(BaseCommand):
    help = 'Automatically promote students based on academic performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--academic-year',
            type=str,
            help='Academic year to process promotions for (e.g., 2023-2024)',
            required=True
        )
        parser.add_argument(
            '--next-academic-year',
            type=str,
            help='Next academic year (e.g., 2024-2025)',
            required=True
        )
        parser.add_argument(
            '--promoted-by',
            type=str,
            help='Username of teacher/admin performing the promotion',
            default='admin'
        )
        parser.add_argument(
            '--min-average',
            type=float,
            help='Minimum average score required for promotion',
            default=70.0
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be promoted without actually promoting'
        )

    def handle(self, *args, **options):
        academic_year = options['academic_year']
        next_academic_year = options['next_academic_year']
        min_average = options['min_average']
        dry_run = options['dry_run']
        promoted_by_username = options['promoted_by']
        
        try:
            promoted_by = CustomUser.objects.get(username=promoted_by_username)
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{promoted_by_username}' not found"))
            return
        
        self.stdout.write(f"Processing promotions from {academic_year} to {next_academic_year}")
        self.stdout.write(f"Minimum average required: {min_average}%")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
        
        # Get all students with grades for the academic year
        students = Student.objects.filter(
            grade__academic_year=academic_year
        ).distinct()
        
        promoted_count = 0
        not_promoted_count = 0
        error_count = 0
        
        for student in students:
            try:
                # Calculate average score for all terms
                grades = Grade.objects.filter(
                    student=student,
                    academic_year=academic_year
                )
                
                if not grades.exists():
                    continue
                
                average_score = grades.aggregate(
                    avg_score=Avg('score')
                )['avg_score'] or 0
                
                average_percentage = (average_score / 100) * 100  # Assuming max score is 100
                
                # Check if student should be promoted
                if average_percentage >= min_average:
                    current_class = student.current_class
                    
                    if not current_class:
                        self.stdout.write(f"{student}: No current class assigned")
                        continue
                    
                    # Determine next class (e.g., Grade 3 → Grade 4)
                    next_class = self.get_next_class(current_class, next_academic_year)
                    
                    if not next_class:
                        self.stdout.write(f"{student}: Cannot determine next class for {current_class}")
                        continue
                    
                    if dry_run:
                        self.stdout.write(f"WOULD PROMOTE: {student} ({average_percentage:.1f}%) from {current_class} to {next_class}")
                    else:
                        # Create promotion record
                        Promotion.objects.create(
                            student=student,
                            from_class=current_class,
                            to_class=next_class,
                            academic_year=academic_year,
                            average_score=average_percentage,
                            promoted_by=promoted_by.teacher if hasattr(promoted_by, 'teacher') else None,
                            notes=f"Automatically promoted based on average score of {average_percentage:.1f}%"
                        )
                        
                        # Update student's current class
                        student.current_class = next_class
                        student.save()
                        
                        self.stdout.write(f"PROMOTED: {student} ({average_percentage:.1f}%) from {current_class} to {next_class}")
                    
                    promoted_count += 1
                else:
                    self.stdout.write(f"NOT PROMOTED: {student} ({average_percentage:.1f}% < {min_average}%)")
                    not_promoted_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {student}: {e}"))
                error_count += 1
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("PROMOTION SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Total students processed: {students.count()}")
        self.stdout.write(f"Promoted: {promoted_count}")
        self.stdout.write(f"Not promoted: {not_promoted_count}")
        self.stdout.write(f"Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\nThis was a dry run. No changes were made."))
        else:
            self.stdout.write(self.style.SUCCESS("\nPromotion process completed successfully!"))

    def get_next_class(self, current_class, next_academic_year):
        """
        Determine the next class based on the current class
        Example: 'Grade 3' → 'Grade 4'
        """
        try:
            # Extract grade level from class name (e.g., "Grade 3" → 3)
            class_name = current_class.name
            if 'Grade' in class_name:
                grade_num = int(class_name.split()[-1])
                next_grade = grade_num + 1
                next_class_name = f"Grade {next_grade}"
            else:
                # For other class naming conventions
                # You might need to customize this based on your class structure
                return None
            
            # Find or create the next class
            next_class, created = Class.objects.get_or_create(
                name=next_class_name,
                section=current_class.section,
                academic_year=next_academic_year,
                defaults={
                    'class_teacher': None  # Can be assigned later
                }
            )
            
            return next_class
            
        except (ValueError, IndexError):
            return None