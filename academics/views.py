# academics/views.py
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import Class, Attendance, Grade, Promotion, ReportCard, Subject
from accounts.models import Student, Teacher
from xhtml2pdf import pisa
from io import BytesIO
import os
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
from django.db.models import Avg


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
        
        if not term or not academic_year:
            messages.error(request, 'Please select both term and academic year.')
            return redirect('generate_report_cards')
        
        generated_count = 0
        for student in students:
            # Check if report card already exists
            if ReportCard.objects.filter(student=student, term=term, academic_year=academic_year).exists():
                continue
            
            student_performances = []

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

                student_performances.append({
                    'student': student,
                    'percentage': percentage,
                    'total_score': total_score,
                    'total_max': total_max
                })
            
            student_performances.sort(key=lambda x: x['percentage'], reverse=True)
        
        # Assign class positions
        generated_count = 0
        current_position = 1
        previous_percentage = None
        skip_count = 0
        
        for i, performance in enumerate(student_performances):
            # Handle ties (students with same percentage get same position)
            if (previous_percentage is not None and 
                abs(performance['percentage'] - previous_percentage) < 0.1):  # Consider same if within 0.1%
                skip_count += 1
            else:
                current_position += skip_count
                skip_count = 1

                
                # Determine overall grade
                if percentage >= 90:
                    overall_grade = 'A+'
                elif percentage >= 80:
                    overall_grade = 'A'
                elif percentage >= 70:
                    overall_grade = 'B'
                elif percentage >= 60:
                    overall_grade = 'C'
                elif percentage >= 50:
                    overall_grade = 'D'
                else:
                    overall_grade = 'F'
                
                # Create report card (without PDF initially)
                ReportCard.objects.create(
                    student=student,
                    term=term,
                    academic_year=academic_year,
                    overall_grade=overall_grade,
                    class_position=None,  # Will be calculated later
                    remarks=f"Automatically generated on {timezone.now().date()}",
                    generated_by=teacher
                )
                generated_count += 1
        
        messages.success(request, f'Generated {generated_count} report cards. You can now generate PDFs for individual students.')
        return redirect('generate_report_cards')
    
    context = {
        'assigned_class': assigned_class,
        'students': students,
    }
    return render(request, 'academics/generate_report_cards.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def generate_report_card_pdf(request, report_card_id):
    """Generate PDF for a report card"""
    report_card = get_object_or_404(ReportCard, id=report_card_id)
    
    # Check if teacher has permission
    if (request.user.user_type != 'teacher' or request.user.teacher != report_card.generated_by) and request.user.user_type != 'admin':
        messages.error(request, 'You do not have permission to generate this report card.')
        return redirect('teacher_dashboard')
    
    # Get all grades for this report card period
    grades = Grade.objects.filter(
        student=report_card.student,
        term=report_card.term,
        academic_year=report_card.academic_year
    )
    
    if not grades.exists():
        messages.error(request, 'No grades found for this report card period.')
        return redirect('report_card_detail', report_card_id=report_card.id)
    
    # Calculate statistics
    total_subjects = grades.count()
    total_score = sum(grade.score for grade in grades)
    total_max_score = sum(grade.maximum_score for grade in grades)
    average_percentage = (total_score / total_max_score * 100) if total_max_score > 0 else 0
    
    context = {
        'report_card': report_card,
        'grades': grades,
        'total_subjects': total_subjects,
        'total_score': total_score,
        'total_max_score': total_max_score,
        'average_percentage': average_percentage,
        'school_name': 'Excel International Academy',
        'generation_date': timezone.now().date(),
    }
    
    # Render HTML template
    template = get_template('academics/report_card_pdf.html')
    html = template.render(context)
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)
    
    if not pdf.err:
        # Save PDF to file
        filename = report_card.generate_filename()
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'report_cards', filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
        
        # Update report card with PDF file
        report_card.pdf_file = f'report_cards/{filename}'
        report_card.is_finalized = True
        report_card.save()
        
        messages.success(request, 'Report card PDF generated successfully!')
        
        # Return to preview after generation
        return preview_report_card(request, report_card_id)
    
    messages.error(request, 'Error generating PDF report card.')
    return redirect('report_card_detail', report_card_id=report_card.id)

