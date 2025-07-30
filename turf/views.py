from django.shortcuts import render
from .models import Turf, Amenity, TurfBooking
from django.db.models import Q
from datetime import datetime

def find_turf(request):
    # Start with all active turfs
    turfs = Turf.objects.filter(is_active=True)

    # --- Get all filter parameters from the request ---
    location_query = request.GET.get('location')
    date_query = request.GET.get('date')
    sport_types = request.GET.getlist('sport_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    amenity_ids = request.GET.getlist('amenities')
    sort_by = request.GET.get('sort_by')

    # --- Apply filters based on parameters ---

    # Location filter (searches name, location, and address)
    if location_query:
        turfs = turfs.filter(
            Q(name__icontains=location_query) |
            Q(location__icontains=location_query) |
            Q(address__icontains=location_query)
        )

    # Date availability filter
    if date_query:
        try:
            booking_date = datetime.strptime(date_query, '%Y-%m-%d').date()
            # Find IDs of turfs that have a confirmed booking on that date
            booked_turf_ids = TurfBooking.objects.filter(
                booking_date=booking_date,
                status='confirmed'
            ).values_list('turf_id', flat=True)
            # Exclude these turfs from the main queryset
            turfs = turfs.exclude(id__in=booked_turf_ids)
        except ValueError:
            # Handle invalid date format gracefully
            pass

    # Sport Type filter
    if sport_types:
        turfs = turfs.filter(sport_type__in=sport_types)

    # Price Range filter
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

    # Amenities filter (finds turfs with ANY of the selected amenities)
    if amenity_ids:
        # The .distinct() is crucial to avoid duplicates
        turfs = turfs.filter(amenities__in=amenity_ids).distinct()

    # --- Apply Sorting ---
    if sort_by == 'price_asc':
        turfs = turfs.order_by('price_per_hour')
    elif sort_by == 'price_desc':
        turfs = turfs.order_by('-price_per_hour')
    elif sort_by == 'rating':
        turfs = turfs.order_by('-rating')
    else: # Default sort
        turfs = turfs.order_by('-created_at')


    context = {
        'turfs': turfs,
        'count': turfs.count(),
        'amenities': Amenity.objects.all(),
        'sport_choices': Turf.SPORT_CHOICES,
        # Pass submitted values back to template to keep filters active
        'values': request.GET
    }
    return render(request, 'find_turf.html', context)


def turf_detail(request, slug):
    turf = Turf.objects.get(slug = slug)
    absolute_url = request.build_absolute_uri()

    # Conditionally build image URL to prevent errors if no image exists
    og_image_url = None
    if turf.image:
        og_image_url = request.build_absolute_uri(turf.image.url)
        
    context = {
        'turf': turf,
        'absolute_url': absolute_url,
        'og_image_url': og_image_url,
    }
    return render(request, 'turf_detail.html', context)
