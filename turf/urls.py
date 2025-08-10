from django.urls import path
from . import views


urlpatterns = [
    path("", views.find_turf, name = 'find_turf'),
    path("turf-detail/<str:slug>", views.turf_detail, name = 'turf_detail'),
    path("add-turf", views.add_turf, name = 'add_turf'),
    path("favourites", views.favourites, name = 'favourites'),    
    path('<int:turf_id>/book/', views.book_turf, name='book_turf'),
    path('booking/<int:booking_id>/confirmation/', views.booking_confirmation, name='booking_confirmation'),
    path('upcoming', views.upcoming, name='upcoming'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
]
