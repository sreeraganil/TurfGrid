from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import User
from django.contrib.sessions.models import Session
from turf.models import Turf, TurfBooking, TurfReview
from django.db.models import Sum, Q
from datetime import date
from owner.models import Notification
from django.utils import timezone

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    # User statistics
    users_count = User.objects.count()
    
    # Turf statistics
    turfs_count = Turf.objects.count()
    
    # Booking statistics
    todays_bookings_count = TurfBooking.objects.filter(booking_date=date.today()).count()
    total_revenue = TurfBooking.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Get recent data for tables
    users = User.objects.all().order_by('-created_at')[:10]
    turfs = Turf.objects.all().order_by('-created_at')[:10]
    bookings = TurfBooking.objects.all().order_by('-created_at')[:10]
    reviews = TurfReview.objects.all().order_by('-created_at')[:5]


    notifications = Notification.objects.all().order_by('-start_date')
    active_notifications_count = Notification.objects.filter(
        is_active=True,
        start_date__lte=timezone.now().date()
    ).filter(
        Q(end_date__gte=timezone.now().date()) | Q(end_date__isnull=True)
    ).count()
    
    context = {
        'users_count': users_count,
        'turfs_count': turfs_count,
        'todays_bookings_count': todays_bookings_count,
        'total_revenue': total_revenue,
        'users': users,
        'turfs': turfs,
        'bookings': bookings,
        'reviews': reviews,
        'notifications': notifications,
        'active_notifications_count': active_notifications_count,
    }
    
    return render(request, 'admin-dashboard.html', context)


@login_required
def verify_turf(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    turf.is_verified = True
    turf.save()
    return redirect('admin_dashboard')  # or redirect to a list

@login_required
def unverify_turf(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    turf.is_verified = False
    turf.save()
    return redirect('admin_dashboard')


def is_admin(user):
    return user.is_staff or user.is_superuser

@user_passes_test(is_admin)
def block_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_blocked = True
    user.save()

    sessions = Session.objects.all()
    for session in sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id):
            session.delete()

    return redirect('admin_dashboard')


@user_passes_test(is_admin)
def unblock_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_blocked = False
    user.save()
    return redirect('admin_dashboard')