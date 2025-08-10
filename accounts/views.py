from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import CustomUserCreationForm
from turf.models import Favourite, Turf, TurfBooking
from datetime import date


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
