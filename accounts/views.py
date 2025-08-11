from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import CustomUserCreationForm
from turf.models import Favourite, Turf, TurfBooking
from datetime import date
from django.db.models import Q
from owner.models import Notification, UserNotification
from django.utils import timezone
from django.core.paginator import Paginator


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        
        if user:
            if getattr(user, 'is_blocked', False):
                messages.error(request, 'Your account has been blocked by the admin')
                return render(request, 'login.html')
            login(request, user)
            messages.success(request, "Login successful")
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return render(request, 'login.html')

    return render(request, 'login.html')


@never_cache
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = CustomUserCreationForm()

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        try:
            if form.is_valid():
                form.save()
                return redirect('login')
            else:
                field, errors = next(iter(form.errors.items()))
                messages.error(request, f"{field.capitalize()}: {errors[0]}")
        except Exception as e:
            print("Error during form processing:", e)
            messages.error(request, "A server error occurred. Please try again.")
    
    return render(request, 'register.html', {'form': form})


@never_cache
def logout_view(request):
    logout(request)
    messages.success(request, 'Logout successfull')
    return redirect('login')


@login_required(login_url='login')
def settings(request):
    return render(request, 'settings.html')


@login_required(login_url='login')
def update_password(request):
    if request.method == 'POST':
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        if not request.user.check_password(current):
            messages.error(request, 'Current password is incorrect.')
            return redirect('settings')
        elif new != confirm:
            messages.error(request, 'New passwords do not match.')
            return redirect('settings')
        elif len(new) < 8:
            messages.error(request, 'New password must be at least 8 characters.')
            return redirect('settings')
        else:
            request.user.set_password(new)
            request.user.save()
            update_session_auth_hash(request, request.user) 
            messages.success(request, 'Password updated successfully.')
            return redirect('dashboard')

    return render(request, 'settings.html')


@login_required(login_url='login')
def update_profile(request):
    if request.method == 'POST':
        fname = request.POST['fname']
        lname = request.POST['lname']
        phone = request.POST['phone']
        profile_pic = request.FILES.get('image')

        request.user.fname = fname
        request.user.lname = lname
        request.user.phone = phone
        request.user.profile_pic = profile_pic

        request.user.save()
        messages.success(request, "Profile updated successfully")
        return redirect('settings')
    
    return render(request, 'settings.html')



@login_required
@never_cache
def toggle_favourite(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    favourite, created = Favourite.objects.get_or_create(user=request.user, turf=turf)

    if not created:
        favourite.delete()

    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('find_turf')


@login_required
@never_cache
def bookings(request):
    status = request.GET.get('status')
    today = date.today()

    if status == 'past':
        bookings = TurfBooking.objects.filter(
            user=request.user,
            booking_date__lt=today
        ).order_by('-booking_date')

    elif status == 'upcoming':
        bookings = TurfBooking.objects.filter(
            user=request.user,
            booking_date__gte=today
        ).order_by('booking_date')

    else:
        bookings = request.user.bookings.all().order_by('-booking_date')

    return render(request, "bookings.html", {
        'bookings': bookings,
        'status': status
    })




@login_required
def notifications_list(request):
    # Get all notifications for the current user
    user_notifications = request.user.notifications.all().order_by('-created_at')
    
    # Apply filters
    search_query = request.GET.get('search')
    type_filter = request.GET.get('type')
    status_filter = request.GET.get('status')

    if search_query:
        user_notifications = user_notifications.filter(
            Q(notification__title__icontains=search_query) | 
            Q(notification__message__icontains=search_query))
    
    if type_filter:
        user_notifications = user_notifications.filter(notification__type=type_filter)
    
    if status_filter == 'read':
        user_notifications = user_notifications.filter(is_read=True)
    elif status_filter == 'unread':
        user_notifications = user_notifications.filter(is_read=False)

    # Count unread notifications
    unread_count = request.user.notifications.filter(is_read=False).count()

    # Pagination
    paginator = Paginator(user_notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'user_notifications': page_obj,
        'unread_count': unread_count,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
    }
    return render(request, 'notifications_list.html', context)

@login_required
def mark_notification_read(request, notification_id):
    user_notification = get_object_or_404(
        UserNotification, 
        id=notification_id, 
        user=request.user
    )
    user_notification.is_read = True
    user_notification.save()
    return redirect('notifications_list')

@login_required
def delete_notification(request, notification_id):
    user_notification = get_object_or_404(
        UserNotification, 
        id=notification_id, 
        user=request.user
    )
    user_notification.delete()
    return redirect('notifications_list')