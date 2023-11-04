from django.shortcuts import render
from .models import FailedLoginAttempt








def login_view(request):
    # Your existing login logic...
    username = request.POST.get('username')
    attempt = FailedLoginAttempt.objects.filter(username=username).first()

    if attempt and attempt.is_locked_out():
        # Inform the user that the account is locked
        # Render a message or redirect as appropriate
        return render(request, 'lockout_message.html', context={})