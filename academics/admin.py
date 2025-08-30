# academics/admin.py
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Class, Subject, Attendance, Grade, ReportCard

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'term', 'academic_year', 'score', 'maximum_score', 'percentage']
    list_filter = ['subject', 'term', 'academic_year', 'student__current_class']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'subject__name']
    readonly_fields = ['percentage']
    
    def percentage(self, obj):
        return f"{obj.percentage()}%"
    percentage.short_description = 'Percentage'

@admin.action(description='Generate PDF for selected report cards')
def generate_pdf_action(modeladmin, request, queryset):
    for report_card in queryset:
        if report_card.is_finalized and not report_card.pdf_file:
            # Call the PDF generation function
            from .views import generate_report_card_pdf
            # We need to mock a request object for the function
            class MockRequest:
                def __init__(self, user):
                    self.user = user
            
            mock_request = MockRequest(request.user)
            try:
                generate_report_card_pdf(mock_request, report_card.id)
            except Exception as e:
                modeladmin.message_user(request, f"Error generating PDF for {report_card}: {e}", level='error')
    
    modeladmin.message_user(request, f"PDF generation initiated for {queryset.count()} report cards.")
    return HttpResponseRedirect(reverse('admin:academics_reportcard_changelist'))





@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin): 
    search_fields = ['name', 'code']

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_filter = ['academic_year']
    search_fields = ['name', 'section']

# Register other models
admin.site.register(Attendance)
admin.site.register(ReportCard)