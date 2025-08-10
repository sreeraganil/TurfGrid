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
from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
import qrcode
from datetime import datetime

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
@never_cache
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(TurfBooking, id=int(booking_id), user=request.user)
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


@login_required
def print_receipt(request, booking_id):
    order = get_object_or_404(TurfBooking, id=booking_id)
    
    # Create a buffer for the PDF
    buffer = BytesIO()
    
    # Create the PDF object
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=4, border=4)
    qr.add_data(f"Booking ID: {order.id}\nTurf: {order.turf.name}\nDate: {order.booking_date}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    
    # Styles
    # styles = getSampleStyleSheet()
    # title_style = ParagraphStyle(
    #     'Title',
    #     parent=styles['Heading1'],
    #     fontSize=18,
    #     textColor=colors.HexColor('#4f46e5'),
    #     spaceAfter=14
    # )
    # heading_style = ParagraphStyle(
    #     'Heading2',
    #     parent=styles['Heading2'],
    #     fontSize=14,
    #     textColor=colors.HexColor('#4f46e5'),
    #     spaceAfter=6
    # )
    # normal_style = styles['Normal']
    
    # Header
    p.setFillColor(colors.HexColor('#4f46e5'))
    p.setFont("Helvetica-Bold", 24)
    p.drawString(72, height - 72, "TurfGrid")
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica", 12)
    p.drawString(width - 200, height - 72, "Booking Receipt")
    p.drawString(width - 200, height - 90, f"#{order.id}")
    
    # Date and status
    p.setFont("Helvetica", 10)
    p.drawString(72, height - 120, f"Issued: {datetime.now().strftime('%b %d, %Y')}")
    p.drawString(72, height - 140, f"Status: {order.get_status_display()}")
    
    # Booking Information
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, height - 180, "Booking Information")
    
    p.setFont("Helvetica", 10)
    p.drawString(72, height - 200, f"Booking Reference: #{order.id}")
    p.drawString(72, height - 220, f"Date: {order.booking_date}")
    p.drawString(72, height - 240, f"Time Slot: {order.start_time.strftime('%H:%M')} - {order.end_time.strftime('%H:%M')}")
    p.drawString(72, height - 260, f"Booked On: {order.created_at.strftime('%b %d, %Y %H:%M')}")
    
    # Turf Information
    p.setFont("Helvetica-Bold", 14)
    p.drawString(300, height - 180, "Turf Information")
    
    p.setFont("Helvetica", 10)
    p.drawString(300, height - 200, f"Turf Name: {order.turf.name}")
    p.drawString(300, height - 220, f"Location: {order.turf.location}")
    p.drawString(300, height - 240, f"Contact: {order.turf.owner.phone or '-'}")
    
    # Customer Information
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, height - 300, "Customer Information")
    
    p.setFont("Helvetica", 10)
    p.drawString(72, height - 320, f"Name: {order.user.fname} {order.user.lname}")
    p.drawString(72, height - 340, f"Email: {order.user.email}")
    p.drawString(72, height - 360, f"Phone: {getattr(order.user, 'phone', '-')}")
    
    # Draw QR code
    qr_img_reader = ImageReader(qr_buffer)
    p.drawImage(qr_img_reader, width - 120, height - 360, width=100, height=100)
    p.setFont("Helvetica", 8)
    p.drawString(width - 120, height - 370, "Scan for booking details")
    
    # Start Y position after customer info
    y_position = height - 420  

    # Payment Summary Title
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, y_position, "Payment Summary")

    # Move Y down before table
    y_position -= 20  

    data = [
        ["Description", "Amount (Rupees)"],
        ["Turf Booking Fee", f"{order.total_amount:.2f}"],
        ["Taxes & Fees", "0.00"],
        ["Discount", "0.00"],
        ["Total Amount", f"{order.total_amount:.2f}"],
        ["Payment Method", order.payment_method or "Online Payment"],
        ["Payment Status", f"Paid on {order.created_at.strftime('%b %d, %Y')}"]
    ]

    table = Table(data, colWidths=[300, 110])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e7ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))

    table_width, table_height = table.wrap(0, 0)
    table.drawOn(p, 72, y_position - table_height)

    # Update y_position after table
    y_position -= (table_height + 30)
    
    # Terms and Conditions
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, y_position, "Terms & Conditions")

    # Move below heading
    y_position -= 20

    terms = [
        "1. This receipt serves as proof of booking. Please present it when you arrive.",
        "2. Cancellations must be made at least 24 hours before the booking time for a full refund.",
        "3. TurfGrid reserves the right to cancel bookings due to unforeseen circumstances.",
        "4. For any disputes, please contact our support team within 7 days of booking."
    ]

    p.setFont("Helvetica", 10)
    for term in terms:
        p.drawString(72, y_position, term)
        y_position -= 20

    
    # Footer
    p.setFont("Helvetica", 9)
    p.drawCentredString(width/2, 50, "Thank you for choosing TurfGrid! We hope you enjoy your game.")
    p.drawCentredString(width/2, 35, "For any queries, contact support@turfgrid.com or call +91 98765 43210")
    p.drawCentredString(width/2, 20, "This is an electronically generated receipt. No signature required.")
    
    # Watermark
    p.saveState()
    p.translate(width/2, height/2)
    p.rotate(45)
    try:
        p.setFillColor(colors.HexColor('#4f46e5'))
        p.setFillAlpha(0.05)
    except AttributeError:
        p.setFillColor(colors.HexColor('#d0d4f7'))  # light color fallback
    p.setFont("Helvetica-Bold", 72)
    p.drawCentredString(0, 0, "TURFGRID")
    p.restoreState()
    
    # Save the PDF
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{order.id}.pdf"'
    return response



