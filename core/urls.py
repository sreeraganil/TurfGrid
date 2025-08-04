from django.urls import path
from . import views


urlpatterns = [
    path('', views.landing_view, name = 'landing'),
    path('dashboard/', views.dashboard, name = 'dashboard'),
    path('about/', views.about, name = 'about'),
    path('contact/', views.contact, name = 'contact'),
]
