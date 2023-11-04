from django.core.mail import send_mail
from .models import FailedLoginAttempt

SUSPICIOUS_ATTEMPT_THRESHOLD = 5


def alert_for_suspicious_activity(username):
    # Create or update a record of the failed login attempt
    attempt, created = FailedLoginAttempt.objects.get_or_create(
        username=username,
        defaults={'attempts': 1},
    )

    # Check if the account is already locked out
    if attempt.is_locked_out():
        # Do not increment attempts if the account is locked out
        return

    if not created:
        attempt.attempts += 1
        attempt.save()

    # Check if the number of failed attempts is above the threshold
    if attempt.attempts > SUSPICIOUS_ATTEMPT_THRESHOLD:
        # Send an email alert to the admin
        send_mail(
            'Suspicious Login Activity Detected',
            f'Multiple failed login attempts for user: {username}',
            'from@example.com',
            ['admin@example.com'],
            fail_silently=False,
        )
        # Lockout the user
        attempt.lock_out()
    elif attempt.attempts == SUSPICIOUS_ATTEMPT_THRESHOLD:
        # Start the lockout period
        attempt.lock_out()
