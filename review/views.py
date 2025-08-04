from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from turf.models import Turf, TurfReview
from django.contrib import messages

@login_required
@never_cache
def add_review(request, turf_id):
    turf = get_object_or_404(Turf, id=turf_id)
    
    if TurfReview.objects.filter(turf=turf, user=request.user).exists():
        return redirect("turf_detail", slug=turf.slug)

    if request.method == "POST":
        rating = int(request.POST["rating"])
        comment = request.POST["comment"]
        TurfReview.objects.create(turf=turf, user=request.user, rating=rating, comment=comment)
        messages.success(request, "Review added successfully!")
        return redirect("turf_detail", slug=turf.slug)

    return render(request, "add_review.html", {"turf": turf})


@login_required
@never_cache
def edit_review(request, review_id):
    review = get_object_or_404(TurfReview, id=review_id)
    
    # Ensure only the review owner can edit
    if request.user != review.user:
        messages.error(request, "You can only edit your own reviews.")
        return redirect('turf_detail', slug=review.turf.slug)
    
    if request.method == "POST":
        review.rating = int(request.POST.get("rating"))
        review.comment = request.POST.get("comment")
        review.save()
        messages.success(request, "Review updated successfully!")
        return redirect('turf_detail', slug=review.turf.slug)
    
    return render(request, 'edit_review.html', {
        'review': review,
        'turf': review.turf
    })

@login_required
@never_cache
def delete_review(request, review_id):
    review = get_object_or_404(TurfReview, id=review_id)

    if request.user != review.user and request.user.role != 'admin':
        messages.error(request, "You can only delete your own reviews.")
        return redirect('turf_detail', slug=review.turf.slug)

    review.delete()
    messages.success(request, "Your review has been successfully deleted.")

    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)

    # fallback
    return redirect('turf_detail', slug=review.turf.slug)
