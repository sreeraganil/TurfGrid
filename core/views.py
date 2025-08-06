from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail
from django.contrib import messages


@never_cache
def landing_view(request):
    if request.user.is_authenticated :
        return redirect('dashboard')
    return render(request, 'landing.html')



@login_required(login_url='login')
@never_cache
def dashboard(request):
    now = timezone.localtime(timezone.now())
    today = now.date()
    current_time = now.time()

# Filter for bookings that are in the future OR today with a later start_time
    upcoming_bookings = request.user.bookings.filter(
        Q(booking_date__gt=today) | 
        Q(booking_date=today, start_time__gte=current_time)
    )

    user_bookings = request.user.bookings.all().order_by('-created_at')

    context = {
        'upcoming_bookings': upcoming_bookings,
        'now': now,
        'today': today,
        'current_time': current_time,
        'user_bookings': user_bookings
    }
    return render(request, 'dashboard.html', context)


def about(request):
    return render(request, 'about.html')



def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # Create styled HTML email
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #6b46c1;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    padding: 20px;
                    background-color: #f9f9f9;
                    border: 1px solid #ddd;
                    border-top: none;
                    border-radius: 0 0 8px 8px;
                }}
                .footer {{
                    margin-top: 20px;
                    padding: 10px;
                    text-align: center;
                    font-size: 0.8em;
                    color: #666;
                }}
                .message {{
                    white-space: pre-line;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>New Contact Message</h2>
            </div>
            <div class="content">
                <p><strong>From:</strong> {name} ({email})</p>
                <p><strong>Subject:</strong> {subject}</p>
                <div class="message">
                    <strong>Message:</strong>
                    <p>{message}</p>
                </div>
            </div>
            <div class="footer">
                <p>This message was sent from the contact form on your website.</p>
            </div>
        </body>
        </html>
        """

        # Plain text version for email clients that don't support HTML
        plain_message = f"""
        New Contact Message
        -------------------
        From: {name} ({email})
        Subject: {subject}
        
        Message:
        {message}
        """

        send_mail(
            subject=f"New Contact Message: {subject}",
            message=plain_message,
            from_email=f"{name} <{email}>", 
            recipient_list=["sreekuttankottakkal@gmail.com"],
            html_message=html_message,
            fail_silently=False,
        )

        messages.success(request, "Thanks for reaching out! We'll get back to you soon.")
        return redirect('contact')
    
    return render(request, 'contact.html')