import logging
from .DAL import DAL
from axes.models import AccessAttempt
from django.core.mail import send_mail
from axes.helpers import get_client_ip_address








SUSPICIOUS_ATTEMPT_THRESHOLD = 5

dal = DAL()
logger = logging.getLogger(__name__)



def alert_for_suspicious_activity(username, request=None):

    """
    The alert_for_suspicious_activity function is designed to log and alert on suspicious login activity based on failed login attempts. It operates as follows:

    1. It first retrieves the client's IP address from the incoming request.

    2. It then queries the AccessAttempt model to fetch all failed login attempt records associated with this IP address.

    3. The function iterates over these records, logging the number of failed attempts for each user. For the user associated with the current failed attempt (identified by 'username'), the failure count is incremented by one to reflect the most recent failure. This increment is necessary because the logging occurs before the current attempt is committed to the database, and thus the fetched count is one less than the actual count after the failure.

    4. In addition to logging individual user failures, the function also calculates the total number of failed login attempts from the specified IP address. This total includes the incremented counts, providing an up-to-date view of the overall failed attempts from that IP.

    5. If the total number of failures exceeds a predefined threshold (SUSPICIOUS_ATTEMPT_THRESHOLD), an alert is triggered, notifying about the suspicious login activity. This alert includes sending an email and logging a warning message.

    This approach ensures that the counts of failed login attempts are accurate and current, reflecting the latest state immediately after a login failure, thereby offering a real-time insight into suspicious activities for security monitoring purposes.
    """



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