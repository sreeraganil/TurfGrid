from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache

@never_cache
def landing_view(request):
    if request.user.is_authenticated :
        return redirect('dashboard')
    return render(request, 'landing.html')
