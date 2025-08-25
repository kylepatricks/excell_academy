# accounts/context_processors.py
def user_profile(request):
    """Add user profile to template context"""
    context = {}
    
    if request.user.is_authenticated:
        user = request.user
        
        if user.user_type == 'teacher' and hasattr(user, 'teacher_profile'):
            context['user_profile'] = user.teacher_profile
        elif user.user_type == 'parent' and hasattr(user, 'parent_profile'):
            context['user_profile'] = user.parent_profile
        elif user.user_type == 'student' and hasattr(user, 'student_profile'):
            context['user_profile'] = user.student_profile
        else:
            context['user_profile'] = None
    
    return context