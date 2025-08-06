from django.urls import path
from . import views


urlpatterns = [
    path('', views.owner_dashboard, name = 'owner_dashboard'),
    path('turf/<int:id>/', views.turf_detail, name='owner_manage_turf'),
    path('turf/<int:id>/update/', views.turf_update, name='owner_update_turf_status'),
    path('turf/<int:id>/delete/', views.turf_delete, name='owner_delete_turf'),
    path('manage-bookings/', views.manage_bookings, name='manage_bookings'),
    path('payments/', views.view_payments, name='view_payments'),
]
