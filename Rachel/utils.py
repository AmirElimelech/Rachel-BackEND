from django.core.mail import send_mail
from .models import FailedLoginAttempt
from .DAL import DAL
import logging



SUSPICIOUS_ATTEMPT_THRESHOLD = 5

dal = DAL()
logger = logging.getLogger(__name__)

def alert_for_suspicious_activity(username):
    try:
        attempt, created = dal.get_or_create(
            FailedLoginAttempt,
            defaults={'attempts': 1},
            username=username
        )

        # Check if the account is already locked out
        if dal.is_locked_out(attempt):
            logger.warning(f"Suspicious activity detected for user {username}, but the account is already locked out.")
            return

        if not created:
            attempt.attempts += 1
            dal.update(attempt)

        logger.info(f"Suspicious activity detected for user {username}. Attempts: {attempt.attempts}")


        if attempt.attempts > SUSPICIOUS_ATTEMPT_THRESHOLD:
            send_mail(
                'Suspicious Login Activity Detected',
                f'Multiple failed login attempts for user: {username}',
                'from@example.com',
                ['admin@example.com'],
                fail_silently=False,
            )
            dal.lock_out(attempt)
            logger.warning(f"User {username} locked out due to suspicious activity.")

        elif attempt.attempts == SUSPICIOUS_ATTEMPT_THRESHOLD:
            dal.lock_out(attempt)
            logger.warning(f"User {username} locked out due to reaching the suspicious attempt threshold.")

    except Exception as e:
        logger.exception(f"Error in alert_for_suspicious_activity: {str(e)}")
