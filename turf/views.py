from django.shortcuts import render, redirect
from .models import Turf, Amenity, TurfBooking
from django.db.models import Q
from datetime import datetime
from django.contrib import messages
from django.views.decorators.cache import never_cache

@never_cache
def find_turf(request):
    turfs = Turf.objects.filter(is_active = True, is_verified = True)

    location_query = request.GET.get('location')
    date_query = request.GET.get('date')
    sport_types = request.GET.getlist('sport_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    amenity_ids = request.GET.getlist('amenities')
    sort_by = request.GET.get('sort_by')

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

    if sort_by == 'price_asc':
        turfs = turfs.order_by('price_per_hour')
    elif sort_by == 'price_desc':
        turfs = turfs.order_by('-price_per_hour')
    elif sort_by == 'rating':
        turfs = turfs.order_by('-rating')
    else:
        turfs = turfs.order_by('-created_at')


    selected_sports = request.GET.getlist('sport_type')
    selected_amenities = request.GET.getlist('amenities')

    favourited_turf_ids = []
    if request.user.is_authenticated:
        favourited_turf_ids = [fav.turf.id for fav in request.user.favourites.all()]


    context = {
        'turfs': turfs,
        'count': turfs.count(),
        'amenities': Amenity.objects.all(),
        'sport_choices': Turf.SPORT_CHOICES,
        'selected_sports': selected_sports,
        'selected_amenities': selected_amenities,
        'values': request.GET,
        'favourited_turf_ids': favourited_turf_ids
    }

    return render(request, 'find_turf.html', context)


def turf_detail(request, slug):
    turf = Turf.objects.get(slug = slug)
    absolute_url = request.build_absolute_uri()

    og_image_url = None
    if turf.image:
        og_image_url = request.build_absolute_uri(turf.image.url)

    if not turf.is_verified:
        messages.error(request, "Please note: This turf is yet to be verified by the admin. Book at your own risk.")

    favourited_turf_ids = []
    if request.user.is_authenticated:
        favourited_turf_ids = [fav.turf.id for fav in request.user.favourites.all()]
        
    context = {
        'turf': turf,
        'absolute_url': absolute_url,
        'og_image_url': og_image_url,
        'favourited_turf_ids': favourited_turf_ids
    }
    return render(request, 'turf_detail.html', context)




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
            image=image
        )
        turf.amenities.set(amenities)

        messages.success(request, "Turf added successfully")
        
        return redirect('owner_dashboard')

    context = {
        'amenities': Amenity.objects.all()
    }
    return render(request, 'add_turf.html', context)


def favourites(request):
    return render(request, 'manage_favourites.html')