from django.shortcuts import render
from .models import Turf

def find_turf(request):
    turfs = Turf.objects.all()
    context = {
        'turfs': turfs,
        'count': len(turfs)
    }
    return render(request, 'find_turf.html', context)


def turf_detail(request):
    return render(request, 'turf_detail.html')
