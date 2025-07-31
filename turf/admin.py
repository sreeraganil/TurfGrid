from django.contrib import admin
from .models import Turf, TurfSchedule, TurfBooking, TurfReview, Amenity, Favourite


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)

@admin.register(Turf)
class TurfAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'sport_type','is_verified', 'owner', 'is_active', 'created_at')
    list_filter = ('sport_type', 'surface_type', 'is_active')
    search_fields = ('name', 'address', 'city')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['owner']


@admin.register(TurfSchedule)
class TurfScheduleAdmin(admin.ModelAdmin):
    list_display = ('turf', 'day', 'start_time', 'end_time', 'price', 'is_peak', 'is_available')
    list_filter = ('day', 'is_peak', 'is_available')
    search_fields = ('turf__name',)


@admin.register(TurfBooking)
class TurfBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'turf', 'user', 'booking_date', 'start_time', 'end_time', 'status', 'total_amount')
    list_filter = ('status', 'booking_date')
    search_fields = ('turf__name', 'user__username')
    autocomplete_fields = ['turf', 'user']


@admin.register(TurfReview)
class TurfReviewAdmin(admin.ModelAdmin):
    list_display = ('turf', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('turf__name', 'user__username')
    autocomplete_fields = ['turf', 'user']


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'turf', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'turf__name']
