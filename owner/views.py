from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Avg, Q
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from turf.models import Turf, TurfBooking, TurfReview, TurfImage
from django.views.decorators.http import require_http_methods
from datetime import datetime, date
from django.contrib.auth.decorators import  user_passes_test
from .models import Notification
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from accounts.models import User
from owner.models import UserNotification

def turf_detail(request, id):
    turf = get_object_or_404(Turf, id=id)
    
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    monthly_bookings = TurfBooking.objects.filter(
        turf=turf,
        booking_date__month=current_month,
        booking_date__year=current_year
    )
    
    stats = {
        'monthly_bookings': monthly_bookings.count(),
        'monthly_revenue': monthly_bookings.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'average_rating': TurfReview.objects.filter(turf=turf).aggregate(Avg('rating'))['rating__avg'] or 0,
        'total_reviews': TurfReview.objects.filter(turf=turf).count()
    }
    
    return render(request, 'manage_turf.html', {
        'turf': turf,
        'stats': stats,
        'STATUS_CHOICES': Turf.STATUS_CHOICES  
    })


@require_http_methods(["GET", "POST"])
@user_passes_test(lambda u: u.is_authenticated and (u.role == "owner" or u.role == "admin"))
def turf_update(request, id):
    turf = get_object_or_404(Turf, id=id)

    if request.method == 'POST':
        status = request.POST.get('status')
        turf.status = status
        turf.save()
        messages.success(request, 'Turf status updated successfully')
        return redirect(reverse('owner_manage_turf', kwargs={'id': turf.id}))

    return render(request, 'update_status.html', {
        'turf': turf,
        'STATUS_CHOICES': Turf.STATUS_CHOICES
    })


@require_http_methods(["GET", "POST"])
@user_passes_test(lambda u: u.is_authenticated and (u.role == "owner" or u.role == "admin"))
def turf_delete(request, id):
    turf = get_object_or_404(Turf, id=id)

    if request.method == 'POST':
        turf.delete()
        messages.success(request, 'Turf deleted successfully')
        return redirect(reverse_lazy('owner_dashboard'))

    return render(request, 'turf_confirm_delete.html', {'turf': turf})



@user_passes_test(lambda u: u.is_authenticated and u.role == "owner")
def owner_dashboard(request):
    turfs = Turf.objects.filter(owner=request.user)

    turf_ids = turfs.values_list('id', flat=True)

    confirmed_bookings = TurfBooking.objects.filter(
        turf_id__in=turf_ids,
        status='confirmed'
    )
    todays_bookings = TurfBooking.objects.filter(
        turf_id__in=turf_ids,
        status='confirmed',
        booking_date=date.today()
    ).count()

    rating = TurfReview.objects.filter(
        turf_id__in = turf_ids
    )
    reviews = TurfReview.objects.filter(
        turf_id__in = turf_ids
    )

    total_bookings = confirmed_bookings.count()
    total_earnings = confirmed_bookings.aggregate(total=Sum('total_amount'))['total'] or 0
    average_rating = rating.aggregate(total=Avg('rating'))['total'] or 0

    recent_bookings = confirmed_bookings.order_by('-created_at')[:5]
    recent_reviews = reviews.order_by('-created_at')[:5]

    active_notifications = Notification.objects.filter(
        Q(turfs__owner=request.user) | Q(turfs__isnull=True),
        is_active=True,
        # start_date__lte=timezone.now().date()
        ).filter(
            Q(end_date__gte=timezone.now().date()) | Q(end_date__isnull=True)
    ).distinct()


    context = {
        'turfs': turfs,
        'total_turfs': turfs.count(),
        'total_bookings': total_bookings,
        'total_earnings': total_earnings,
        'recent_bookings': recent_bookings,
        'average_rating': average_rating,
        'todays_bookings': todays_bookings,
        'recent_reviews': recent_reviews,
        'active_notifications': active_notifications,
        'today': date.today()
    }

    return render(request, 'owner_dashboard.html', context)


