import logging
from .DAL import DAL
from Rachel.models import Country
from axes.models import AccessAttempt
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from axes.helpers import get_client_ip_address
from django.core.exceptions import ValidationError









SUSPICIOUS_ATTEMPT_THRESHOLD = 5

dal = DAL()

logger = logging.getLogger(__name__)



def alert_for_suspicious_activity(username, request=None):
    """
    The alert_for_suspicious_activity function is designed to log and alert on suspicious login activity based on failed login attempts. It operates as follows:

    1. It first retrieves the client's IP address from the incoming request.

    2. It then queries the AccessAttempt model to fetch all failed login attempt records associated with this IP address.

    3. The function iterates over these records, logging the number of failed attempts for each user. For the user associated with the 
    current failed attempt (identified by 'username'), the failure count is incremented by one to reflect the most recent failure. 
    This increment is necessary because the logging occurs before the current attempt is committed to the database, and thus the fetched 
    count is one less than the actual count after the failure.

    4. In addition to logging individual user failures, the function also calculates the total number of failed login attempts from 
    the specified IP address. This total includes the incremented counts, providing an up-to-date view of the overall failed attempts from that IP.

    5. If the total number of failures exceeds a predefined threshold (SUSPICIOUS_ATTEMPT_THRESHOLD), an alert is triggered, notifying 
    about the suspicious login activity to the system Administrator Emails ( searches for All system Administrators ). This alert includes sending an email 
    and logging a warning message.

    This approach ensures that the counts of failed login attempts are accurate and current, reflecting the latest state immediately 
    after a login failure, thereby offering a real-time insight into suspicious activities for security monitoring purposes.
    """

    # Initialize the DAL instance

    try:
        # Get the client IP address from the request
        ip_address = get_client_ip_address(request)

        # Fetch all AccessAttempt instances for this IP address using DAL
        attempts_from_ip = dal.filter(AccessAttempt, ip_address=ip_address)

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
            # Get all administrators' emails
            admin_group = dal.get_by_field(Group, name='Administrator')
            if admin_group:
                admin_emails = [user.email for user in admin_group.user_set.all() if user.email]
            

                # Log the recipients before sending the email
                logger.info(f"Sending email to administrators: {admin_emails}")

                # Send email to all administrators
                send_mail(
                    'Suspicious Login Activity Detected',
                    f'Multiple failed login attempts from IP: {ip_address}',
                    'Rachel.for.Israel@gmail.com',
                    admin_emails,
                    fail_silently=False,
                )
                
                logger.warning(f"Suspicious activity detected from IP {ip_address} with {total_failures} total failures.")

    except Exception as e:
        logger.exception(f"Error in alert_for_suspicious_activity: {str(e)}")




def clean_phone_number(country_id, phone_number):
    """
    Validates and formats a phone number based on the country's phone code and ensures it has a specific length.

    This function takes a country ID and a phone number as inputs. It uses the DAL to fetch the corresponding
    country instance and retrieve its phone code. The phone number is then formatted with the country's phone code.
    It also checks if the phone number has the required length (10 digits) after formatting.

    Args:
    country_id (int): The ID of the country to which the phone number belongs.
    phone_number (str): The phone number to be cleaned and formatted.

    Returns:
    str: The formatted phone number in international format.

    Raises:
    ValidationError: If any of the validations fail.
    """
    
    
    country_instance = dal.get_by_id(Country, country_id)

    errors = {}
    if not phone_number.isdigit():
        errors['phone_number'] = "Phone number must contain only digits."

    if phone_number.startswith('+') or (country_instance and phone_number.startswith(country_instance.phone_code)):
        errors['phone_number'] = "Phone number should not include the country code."

    if not 10 <= len(phone_number) <= 15:
        errors['phone_number'] = "Phone number length must be between 7 and 15 digits."

    if errors:
        raise ValidationError(errors)



    phone_number = phone_number.lstrip('0')

    # now this part i ensured that the original phone_number provided as input is used as-is, without any formatting if the country was not found in the database 
    # if it was found it will create the full phonen number for example Israeli phone number = +972546227171 

    full_phone_number = f"+{country_instance.phone_code}{phone_number}" if country_instance else phone_number

    return full_phone_number