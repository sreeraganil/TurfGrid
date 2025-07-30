from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'fname', 'lname', 'email', 'phone', 'role', 'created_at', 'is_blocked', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_active', 'role')
    search_fields = ('fname', 'lname', 'email')
