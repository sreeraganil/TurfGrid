from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Avg
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from turf.models import Turf, TurfBooking, TurfReview
from django.views.decorators.http import require_http_methods
from datetime import datetime

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
        'STATUS_CHOICES': Turf.STATUS_CHOICES  # Pass the choices to template
    })


@require_http_methods(["GET", "POST"])
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
def turf_delete(request, id):
    turf = get_object_or_404(Turf, id=id)

    if request.method == 'POST':
        turf.delete()
        messages.success(request, 'Turf deleted successfully')
        return redirect(reverse_lazy('owner_dashboard'))

    return render(request, 'turf_confirm_delete.html', {'turf': turf})

def owner_dashboard(request):
    return render(request, 'owner_dashboard.html')