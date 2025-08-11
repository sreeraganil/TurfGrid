from django.urls import path
from . import views


urlpatterns = [
    path('', views.owner_dashboard, name = 'owner_dashboard'),
    path('turf/<int:id>/', views.turf_detail, name='owner_manage_turf'),
    path('turf/<int:id>/update/', views.turf_update, name='owner_update_turf_status'),
    path('turf/<int:id>/delete/', views.turf_delete, name='owner_delete_turf'),
    path('manage-bookings/', views.manage_bookings, name='manage_bookings'),
    path('payments/', views.view_payments, name='view_payments'),
    path('notifications/create/', views.create_notification, name='create_notification'),
    path('notifications/<int:notification_id>/edit/', views.edit_notification, name='edit_notification'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'), 
    path('turf/<int:turf_id>/images/', views.add_turf_images, name='add_turf_images'), 
    path('image/<int:image_id>/delete/', views.delete_image, name='delete_image'), 
]
