# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Parent, Student, Teacher

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_verified')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active', 'is_verified')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {'fields': ('user_type', 'phone', 'address', 'profile_picture', 'date_of_birth', 'is_verified')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Parent)
admin.site.register(Student)
admin.site.register(Teacher)