# accounts/utils.py
from django.contrib import messages
from django.shortcuts import redirect

def get_teacher_profile(user):
    """Safely get teacher profile from user"""
    if hasattr(user, 'teacher_profile'):
        teacher = user.teacher_profile.first()
        if teacher:
            return teacher
    return None

def get_parent_profile(user):
    """Safely get parent profile from user"""
    if hasattr(user, 'parent_profile'):
        parent = user.parent_profile.first()
        if parent:
            return parent
    return None

def get_student_profile(user):
    """Safely get student profile from user"""
    if hasattr(user, 'student_profile'):
        student = user.student_profile.first()
        if student:
            return student
    return None

def require_profile(profile_type):
    """Decorator to require a specific profile type"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            if profile_type == 'teacher':
                profile = get_teacher_profile(user)
                error_msg = 'Teacher profile not found. Please contact administrator.'
            elif profile_type == 'parent':
                profile = get_parent_profile(user)
                error_msg = 'Parent profile not found. Please contact administrator.'
            elif profile_type == 'student':
                profile = get_student_profile(user)
                error_msg = 'Student profile not found. Please contact administrator.'
            else:
                messages.error(request, 'Invalid profile type.')
                return redirect('dashboard')
            
            if not profile:
                messages.error(request, error_msg)
                return redirect('dashboard')
            
            # Add profile to request for easier access in views
            request.profile = profile
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator