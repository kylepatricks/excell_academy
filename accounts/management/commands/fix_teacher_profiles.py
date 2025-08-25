# accounts/management/commands/fix_teacher_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Teacher
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Create Teacher profiles for users with teacher type who are missing profiles'

    def handle(self, *args, **options):
        teacher_users = User.objects.filter(user_type='teacher')
        created_count = 0
        
        for user in teacher_users:
            if not hasattr(user, 'teacher'):
                Teacher.objects.create(
                    user=user,
                    employee_id=f"TEMP_{user.id}",
                    hire_date=timezone.now().date()
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created Teacher profile for {user.username}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} Teacher profiles')
        )