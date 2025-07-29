from django.urls import path
from . import views


urlpatterns = [
    path("", views.find_turf, name = 'find_turf'),
    path("turf-detail", views.turf_detail, name = 'turf_detail'),
]
