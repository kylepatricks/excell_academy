# accounts/management/commands/fix_user_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Parent, Student, Teacher

CustomUser = get_user_model()

class Command(BaseCommand):
    help = 'Create missing user profiles based on user type'

    def handle(self, *args, **options):
        # Fix parent profiles
        parent_users = CustomUser.objects.filter(user_type='parent')
        for user in parent_users:
            if not hasattr(user, 'parent_profile'):
                Parent.objects.create(user=user)
                self.stdout.write(f'Created parent profile for {user.username}')
        
        # Fix teacher profiles
        teacher_users = CustomUser.objects.filter(user_type='teacher')
        for user in teacher_users:
            if not hasattr(user, 'teacher_profile'):
                Teacher.objects.create(user=user, employee_id=f'TCH{user.id}')
                self.stdout.write(f'Created teacher profile for {user.username}')
        
        # Fix student profiles
        student_users = CustomUser.objects.filter(user_type='student')
        for user in student_users:
            if not hasattr(user, 'student_profile'):
                # Create a default parent for the student
                parent, created = Parent.objects.get_or_create(
                    user=user,
                    defaults={'occupation': 'Unknown', 'emergency_contact': 'Not provided'}
                )
                Student.objects.create(
                    user=user,
                    parent=parent,
                    admission_number=f'STU{user.id}',
                    admission_date='2023-01-01'
                )
                self.stdout.write(f'Created student profile for {user.username}')
        
        self.stdout.write(self.style.SUCCESS('User profiles fixed successfully!'))