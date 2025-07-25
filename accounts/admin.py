from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'fname', 'lname', 'email', 'phone', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('fname', 'lname', 'email')
