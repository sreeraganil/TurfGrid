from django.shortcuts import render, redirect, get_object_or_404
from .models import Turf, Amenity, TurfBooking
from django.db.models import Q, Avg
from datetime import datetime
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from haversine import haversine, Unit
import math
from django.core.paginator import Paginator
from datetime import date

@never_cache
def find_turf(request):
    turfs = Turf.objects.filter(is_active=True, is_verified=True)

    location_query = request.GET.get('location')
    date_query = request.GET.get('date')
    sport_types = request.GET.getlist('sport_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    amenity_ids = request.GET.getlist('amenities')
    sort_by = request.GET.get('sort_by')

    user_lat = request.GET.get('user_lat')
    user_lng = request.GET.get('user_lng')
    user_location = None

    if user_lat and user_lng:
        try:
            user_lat_float = float(user_lat)
            user_lng_float = float(user_lng)
            user_location = (user_lat_float, user_lng_float)

           
            lat_range = 0.45
            lng_range = 0.45 / math.cos(math.radians(user_lat_float))
            turfs = turfs.filter(
                latitude__gte=user_lat_float - lat_range,
                latitude__lte=user_lat_float + lat_range,
                longitude__gte=user_lng_float - lng_range,
                longitude__lte=user_lng_float + lng_range
            )
        except ValueError:
            user_location = None

    if location_query:
        turfs = turfs.filter(
            Q(name__icontains=location_query) |
            Q(location__icontains=location_query) |
            Q(address__icontains=location_query)
        )

    if date_query:
        try:
            booking_date = datetime.strptime(date_query, '%Y-%m-%d').date()
            booked_turf_ids = TurfBooking.objects.filter(
                booking_date=booking_date,
                status='confirmed'
            ).values_list('turf_id', flat=True)
            turfs = turfs.exclude(id__in=booked_turf_ids)
        except ValueError:
            pass

    if sport_types:
        turfs = turfs.filter(sport_type__in=sport_types)

    if min_price:
        try:
            turfs = turfs.filter(price_per_hour__gte=float(min_price))
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            turfs = turfs.filter(price_per_hour__lte=float(max_price))
        except (ValueError, TypeError):
            pass

    if amenity_ids:
        turfs = turfs.filter(amenities__in=amenity_ids).distinct()

    turf_distance_map = {}
    if user_location:
        for turf in turfs:
            if turf.latitude and turf.longitude:
                turf_location = (float(turf.latitude), float(turf.longitude))
                distance = haversine(user_location, turf_location, unit=Unit.KILOMETERS)
                turf_distance_map[turf.id] = round(distance, 2)

    if sort_by == 'price_asc':
        turfs = turfs.order_by('price_per_hour')
    elif sort_by == 'price_desc':
        turfs = turfs.order_by('-price_per_hour')
    elif sort_by == 'rating':
        turfs = list(turfs.annotate(avg_rating=Avg('reviews__rating')))
        turfs.sort(key=lambda t: t.avg_rating if t.avg_rating is not None else -1, reverse=True)
    elif user_location:
        turfs = sorted(turfs, key=lambda t: turf_distance_map.get(t.id, float('inf')))
    else:
        turfs = turfs.order_by('-created_at')

    selected_sports = request.GET.getlist('sport_type')
    selected_amenities = request.GET.getlist('amenities')
    favourited_turf_ids = []
    if request.user.is_authenticated:
        favourited_turf_ids = [fav.turf.id for fav in request.user.favourites.all()]

    for turf in turfs:
        turf.distance = turf_distance_map.get(turf.id)

    context = {
        'turfs': turfs,
        'count': len(turfs),
        'amenities': Amenity.objects.all(),
        'sport_choices': Turf.SPORT_CHOICES,
        'selected_sports': selected_sports,
        'selected_amenities': selected_amenities,
        'values': request.GET,
        'favourited_turf_ids': favourited_turf_ids
    }

    return render(request, 'find_turf.html', context)


def turf_detail(request, slug):
    turf = get_object_or_404(Turf, slug=slug)
    absolute_url = request.build_absolute_uri()

    og_image_url = request.build_absolute_uri(turf.image.url) if turf.image else None

    if not turf.is_verified:
        messages.error(request, "Please note: This turf is yet to be verified by the admin. Book at your own risk.")

    favourited_turf_ids = []
    has_reviewed = False
    if request.user.is_authenticated:
        favourited_turf_ids = [fav.turf.id for fav in request.user.favourites.all()]
        has_reviewed = turf.reviews.filter(user=request.user).exists()


    context = {
        'turf': turf,
        'absolute_url': absolute_url,
        'og_image_url': og_image_url,
        'favourited_turf_ids': favourited_turf_ids,
        "has_reviewed": has_reviewed,
    }
    return render(request, 'turf_detail.html', context)



@login_required(login_url='login')
def add_turf(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        sport_type = request.POST.get('sport_type')
        description = request.POST.get('description')
        location = request.POST.get('location')
        address = request.POST.get('address')
        length = request.POST.get('length')
        width = request.POST.get('width')
        surface_type = request.POST.get('surface_type')
        capacity = request.POST.get('capacity')
        price_per_hour = request.POST.get('price_per_hour')
        minimum_booking_duration = request.POST.get('minimum_booking_duration')
        opening = request.POST.get('opening')
        closing = request.POST.get('closing')
        status = request.POST.get('status')
        image = request.FILES.get('image')
        amenities = request.POST.getlist('amenities')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        turf = Turf.objects.create(
            owner=request.user,
            name=name,
            sport_type=sport_type,
            description=description,
            location=location,
            address=address,
            length=length,
            width=width,
            surface_type=surface_type,
            capacity=capacity,
            price_per_hour=price_per_hour,
            minimum_booking_duration=minimum_booking_duration,
            opening=opening,
            closing=closing,
            status=status,
            image=image,
            latitude=latitude,
            longitude=longitude
        )
        turf.amenities.set(amenities)

        messages.success(request, "Turf added successfully")
        
        return redirect('owner_dashboard')

    context = {
        'amenities': Amenity.objects.all()
    }
    return render(request, 'add_turf.html', context)





@login_required(login_url='login')
def favourites(request):
    return render(request, 'manage_favourites.html')



@login_required(login_url='login')
def book_turf(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    # today = timezone.localdate()
    today = date.today()

    # Handle date selection from query parameters
    selected_date_str = request.GET.get('booking_date')
    if selected_date_str:
        try:
            booking_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            booking_date = today
    else:
        booking_date = today

    # Calculate available hours
    selected_duration = float(request.GET.get('duration', turf.minimum_booking_duration))
    if booking_date:
        available_hours = turf.get_available_hours(booking_date, selected_duration)

        # Exclude past time slots for today
        if booking_date == today:
            now = timezone.localtime().time()
            available_hours = [hour for hour in available_hours if hour > now]
    
    # Calculate max possible duration
    max_duration = turf.get_max_booking_duration()
    duration_options = []
    current = 1
    while current <= max_duration:
        duration_options.append(current)
        current += 1


    if request.method == 'POST':
        # Handle form submission
        booking_date = request.POST.get('booking_date')
        start_time = request.POST.get('start_time')
        try:
            duration = Decimal(str(request.POST.get('duration')))
        except InvalidOperation:
            messages.error(request, "Invalid duration.")
            return redirect('book_turf', turf_id=turf.id)
        notes = request.POST.get('notes', '')

        try:
            # Create booking
            start_datetime = datetime.strptime(f"{booking_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + timedelta(hours=float(duration))


            service_fee = Decimal('80.00')
            
            booking = TurfBooking(
                turf=turf,
                user=request.user,
                booking_date=booking_date,
                start_time=start_time,
                end_time=end_datetime.time(),
                total_amount=(turf.price_per_hour * duration) + service_fee, 
                status = 'confirmed',
                notes=notes
            )
            booking.save()

            messages.success(request, 'Your booking has been confirmed!')
            return redirect('booking_confirmation', booking_id=booking.id)
        
        except Exception as e:
            messages.error(request, f'Error creating booking: {str(e)}')
            return redirect('book_turf', turf_id=turf.id)

    context = {
        'turf': turf,
        'today': today,
        'available_hours': available_hours,
        'duration_options': duration_options,
        'selected_date': booking_date,
        'selected_duration': selected_duration,
        'values':request.GET,
    }
    return render(request, 'book_turf.html', context)


@login_required(login_url='login')
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(TurfBooking, id=booking_id, user=request.user)
    if booking.shown:
        return redirect('booking_detail', booking_id = booking.id)
    else:
        booking.shown = True
        booking.save()
    return render(request, 'booking_confirmation.html', {'booking': booking})


def upcoming(request):
    today = date.today()

    # Filter only bookings for this user that are in the future
    bookings_qs = (
        TurfBooking.objects
        .filter(user=request.user, booking_date__gte=today)
        .order_by('booking_date', 'start_time')
    )


    # Pagination — 6 bookings per page
    paginator = Paginator(bookings_qs, 6)
    page_number = request.GET.get('page')
    bookings = paginator.get_page(page_number)

    return render(request, 'upcoming.html', {
        'bookings': bookings
    })





@login_required
def booking_detail(request, booking_id):
    # Get the booking or return 404
    booking = get_object_or_404(TurfBooking, id=booking_id, user=request.user)
    
    # Calculate additional context data
    context = {
        'booking': booking,
        'page_title': f"Booking #{booking.id} - {booking.turf.name}",
    }
    
    return render(request, 'booking_detail.html', context)



@login_required
def cancel_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(TurfBooking, id=booking_id, user=request.user)
        
        # Check if booking can be cancelled
        if booking.status not in ['pending', 'confirmed']:
            messages.error(request, "This booking cannot be cancelled.")
            return redirect('booking_detail', booking_id=booking.id)
            
        if booking.is_past:
            messages.error(request, "Past bookings cannot be cancelled.")
            return redirect('booking_detail', booking_id=booking.id)
            
        # Update booking status
        booking.status = 'cancelled'
        booking.save()
        
        messages.success(request, "Your booking has been cancelled successfully.")
        return redirect('booking_detail', booking_id=booking.id)
    
    return redirect('bookings')