# academics/views.py
@login_required
def download_report_card(request, report_card_id):
    """Download report card PDF"""
    report_card = get_object_or_404(ReportCard, id=report_card_id)
    
    # Check permission (parent, student, teacher, or admin)
    if (request.user != report_card.student.user and 
        request.user != report_card.student.parent.user and
        (request.user.user_type != 'teacher' or request.user.teacher != report_card.generated_by) and
        request.user.user_type != 'admin'):
        messages.error(request, 'You do not have permission to download this report card.')
        return redirect('dashboard')
    
    if not report_card.pdf_file:
        # If PDF doesn't exist but report card is finalized, try to generate it
        if report_card.is_finalized:
            try:
                # Generate PDF on the fly
                from .utils import generate_pdf_for_report_card
                generate_pdf_for_report_card(report_card)
                report_card.refresh_from_db()
            except Exception as e:
                messages.error(request, 'Report card PDF not generated yet. Please contact administrator.')
                return redirect('report_card_detail', report_card_id=report_card.id)
        else:
            messages.error(request, 'Report card not finalized yet. Please wait for administration to finalize it.')
            return redirect('report_card_detail', report_card_id=report_card.id)
    
    # Check if file actually exists on filesystem
    if not report_card.pdf_file or not os.path.exists(report_card.pdf_file.path):
        messages.error(request, 'PDF file not found. Please contact administrator.')
        return redirect('report_card_detail', report_card_id=report_card.id)
    
    # Serve the PDF file
    with open(report_card.pdf_file.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
    
    filename = f"report_card_{report_card.student.user.get_full_name()}_{report_card.term}_{report_card.academic_year}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def preview_report_card(request, report_card_id):
    """Preview report card in browser"""
    report_card = get_object_or_404(ReportCard, id=report_card_id)
    
    # Check permission
    if (request.user != report_card.student.user and 
        request.user != report_card.student.parent.user and
        (request.user.user_type != 'teacher' or request.user.teacher != report_card.generated_by) and
        request.user.user_type != 'admin'):
        messages.error(request, 'You do not have permission to view this report card.')
        return redirect('dashboard')
    
    if not report_card.pdf_file:
        # If PDF hasn't been generated yet, generate it first
        return generate_report_card_pdf(request, report_card_id)
    
    # Serve the PDF for preview
    try:
        with open(report_card.pdf_file.path, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="preview.pdf"'
            return response
    except FileNotFoundError:
        # If file doesn't exist, regenerate it
        return generate_report_card_pdf(request, report_card_id)

# academics/views.py
@login_required
def report_card_list(request):
    """List all report cards for the current user (parent or student)"""
    student_id = request.GET.get('student')
    
    if request.user.user_type == 'parent':
        report_cards = ReportCard.objects.filter(student__parent__user=request.user)
        if student_id:
            report_cards = report_cards.filter(student_id=student_id)
    elif request.user.user_type == 'student':
        report_cards = ReportCard.objects.filter(student__user=request.user)
    elif request.user.user_type == 'teacher':
        report_cards = ReportCard.objects.filter(generated_by=request.user.teacher)
        if student_id:
            report_cards = report_cards.filter(student_id=student_id)
    else:  # admin
        report_cards = ReportCard.objects.all()
        if student_id:
            report_cards = report_cards.filter(student_id=student_id)
    
    report_cards = report_cards.order_by('-academic_year', '-term')
    
    # Get students for filter dropdown (for parents and teachers)
    students = []
    if request.user.user_type == 'parent':
        students = Student.objects.filter(parent__user=request.user)
    elif request.user.user_type == 'teacher':
        students = Student.objects.filter(current_class=request.user.teacher.assigned_class)
    
    context = {
        'report_cards': report_cards,
        'students': students,
        'selected_student': student_id,
    }
    return render(request, 'academics/report_card_list.html', context)

@login_required
def report_card_detail(request, report_card_id):
    """View report card details"""
    report_card = get_object_or_404(ReportCard, id=report_card_id)
    
    # Check permission - FIXED
    has_permission = False
    
    if request.user.user_type == 'parent':
        has_permission = (report_card.student.parent.user == request.user)
    elif request.user.user_type == 'student':
        has_permission = (report_card.student.user == request.user)
    elif request.user.user_type == 'teacher':
        has_permission = (request.user.teacher == report_card.generated_by or 
                         request.user.teacher == report_card.student.current_class.class_teacher)
    elif request.user.user_type == 'admin':
        has_permission = True
    
    if not has_permission:
        messages.error(request, 'You do not have permission to view this report card.')
        return redirect('dashboard')
    
    # Get grades for this report card
    grades = Grade.objects.filter(
        student=report_card.student,
        term=report_card.term,
        academic_year=report_card.academic_year
    )
    
    context = {
        'report_card': report_card,
        'grades': grades,
    }
    return render(request, 'academics/report_card_detail.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'teacher')
def update_report_card_remarks(request, report_card_id):
    """Update report card remarks"""
    report_card = get_object_or_404(ReportCard, id=report_card_id)
    
    # Check if teacher has permission
    if request.user.teacher != report_card.generated_by:
        messages.error(request, 'You can only update remarks for report cards you generated.')
        return redirect('report_card_detail', report_card_id=report_card.id)
    
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        report_card.remarks = remarks
        report_card.save()
        messages.success(request, 'Remarks updated successfully.')
    
    return redirect('report_card_detail', report_card_id=report_card.id)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def admin_generate_report_card_pdf(request, report_card_id):
    """Admin endpoint to generate PDF for finalized report cards"""
    report_card = get_object_or_404(ReportCard, id=report_card_id)
    
    if not report_card.is_finalized:
        messages.error(request, 'Report card must be finalized before generating PDF.')
        return redirect('admin:academics_reportcard_changelist')
    
    # Generate PDF
    return generate_report_card_pdf(request, report_card_id)

# Update the existing function to handle both teacher and admin generation
def generate_report_card_pdf(request, report_card_id):
    """Generate PDF for a report card (internal function)"""
    report_card = get_object_or_404(ReportCard, id=report_card_id)
    
    # Check if teacher has permission or if admin is forcing generation
    is_admin = request.user.user_type == 'admin'
    is_teacher_owner = request.user.user_type == 'teacher' and request.user.teacher == report_card.generated_by
    
    if not (is_admin or is_teacher_owner):
        messages.error(request, 'You do not have permission to generate this report card.')
        return redirect('dashboard')
    
    # Get all grades for this report card period
    grades = Grade.objects.filter(
        student=report_card.student,
        term=report_card.term,
        academic_year=report_card.academic_year
    )
    
    # Calculate statistics
    total_subjects = grades.count()
    total_score = sum(grade.score for grade in grades)
    total_max_score = sum(grade.maximum_score for grade in grades)
    average_percentage = (total_score / total_max_score * 100) if total_max_score > 0 else 0
    
    context = {
        'report_card': report_card,
        'grades': grades,
        'total_subjects': total_subjects,
        'total_score': total_score,
        'total_max_score': total_max_score,
        'average_percentage': average_percentage,
        'school_name': 'Excel International Academy',
        'generation_date': timezone.now().date(),
    }
    
    # Render HTML template
    template = get_template('academics/report_card_pdf.html')
    html = template.render(context)
    
    # Create PDF
    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)
    
    if not pdf.err:
        # Save PDF to file
        filename = report_card.generate_filename()
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'report_cards', filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        
        with open(pdf_path, 'wb') as f:
            f.write(result.getvalue())
        
        # Update report card with PDF file
        report_card.pdf_file = f'report_cards/{filename}'
        report_card.save()
        
        messages.success(request, 'Report card PDF generated successfully!')
        
        if is_admin:
            return redirect('admin:academics_reportcard_changelist')
        else:
            return redirect('report_card_detail', report_card_id=report_card.id)
    
    messages.error(request, 'Error generating PDF report card.')
    
    if is_admin:
        return redirect('admin:academics_reportcard_changelist')
    else:
        return redirect('generate_report_cards')
    


def is_admin_or_principal(user):
    return user.user_type in ['admin', 'teacher']  # Adjust based on your roles

@login_required
@user_passes_test(is_admin_or_principal)
def promotion_dashboard(request):
    """Dashboard for managing student promotions"""
    academic_years = Grade.objects.values_list('academic_year', flat=True).distinct()
    classes = Class.objects.all()
    
    context = {
        'academic_years': sorted(academic_years, reverse=True),
        'classes': classes,
    }
    return render(request, 'academics/promotion_dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_principal)
def check_promotion_eligibility(request):
    """Check which students are eligible for promotion"""
    if request.method == 'POST':
        academic_year = request.POST.get('academic_year')
        class_id = request.POST.get('class_id')
        min_average = float(request.POST.get('min_average', 70.0))
        
        try:
            class_obj = Class.objects.get(id=class_id)
            students = Student.objects.filter(current_class=class_obj)
            
            results = []
            for student in students:
                # Calculate average score
                grades = Grade.objects.filter(
                    student=student,
                    academic_year=academic_year
                )
                
                if grades.exists():
                    average_score = grades.aggregate(avg_score=Avg('score'))['avg_score'] or 0
                    average_percentage = (average_score / 100) * 100
                    eligible = average_percentage >= min_average
                    
                    results.append({
                        'student': student,
                        'average_score': average_percentage,
                        'eligible': eligible,
                        'grades_count': grades.count()
                    })
            
            context = {
                'class_obj': class_obj,
                'academic_year': academic_year,
                'min_average': min_average,
                'results': sorted(results, key=lambda x: x['average_score'], reverse=True),
                'total_students': len(results),
                'eligible_count': sum(1 for r in results if r['eligible']),
            }
            
            return render(request, 'academics/promotion_results.html', context)
            
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('promotion_dashboard')
    
    return redirect('promotion_dashboard')

@login_required
@user_passes_test(is_admin_or_principal)
def promote_students_ajax(request):
    """AJAX endpoint for promoting students"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_ids = data.get('student_ids', [])
            academic_year = data.get('academic_year')
            next_academic_year = data.get('next_academic_year')
            min_average = float(data.get('min_average', 70.0))
            
            promoted = []
            not_promoted = []
            
            for student_id in student_ids:
                try:
                    student = Student.objects.get(id=student_id)
                    current_class = student.current_class
                    
                    if not current_class:
                        not_promoted.append({'student': student, 'reason': 'No current class'})
                        continue
                    
                    # Calculate average
                    grades = Grade.objects.filter(
                        student=student,
                        academic_year=academic_year
                    )
                    
                    if not grades.exists():
                        not_promoted.append({'student': student, 'reason': 'No grades found'})
                        continue
                    
                    average_score = grades.aggregate(avg_score=Avg('score'))['avg_score'] or 0
                    average_percentage = (average_score / 100) * 100
                    
                    if average_percentage >= min_average:
                        # Find next class
                        next_class = get_next_class(current_class, next_academic_year)
                        
                        if next_class:
                            # Create promotion record
                            Promotion.objects.create(
                                student=student,
                                from_class=current_class,
                                to_class=next_class,
                                academic_year=academic_year,
                                average_score=average_percentage,
                                promoted_by=request.user.teacher if hasattr(request.user, 'teacher') else None,
                                notes=f"Manually promoted by {request.user.get_full_name()}"
                            )
                            
                            # Update student class
                            student.current_class = next_class
                            student.save()
                            
                            promoted.append({
                                'student': student,
                                'average': average_percentage,
                                'from_class': current_class,
                                'to_class': next_class
                            })
                        else:
                            not_promoted.append({'student': student, 'reason': 'Cannot determine next class'})
                    else:
                        not_promoted.append({'student': student, 'reason': f'Average {average_percentage:.1f}% < {min_average}%'})
                        
                except Exception as e:
                    not_promoted.append({'student': student_id, 'reason': f'Error: {str(e)}'})
            
            return JsonResponse({
                'success': True,
                'promoted': len(promoted),
                'not_promoted': len(not_promoted),
                'promoted_details': promoted,
                'not_promoted_details': not_promoted
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def get_next_class(current_class, next_academic_year):
    """Helper function to determine next class"""
    try:
        class_name = current_class.name
        if 'Grade' in class_name:
            grade_num = int(class_name.split()[-1])
            next_grade = grade_num + 1
            next_class_name = f"Grade {next_grade}"
        else:
            return None
        
        next_class, created = Class.objects.get_or_create(
            name=next_class_name,
            section=current_class.section,
            academic_year=next_academic_year
        )
        
        return next_class
        
    except (ValueError, IndexError):
        return None