from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['fname', 'lname', 'phone', 'email', 'password1', 'password2', 'terms_and_conditions']
