from django.urls import path
from . import views


urlpatterns = [
    path("", views.find_turf, name = 'find_turf'),
    path("turf-detail/<str:slug>", views.turf_detail, name = 'turf_detail'),
    path("add-turf", views.add_turf, name = 'add_turf'),
    path("favourites", views.favourites, name = 'favourites'),
]
