from django.core.mail import send_mail
from .DAL import DAL
from django.utils import timezone
from datetime import timedelta
from axes.models import AccessAttempt
from django.db.models import Sum

from axes.attempts import get_user_attempts
from axes.helpers import get_client_ip_address




import logging



SUSPICIOUS_ATTEMPT_THRESHOLD = 5

dal = DAL()
logger = logging.getLogger(__name__)



def alert_for_suspicious_activity(username, request=None):
    try:
        # Get the client IP address from the request
        ip_address = get_client_ip_address(request)

        # Fetch all AccessAttempt instances for this IP address
        attempts_from_ip = AccessAttempt.objects.filter(ip_address=ip_address)

        total_failures = 0
        user_failure_updated = False

        # Log the number of attempts for each user from this IP and increment the count
        for attempt in attempts_from_ip:
            user_failures = attempt.failures_since_start
            if attempt.username == username:
                user_failures += 1  # Incrementing for the current user
                user_failure_updated = True
            logger.info(f"User {attempt.username} from IP {ip_address} has {user_failures} failed attempts")
            total_failures += user_failures

        # If the current user's failure wasn't in the list, add it manually
        if not user_failure_updated:
            logger.info(f"User {username} from IP {ip_address} has 1 failed attempt")
            total_failures += 1

        logger.info(f"Total login failures from IP {ip_address}: {total_failures}")

        # Alert if the number of attempts exceeds the threshold
        if total_failures > SUSPICIOUS_ATTEMPT_THRESHOLD:
            send_mail(
                'Suspicious Login Activity Detected',
                f'Multiple failed login attempts from IP: {ip_address}',
                'rachel.for.israel@gmail.com',
                ['sapinhopreto@gmail.com'],
                fail_silently=False,
            )
            logger.warning(f"Suspicious activity detected from IP {ip_address} with {total_failures} total failures.")

    except Exception as e:
        logger.exception(f"Error in alert_for_suspicious_activity: {str(e)}")