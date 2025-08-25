# academics/models.py
from django.db import models

class Class(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=50)
    section = models.CharField(max_length=10, blank=True)
    academic_year = models.CharField(max_length=9)  # Format: 2023-2024
    teacher_class_taught = models.ForeignKey('accounts.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='classes_taught')
    
    class Meta:
        verbose_name_plural = "Classes"
        unique_together = ('name', 'section', 'academic_year')
    
    def __str__(self):
        return f"{self.name} {self.section} - {self.academic_year}"


class Subject(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Attendance(models.Model):
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    class_instance = models.ForeignKey(Class, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=(
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused')
    ))
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('student', 'date')
    
    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"


class Grade(models.Model):
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.CharField(max_length=20)  # e.g., "First Term", "Mid Term"
    academic_year = models.CharField(max_length=9)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    maximum_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('student', 'subject', 'term', 'academic_year')
    
    def percentage(self):
        return (self.score / self.maximum_score) * 100
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.term}: {self.score}/{self.maximum_score}"


class ReportCard(models.Model):
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    term = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=9)
    overall_grade = models.CharField(max_length=5, blank=True)
    class_position = models.PositiveIntegerField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey('accounts.Teacher', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('student', 'term', 'academic_year')
    
    def __str__(self):
        return f"Report Card - {self.student} - {self.term} {self.academic_year}"