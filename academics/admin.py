# academics/admin.py
from django.contrib import admin
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