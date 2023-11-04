from django.core.mail import send_mail
from .models import FailedLoginAttempt


def alert_for_suspicious_activity(username):
    # Create or update a record of the failed login attempt
    attempt, created = FailedLoginAttempt.objects.get_or_create(
        username=username,
        defaults={'attempts': 1},
    )
    if not created:
        attempt.attempts += 1
        attempt.save()

    # Check if the number of failed attempts is above a certain threshold
    if attempt.attempts > 5:  # for example, if there are more than 5 attempts
        # Send an email alert to the admin
        send_mail(
            'Suspicious Login Activity Detected',
            f'Multiple failed login attempts for user: {username}',
            'from@example.com',
            ['admin@example.com'],
            fail_silently=False,
        )
        # Reset the attempt count after alerting
        attempt.attempts = 0
        attempt.save()
