from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required

@never_cache
def landing_view(request):
    if request.user.is_authenticated :
        return redirect('dashboard')
    return render(request, 'landing.html')

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'dashboard.html')