@user_passes_test(lambda u: u.is_authenticated and u.role == "owner")
def manage_bookings(request):
    owned_turfs = Turf.objects.filter(owner=request.user)

    turf_ids = owned_turfs.values_list('id', flat=True)

    bookings = TurfBooking.objects.filter(turf_id__in=turf_ids).select_related('user', 'turf').order_by('-booking_date', '-start_time')

    today = request.GET.get('today')
    if today == '1':
        bookings = bookings.filter(booking_date=date.today())

    context = {
        'bookings': bookings,
        'today_only': today == '1'
    }

    return render(request, 'manage_bookings.html', context)



@user_passes_test(lambda u: u.is_authenticated and u.role == "owner")
def view_payments(request):
    owner = request.user
    turfs = Turf.objects.filter(owner=owner)
    turf_ids = turfs.values_list('id', flat=True)

    payments = TurfBooking.objects.filter(
        turf_id__in=turf_ids,
        status='confirmed'  
    ).order_by('-booking_date')

    return render(request, 'view_payments.html', {'payments': payments})



@login_required
def create_notification(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        notification_type = request.POST.get('type')
        turf_id = request.POST.get('turf')
        start_date = request.POST.get('start_date', timezone.now().date())
        end_date = request.POST.get('end_date')
        
        # Get turfs (single or multiple)
        if turf_id:
            turfs = Turf.objects.filter(id=turf_id, owner=request.user)
        else:
            turfs = Turf.objects.filter(owner=request.user)

        if not turfs.exists():
            return redirect('owner_dashboard')

        # Create the notification
        notification = Notification.objects.create(
            title=title,
            message=message,
            type=notification_type,
            start_date=start_date,
            end_date=end_date if end_date else None,
            is_active=True
        )
        notification.turfs.set(turfs)  # M2M assignment

        # Get unique users who booked these turfs
        booked_users = User.objects.filter(
            bookings__turf__in=turfs,
            bookings__status='confirmed'
        ).distinct()

        # Create user-specific notifications
        user_notifications = [
            UserNotification(user=user, notification=notification)
            for user in booked_users
        ]
        UserNotification.objects.bulk_create(user_notifications)

        return redirect('owner_dashboard')

    return redirect('owner_dashboard')

@login_required
def edit_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    # Verify the notification belongs to the owner
    if notification.turfs.exists() and not notification.turfs.filter(owner=request.user).exists():
        return redirect('owner_dashboard')

    
    if request.method == 'POST':
        notification.title = request.POST.get('title')
        notification.message = request.POST.get('message')
        notification.type = request.POST.get('type')
        turf_id = request.POST.get('turf')
        notification.start_date = request.POST.get('start_date', timezone.now().date())
        end_date = request.POST.get('end_date')
        
        notification.turfs = None
        if turf_id:
            notification.turfs = get_object_or_404(Turf, id=turf_id, owner=request.user)
        else :
            notification.turfs = get_object_or_404(Turf, owner=request.user)
        
        notification.end_date = end_date if end_date else None
        notification.save()
        return redirect('owner_dashboard')
    
    return redirect('owner_dashboard')

@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    # Verify the notification belongs to the owner
    if notification.turfs.exists() and not notification.turfs.filter(owner=request.user).exists():
        return redirect('owner_dashboard')
    
    notification.delete()
    return redirect('owner_dashboard')



@user_passes_test(lambda u: u.is_authenticated and u.role == "owner")
def add_turf_images(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)

    if request.method == "POST":
        images = request.FILES.getlist('images')  # Grab multiple files
        for img in images:
            TurfImage.objects.create(turf=turf, image=img)
        return redirect('owner_manage_turf', id=turf.id)  # Change to your actual detail view name

    return render(request, "add_turf_images.html", {"turf": turf})

def delete_image(request, image_id):
    image = TurfImage.objects.get(id = image_id)

    if request.user !=  image.turf.owner:
        return redirect('dashboard')
    
    next = request.GET.get("turf-id")
    
    image.delete()
    return redirect(next)
