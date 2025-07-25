from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages
from .forms import CustomUserCreationForm


@never_cache
def login_view(request):
    if request.user.is_authenticated :
        return redirect('dashboard')
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            messages.success(request, "Login successfull")
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

