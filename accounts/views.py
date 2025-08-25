# accounts/views.py
from django.db.models import Q
from django.db import OperationalError
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.contrib import messages
from accounts.utils import require_profile
from core.models import Application
from .models import CustomUser, Parent, Student, Teacher
from academics.models import Class, Attendance, Grade, ReportCard
from finance.models import Invoice, Payment
from notifications.models import Notification
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect


def is_admin(user):
    return user.user_type == 'admin'

def is_teacher(user):
    return user.user_type == 'teacher'

def is_parent(user):
    return user.user_type == 'parent'

def is_student(user):
    return user.user_type == 'student'

@login_required
def dashboard(request):
    user = request.user
    
    if user.user_type == 'admin':
        return redirect('admin_dashboard')
    elif user.user_type == 'teacher':
        return redirect('teacher_dashboard')
    elif user.user_type == 'parent':
        return redirect('parent_dashboard')
    elif user.user_type == 'student':
        return redirect('student_dashboard')
    else:
        return redirect('home')

def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect based on user type
            if user.user_type == 'admin':
                return redirect('admin_dashboard')
            elif user.user_type == 'teacher':
                return redirect('teacher_dashboard')
            elif user.user_type == 'parent':
                return redirect('parent_dashboard')
            elif user.user_type == 'student':
                return redirect('student_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

@require_http_methods(["GET", "POST"])
@csrf_protect
@login_required
def custom_logout(request):
    """Custom logout view with confirmation support"""
    if request.method == 'GET':
        # Show confirmation page
        return render(request, 'accounts/logout_confirm.html')
    
    # POST request - process logout
    username = request.user.username
    
    # Perform logout
    logout(request)
    
    # Clear session completely
    request.session.flush()
    
    # Add success message
    messages.success(request, f'You have been successfully logged out, {username}.')
    
    # Redirect to home page
    return redirect('home')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Admin dashboard statistics
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_parents = Parent.objects.count()
    pending_applications = Application.objects.filter(status='pending').count()
    
    recent_notifications = Notification.objects.filter(recipient=request.user)[:5]
    unread_notifications_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_parents': total_parents,
        'pending_applications': pending_applications,
        'recent_notifications': recent_notifications,
        'unread_notifications_count': unread_notifications_count,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
@user_passes_test(is_teacher)
@require_profile('teacher')
def teacher_dashboard(request):
    teacher = request.profile
    assigned_class = teacher.assigned_class
    
    # Get students in assigned class
    students = assigned_class.students.all() if assigned_class else []
    
    # Get today's attendance
    from django.utils import timezone
    today = timezone.now().date()
    attendance_today = Attendance.objects.filter(
        class_instance=assigned_class,
        date=today
    ) if assigned_class else []
    
    # Count present students
    present_count = attendance_today.filter(status='present').count() if assigned_class else 0
    
    context = {
        'teacher': teacher,
        'assigned_class': assigned_class,
        'students': students,
        'attendance_today': attendance_today,
        'present_count': present_count,
        'total_students': students.count(),
        'subjects': teacher.subjects.all(),
    }
    return render(request, 'accounts/teacher_dashboard.html', context)


@login_required
@user_passes_test(is_parent)
@require_profile('parent')
def parent_dashboard(request):
    parent = request.profile
    children = parent.children.all()
        
    # Get children's academic information
    children_data = []
    for child in children:
        recent_grades = Grade.objects.filter(student=child)[:5]
        attendance = Attendance.objects.filter(student=child).order_by('-date')[:10]
        
        # Get ALL outstanding fees (pending, partial, overdue)
        outstanding_fees = Invoice.objects.filter(
            student=child, 
            status__in=['pending', 'partial', 'overdue']
        )
        
        # Calculate total outstanding amount
        total_outstanding = sum(invoice.amount for invoice in outstanding_fees)
        
        children_data.append({
            'child': child,
            'recent_grades': recent_grades,
            'attendance': attendance,
            'outstanding_fees': outstanding_fees,
            'total_outstanding': total_outstanding,
            'fee_count': outstanding_fees.count(),
        })
    
    # Calculate overall outstanding fees
    all_outstanding_fees = Invoice.objects.filter(
        student__parent=parent,
        status__in=['pending', 'partial', 'overdue']
    )
    total_family_outstanding = sum(invoice.amount for invoice in all_outstanding_fees)
    total_family_fee_count = all_outstanding_fees.count()
    
    context = {
        'children_data': children_data,
        'children': children,
        'total_family_outstanding': total_family_outstanding,
        'total_family_fee_count': total_family_fee_count,
        'has_outstanding_fees': total_family_fee_count > 0,
    }
    return render(request, 'accounts/parent_dashboard.html', context)

@login_required
def profile(request):
    """User profile view"""
    user = request.user
    profile_data = {}
    
    # Get additional profile data based on user type
    if user.user_type == 'parent':
        try:
            parent_profile = Parent.objects.get(user=user)
            profile_data = {
                'occupation': parent_profile.occupation,
                'emergency_contact': parent_profile.emergency_contact,
                'children': parent_profile.children.all()
            }
        except Parent.DoesNotExist:
            pass
            
    elif user.user_type == 'teacher':
        try:
            teacher_profile = Teacher.objects.get(user=user)
            profile_data = {
                'employee_id': teacher_profile.employee_id,
                'hire_date': teacher_profile.hire_date,
                'subjects': teacher_profile.subjects.all(),
                'assigned_class': teacher_profile.assigned_class
            }
        except Teacher.DoesNotExist:
            pass
            
    elif user.user_type == 'student':
        try:
            student_profile = Student.objects.get(user=user)
            profile_data = {
                'admission_number': student_profile.admission_number,
                'admission_date': student_profile.admission_date,
                'current_class': student_profile.current_class,
                'parent': student_profile.parent
            }
        except Student.DoesNotExist:
            pass
    
    context = {
        'profile_data': profile_data,
        'user_type_display': user.get_user_type_display()
    }
    return render(request, 'accounts/profile.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_profile(request):
    """Teacher profile view and edit"""
    try:
        teacher = request.user.teacher_profile.first()
    except Teacher.DoesNotExist:
        # Create a basic teacher profile if it doesn't exist
        teacher = Teacher.objects.create(
            user=request.user,
            employee_id=f"TEMP_{request.user.id}",
            hire_date=timezone.now().date()
        )
        messages.info(request, 'A basic teacher profile has been created for you. Please update your details.')
    
    if request.method == 'POST':
        # Update teacher profile
        teacher.employee_id = request.POST.get('employee_id', teacher.employee_id)
        teacher.hire_date = request.POST.get('hire_date', teacher.hire_date)
        teacher.save()
        
        # Update user information
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.phone = request.POST.get('phone', request.user.phone)
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('teacher_profile')
    
    context = {
        'teacher': teacher,
    }
    return render(request, 'accounts/teacher_profile.html', context)



@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def user_management(request):
    """User management dashboard"""
    users = CustomUser.objects.all().order_by('-date_joined')
    user_type_filter = request.GET.get('user_type')
    search_query = request.GET.get('search')
    status_filter = request.GET.get('status')
    
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Counts for statistics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    parents_count = CustomUser.objects.filter(user_type='parent').count()
    teachers_count = CustomUser.objects.filter(user_type='teacher').count()
    students_count = CustomUser.objects.filter(user_type='student').count()
    
    context = {
        'users': users,
        'user_type_filter': user_type_filter,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_users': total_users,
        'active_users': active_users,
        'parents_count': parents_count,
        'teachers_count': teachers_count,
        'students_count': students_count,
    }
    return render(request, 'accounts/user_management.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def user_detail(request, user_id):
    """View user details"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Get additional profile data based on user type
    profile_data = {}
    if user.user_type == 'parent':
        try:
            parent_profile = Parent.objects.get(user=user)
            profile_data = {
                'occupation': parent_profile.occupation,
                'emergency_contact': parent_profile.emergency_contact,
                'children': parent_profile.children.all()
            }
        except Parent.DoesNotExist:
            pass
            
    elif user.user_type == 'teacher':
        try:
            teacher_profile = Teacher.objects.get(user=user)
            profile_data = {
                'employee_id': teacher_profile.employee_id,
                'hire_date': teacher_profile.hire_date,
                'subjects': teacher_profile.subjects.all(),
                'assigned_class': teacher_profile.assigned_class
            }
        except Teacher.DoesNotExist:
            pass
            
    elif user.user_type == 'student':
        try:
            student_profile = Student.objects.get(user=user)
            profile_data = {
                'admission_number': student_profile.admission_number,
                'admission_date': student_profile.admission_date,
                'current_class': student_profile.current_class,
                'parent': student_profile.parent
            }
        except Student.DoesNotExist:
            pass
    
    context = {
        'user_profile': user,
        'profile_data': profile_data
    }
    return render(request, 'accounts/user_detail.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def toggle_user_status(request, user_id):
    """Activate or deactivate a user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user.is_active:
        user.is_active = False
        action = 'deactivated'
    else:
        user.is_active = True
        action = 'activated'
    
    user.save()
    messages.success(request, f'User {user.username} has been {action}.')
    
    return redirect('user_management')