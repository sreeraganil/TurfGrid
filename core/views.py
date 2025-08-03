from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

@never_cache
def landing_view(request):
    if request.user.is_authenticated :
        return redirect('dashboard')
    return render(request, 'landing.html')

@login_required(login_url='login')
def dashboard(request):
    now = timezone.localtime(timezone.now())
    today = now.date()
    current_time = now.time()

# Filter for bookings that are in the future OR today with a later start_time
    upcoming_bookings = request.user.bookings.filter(
        Q(booking_date__gt=today) | 
        Q(booking_date=today, start_time__gte=current_time)
    )
    context = {
        'upcoming_bookings': upcoming_bookings,
        'now': now,
        'today': today,
        'current_time': current_time
    }
    return render(request, 'dashboard.html', context)

