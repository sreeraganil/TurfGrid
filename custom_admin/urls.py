from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name = 'admin_dashboard'),
    path('turf/<int:turf_id>/verify/', views.verify_turf, name='verify_turf'),
    path('turf/<int:turf_id>/unverify/', views.unverify_turf, name='unverify_turf'),
    path('user/<int:user_id>/block/', views.block_user, name='block_user'),
    path('user/<int:user_id>/unblock/', views.unblock_user, name='unblock_user'),
]
