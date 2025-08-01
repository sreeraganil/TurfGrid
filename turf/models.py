from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from accounts.models import User
from accounts.models import User

class Amenity(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    

    
class Turf(models.Model):
    SPORT_CHOICES = [
        ('football', 'Football'),
        ('cricket', 'Cricket'),
        ('tennis', 'Tennis'),
        ('badminton', 'Badminton'),
        ('multi', 'Multi-Sport'),
    ]

    SURFACE_CHOICES = [
        ('natural', 'Natural'),
        ('artificial', 'Artificial'),
        ('clay', 'Clay'),
        ('hard', 'Hard'),
        ('synthetic', 'Synthetic'),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("closed", "Closed"),
        ("maintenance", "Under Maintenance"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role__in': ['owner', 'admin']}, related_name='turf')
    sport_type = models.CharField(max_length=20, choices=SPORT_CHOICES)
    description = models.TextField()
    location = models.CharField(max_length=255)

    address = models.CharField(max_length=255)

    length = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    surface_type = models.CharField(max_length=20, choices=SURFACE_CHOICES)
    capacity = models.PositiveIntegerField()
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)], default=0)
    amenities = models.ManyToManyField(Amenity, blank=True)
    minimum_booking_duration = models.IntegerField(default=1)
    opening = models.TimeField()
    closing = models.TimeField()
    status = models.CharField(choices = STATUS_CHOICES, default='open')
    is_verified = models.BooleanField(default=False)

    image = models.ImageField(upload_to='turfs/images/', null=True, blank=True) 
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.address[:20]}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    


class TurfSchedule(models.Model):
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='schedules')
    day = models.PositiveIntegerField(choices=[(i, day) for i, day in enumerate(
        ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    )])
    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_peak = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['day', 'start_time']


class TurfBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    turf = models.ForeignKey(Turf, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class TurfReview(models.Model):
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['turf', 'user']


class Favourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favourites')
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='favourited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'turf')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} favourited {self.turf.name}"
