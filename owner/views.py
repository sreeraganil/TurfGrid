from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Avg
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from turf.models import Turf, TurfBooking, TurfReview
from django.views.decorators.http import require_http_methods
from datetime import datetime, date
from django.contrib.auth.decorators import  user_passes_test

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

    context = {
        'turfs': turfs,
        'total_turfs': turfs.count(),
        'total_bookings': total_bookings,
        'total_earnings': total_earnings,
        'recent_bookings': recent_bookings,
        'average_rating': average_rating,
        'todays_bookings': todays_bookings,
        'recent_reviews': recent_reviews,
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