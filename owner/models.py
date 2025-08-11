from django.db import models
from turf.models import Turf
from django.utils import timezone
from accounts.models import User

class Notification(models.Model):
    MESSAGE_TYPE = [
        ('info', 'Info'),
        ('offer', 'Offer'),
        ('alert', 'Alert'),
    ]
    
    title = models.CharField(max_length=100)
    message = models.TextField()
    type = models.CharField(max_length=10, choices=MESSAGE_TYPE, default='info')
    turfs = models.ManyToManyField(Turf, blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def is_visible(self):
        today = timezone.now().date()
        return (
            self.is_active and
            (self.start_date <= today) and
            (not self.end_date or today <= self.end_date)
        )

    def __str__(self):
        return self.title
    


class UserNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)