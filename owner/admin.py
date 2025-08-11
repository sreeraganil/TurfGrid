from django.contrib import admin
from .models import Notification, UserNotification

# Register your models here.

@admin.register(Notification)
class AdminNotification(admin.ModelAdmin):
    list_display = ('title', 'message', 'type', 'display_turfs', 'start_date', 'end_date', 'is_active')

    def display_turfs(self, obj):
        return ", ".join([turf.name for turf in obj.turfs.all()])
    display_turfs.short_description = 'Turfs'

@admin.register(UserNotification)
class AdminUserNotification(admin.ModelAdmin):
    pass