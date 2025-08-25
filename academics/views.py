# academics/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import Class, Attendance, Grade, ReportCard, Subject
from accounts.models import Student, Teacher

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def mark_attendance(request):
    teacher = request.user.teacher_profile.first()
    assigned_class = teacher.assigned_class
    
    if not assigned_class:
        messages.error(request, 'You are not assigned to any class.')
        return redirect('teacher_dashboard')
    
    students = Student.objects.filter(current_class=assigned_class)
    today = timezone.now().date()
    
    # Get existing attendance for today
    existing_attendance = {}
    attendance_records = Attendance.objects.filter(class_instance=assigned_class, date=today)
    for att in attendance_records:
        existing_attendance[att.student.id] = att.status
    
    # Calculate attendance statistics
    present_count = attendance_records.filter(status='present').count()
    absent_count = attendance_records.filter(status='absent').count()
    late_count = attendance_records.filter(status='late').count()
    excused_count = attendance_records.filter(status='excused').count()
    
    # Calculate attendance rate
    if students.count() > 0:
        attendance_rate = ((present_count + late_count + excused_count) / students.count()) * 100
    else:
        attendance_rate = 0
    
    if request.method == 'POST':
        date_str = request.POST.get('date', today.isoformat())
        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            date = today
        
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'present')
            remarks = request.POST.get(f'remarks_{student.id}', '')
            
            # Update or create attendance record
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                class_instance=assigned_class,
                date=date,
                defaults={'status': status, 'remarks': remarks}
            )
            
            if not created:
                attendance.status = status
                attendance.remarks = remarks
                attendance.save()
        
        messages.success(request, f'Attendance marked successfully for {date}')
        return redirect('mark_attendance')
    
    context = {
        'assigned_class': assigned_class,
        'students': students,
        'today': today,
        'existing_attendance': existing_attendance,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'excused_count': excused_count,
        'attendance_rate': attendance_rate,
        'total_students': students.count(),
    }
    return render(request, 'academics/mark_attendance.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def enter_grades(request):
    try:
        teacher = request.user.teacher_profile.first()
    except Teacher.DoesNotExist:
        messages.error(request, 'Teacher profile not found. Please contact administrator.')
        return redirect('teacher_dashboard')
    
    assigned_class = teacher.assigned_class
    subjects = teacher.subjects.all()
    
    if not assigned_class:
        messages.error(request, 'You are not assigned to any class.')
        return redirect('teacher_dashboard')
    
    # Get students in assigned class - FIXED: Use the correct relationship
    students = Student.objects.filter(current_class=assigned_class)
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        term = request.POST.get('term')
        academic_year = request.POST.get('academic_year')
        
        if not subject_id or not term or not academic_year:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('enter_grades')
        
        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            messages.error(request, 'Selected subject does not exist.')
            return redirect('enter_grades')
        
        # Process grades for each student
        grades_created = 0
        grades_updated = 0
        
        for student in students:
            score_key = f'score_{student.id}'
            max_score_key = f'max_score_{student.id}'
            
            score = request.POST.get(score_key)
            max_score = request.POST.get(max_score_key, 100)
            
            if score:  # Only save if score is provided
                # Convert to decimal
                try:
                    score_decimal = float(score)
                    max_score_decimal = float(max_score)
                    
                    # Create or update grade
                    grade, created = Grade.objects.update_or_create(
                        student=student,
                        subject=subject,
                        term=term,
                        academic_year=academic_year,
                        defaults={
                            'score': score_decimal,
                            'maximum_score': max_score_decimal
                        }
                    )
                    
                    if created:
                        grades_created += 1
                    else:
                        grades_updated += 1
                        
                except ValueError:
                    messages.error(request, f'Invalid score format for {student.user.get_full_name()}')
                    continue
        
        messages.success(request, f'Grades saved successfully! Created: {grades_created}, Updated: {grades_updated}')
        return redirect('enter_grades')
    
    context = {
        'assigned_class': assigned_class,
        'subjects': subjects,
        'students': students,
    }
    return render(request, 'academics/enter_grades.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def generate_report_cards(request):
    teacher = request.user.teacher_profile.first()
    assigned_class = teacher.assigned_class
    
    if not assigned_class:
        messages.error(request, 'You are not assigned to any class.')
        return redirect('teacher_dashboard')
    
    students = Student.objects.filter(current_class=assigned_class)
    
    if request.method == 'POST':
        term = request.POST.get('term')
        academic_year = request.POST.get('academic_year')
        
        for student in students:
            # Calculate overall performance
            grades = Grade.objects.filter(
                student=student,
                term=term,
                academic_year=academic_year
            )
            
            if grades.exists():
                total_score = sum(grade.score for grade in grades)
                total_max = sum(grade.maximum_score for grade in grades)
                percentage = (total_score / total_max) * 100 if total_max > 0 else 0
                
                # Determine overall grade
                if percentage >= 90:
                    overall_grade = 'A'
                elif percentage >= 80:
                    overall_grade = 'B'
                elif percentage >= 70:
                    overall_grade = 'C'
                elif percentage >= 60:
                    overall_grade = 'D'
                else:
                    overall_grade = 'F'
                
                # Calculate class position (simplified)
                all_students_grades = []
                for s in students:
                    s_grades = Grade.objects.filter(
                        student=s,
                        term=term,
                        academic_year=academic_year
                    )
                    if s_grades.exists():
                        s_total = sum(g.score for g in s_grades)
                        s_max = sum(g.maximum_score for g in s_grades)
                        s_percentage = (s_total / s_max) * 100 if s_max > 0 else 0
                        all_students_grades.append((s.id, s_percentage))
                
                # Sort by percentage descending
                all_students_grades.sort(key=lambda x: x[1], reverse=True)
                
                # Find position
                position = None
                for idx, (s_id, perc) in enumerate(all_students_grades):
                    if s_id == student.id:
                        position = idx + 1
                        break
                
                # Create or update report card
                ReportCard.objects.update_or_create(
                    student=student,
                    term=term,
                    academic_year=academic_year,
                    defaults={
                        'overall_grade': overall_grade,
                        'class_position': position,
                        'generated_by': teacher,
                        'remarks': f'Generated on {timezone.now().strftime("%Y-%m-%d")}'
                    }
                )
        
        messages.success(request, f'Report cards generated successfully for {term} {academic_year}')
        return redirect('generate_report_cards')
    
    context = {
        'assigned_class': assigned_class,
        'students': students,
    }
    return render(request, 'academics/generate_report_cards.html', context)