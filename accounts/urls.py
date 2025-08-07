from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.login_view, name = 'login'),
    path('register/', views.register_view, name = 'register'),
    path('logout/', views.logout_view, name = 'logout'),
    path('settings/', views.settings, name = 'settings'),
    path('update-password/', views.update_password, name = 'update_password'),
    path('update-profile/', views.update_profile, name = 'update_profile'),
    path('toggle-favourite/<int:turf_id>', views.toggle_favourite, name = 'toggle_favourite'),
    path('bookings', views.bookings, name = 'bookings'),
]
