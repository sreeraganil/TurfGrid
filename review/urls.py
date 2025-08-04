from django.urls import path
from . import views

urlpatterns = [
    path('turf/<int:turf_id>/', views.add_review, name='add_review'),
    path('turf/<int:review_id>/update/', views.edit_review, name='edit_review'),
    path('turf/<int:review_id>/delete/', views.delete_review, name='delete_review'),
]
