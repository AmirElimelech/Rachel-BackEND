

import logging
from .DAL import DAL
from django.dispatch import receiver
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.db.models.signals import post_save
from axes.helpers import get_client_ip_address
from django.contrib.auth import  get_user_model
from .utils import alert_for_suspicious_activity
from .models import User, Shelter, UserActivity , Group , SupportProvider ,Civilian
from django.contrib.auth.signals import user_logged_in, user_login_failed , user_logged_out



logger = logging.getLogger(__name__)


dal = DAL()


@receiver(post_save, sender=User)
def create_shelter_signal(sender, instance, created, **kwargs):
    """
    Create a shelter for new support provider users categorized as 'Shelter and Housing'.
    This function is triggered after a User instance is saved and checks if the user
    is a SupportProvider in the 'Shelter and Housing' category.
    If so, and if a Shelter does not already exist for this SupportProvider, a new Shelter instance is created.
    """
    try:
        if created and instance.groups.filter(name='SupportProvider').exists():
            logger.info(f"Checking for shelter creation conditions for user: {instance.username}")

            # Use DAL to get the related SupportProvider instance
            support_provider = dal.get_related(instance, 'supportprovider')

            if not support_provider:
                logger.error(f"User {instance.username} does not have a SupportProvider associated")
                return

            logger.info(f"SupportProvider found for user: {instance.username}. Checking for 'Shelter and Housing' category.")

            # Check if the support provider is in the 'Shelter and Housing' category
            if 'Shelter and Housing' in support_provider.support_provider_categories.values_list('name', flat=True):
                logger.info(f"SupportProvider {support_provider} has 'Shelter and Housing' category.")

                # Check if a Shelter with this provider does not exist
                if not dal.filter(Shelter, support_provider=support_provider).exists():
                    logger.info(f"No existing shelter found for {support_provider}. Creating new shelter.")

                    # Use DAL to create a new Shelter instance
                    new_shelter = dal.create(
                        Shelter,
                        name=f"Shelter by {instance.username}",
                        support_provider=support_provider
                    )

                    if new_shelter:
                        logger.info(f"New shelter created: {new_shelter.name}. Sending notification to administrators.")
                        admin_group = dal.get_by_field(Group, name='Administrator')
                        if admin_group:
                            admin_emails = [user.email for user in admin_group.user_set.all() if user.email]

                            # Send email to all administrators
                            send_mail(
                                'New Shelter Registration',
                                f'A new shelter {new_shelter.name} has been created and needs review.',
                                'Rachel.for.Israel@gmail.com',
                                admin_emails,
                                fail_silently=False,
                            )

                        logger.info(f"Notification sent for new shelter: {new_shelter.name}")
                    else:
                        logger.error(f"Failed to create a new shelter for {support_provider}")
                else:
                    logger.info(f"Shelter already exists for {support_provider}")
            else:
                logger.info(f"SupportProvider {support_provider} does not have 'Shelter and Housing' category.")
        else:
            logger.info(f"No action needed for user {instance.username} as it's not a new SupportProvider.")

    except Exception as e:
        logger.error(f"Error in create_shelter_signal for user {instance.username}: {e}")



@receiver(post_save, sender=User)
def account_activation_notification(sender, instance, created, **kwargs):
    """
    Send an account activation notification to users upon the activation of their account.

    This method is enhanced with logging to track its execution. 
    It logs when an attempt is made to send an account activation notification 
    and reports success or failure, providing visibility into the process 
    and aiding in troubleshooting if any issues arise.

    :param sender: The model class (User) sending the signal.
    :param instance: The instance of the model just saved.
    :param created: Boolean indicating if a new record was created.
    :param kwargs: Additional keyword arguments.
    """
    try:
        # Check if the account is newly created or if the is_active status is changed to True
        # if (created and instance.is_active) or (not created and instance.is_active):
        update_fields = kwargs.get('update_fields')
        if created or (update_fields is not None and 'is_active' in update_fields):

            # Log the initiation of the email sending process
            logger.info(f"Attempting to send account activation email to: {instance.email}")

            subject = 'Account Activated' if instance.is_active else 'Account Deactivated'
            body = f'Your account {instance.username} has been activated. Please login again, thank you.' if instance.is_active else f'Your account {instance.username} has been deactivated.'

            message = EmailMessage(
                subject=subject,
                body=body,
                from_email='Rachel.for.Israel@gmail.com',
                to=[instance.email],  # Ensure this is a list
            )
            message.send()


            request = kwargs.get('request')
            user_ip = request.META.get('REMOTE_ADDR') if request else '0.0.0.0'

            # Record the activity
            activity_type = 'account_activated' if instance.is_active else 'account_deactivated_by_user'
            dal.create(UserActivity, user=instance, activity_type=activity_type, ip_address=user_ip)


            # Log the successful email sending
            logger.info(f"Account activation email successfully sent to: {instance.email}")

    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in account_activation_notification for {instance.email}: {e}")




@receiver(post_save, sender=Civilian)
@receiver(post_save, sender=SupportProvider)
def profile_update_notification(sender, instance, created, **kwargs):
    """
    Send a notification when a Civilian or SupportProvider profile is updated.
    """
    if not created:  # Ensure this is not a new record but an update
        try:
            # Logic to send an email notification about the profile update
            send_mail(
                subject='Profile Updated',
                message='Your profile has been successfully updated.',
                from_email='Rachel.for.Isreal@gmail.com',
                recipient_list=[instance.user.email],
                fail_silently=False,
            )


            # Obtain IP address
            request = kwargs.get('request')
            user_ip = request.META.get('REMOTE_ADDR') if request else '0.0.0.0'

            # Record the activity
            dal.create(UserActivity, user=instance.user, activity_type='profile_updated', ip_address=user_ip)

            logger.info(f"Profile update notification email sent to: {instance.user.email}")

        except Exception as e:
            logger.error(f"Error in profile_update_notification for {instance.user.email}: {e}")





@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):

    """
    Signal receiver for user logout events.

    This function is called when a user logs in. It records the user's
    login activity, including the user's details and the IP address from
    which the login request was made.

    :param sender: The class of the sender (unused in this function).
    :param request: The HTTP request from which the login originated.
    :param user: The user who is logging in.
    :param kwargs: Additional keyword arguments (unused in this function).
    """

    try:

        user_ip = get_client_ip_address(request)
        dal.create(UserActivity, user=user, activity_type='login', ip_address=user_ip)
        
        # Optionally, log the tracking of the login
        logger.info(f"Logged in user: {user.username} from IP: {request.META.get('REMOTE_ADDR', '')}")
    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in track_user_login: {e}")



@receiver(user_logged_out)
def track_user_logout(sender, request, user, **kwargs):
    """
    Signal receiver for user logout events.

    This function is called when a user logs out. It records the user's
    logout activity, including the user's details and the IP address from
    which the logout request was made.

    :param sender: The class of the sender (unused in this function).
    :param request: The HTTP request from which the logout originated.
    :param user: The user who is logging out.
    :param kwargs: Additional keyword arguments (unused in this function).
    """
    try:
        # Use DAL to create a record of the user's logout activity
        logger.info("Creating UserActivity of track user logout")
        user_ip = get_client_ip_address(request)
        dal.create(UserActivity, user=user, activity_type='logout', ip_address=user_ip)

        # Optionally, log the tracking of the logout
        logger.info(f"Logged out user: {user.username} from IP: {request.META.get('REMOTE_ADDR', '')}")
    except Exception as e:
        # Log the exception and handle accordingly)
        logger.error(f"Error in track_user_logout: {e}")









@receiver(post_save, sender=User, dispatch_uid="send_welcome_email")
def send_welcome_email(sender, instance, created, **kwargs):
    """
    Send a welcome email to new users upon their creation.
    This method is enhanced with logging to track its execution. 
    It logs when an attempt is made to send a welcome email and reports 
    success or failure, providing visibility into the email sending process 
    and aiding in troubleshooting if any issues arise.

    :param sender: The model class (User) sending the signal.
    :param instance: The instance of the model just saved.
    :param created: Boolean indicating if a new record was created.
    :param kwargs: Additional keyword arguments.
    """
    try:
        if created:
            # Log the initiation of the email sending process
            logger.info(f"Attempting to send welcome email to new user: {instance.email}")

            message = EmailMessage(
                'Welcome to Our Service',
                'Here’s how to get started...',
                'Rachel.for.Israel@gmail.com',
                [instance.email],
            )
            message.send()

            # Log the successful email sending
            logger.info(f"Welcome email successfully sent to: {instance.email}")

            # Obtain the IP address directly from the request object
            request = kwargs.get('request')
            user_ip = request.META.get('REMOTE_ADDR') if request else '0.0.0.0'
            
            # Record the email sending in UserActivity
            dal.create(UserActivity, user=instance, activity_type='welcome_email_sent', ip_address=user_ip)
            logger.info(f"UserActivity recorded for sending welcome email to: {instance.username}")

    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in send_welcome_email for {instance.email}: {e}")






@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request=None, **kwargs):
    """
    This function acts as a signal receiver for failed login attempts. It processes the credentials
    provided during the login attempt to identify the user and logs relevant information about the failure.

    The function performs the following steps:
    1. Initializes the username as 'unknown' by default.
    2. Checks if the credentials provided are in the expected format (dictionary or string) and extracts the username.
    3. Logs the initiation of the login failure handling process.
    4. Logs the username associated with the failed login attempt.
    5. Calls the alert_for_suspicious_activity function to handle the failed login attempt, which includes additional logging and alerting mechanisms.
    6. Captures and logs any exceptions that occur during the process for debugging purposes.

    This approach helps in monitoring login activities, identifying potential security issues, and aiding in the debugging process in case of errors.
    """

    try:
        # Initialize username as 'unknown' by default
        username = 'unknown'

        # Log the initiation of the login failure handling
        logger.info("Handling user login failure.")

        # Check if credentials is a dictionary and has a 'username' key
        if isinstance(credentials, dict) and 'username' in credentials:
            username = credentials.get('username')
        elif isinstance(credentials, str):
            # If credentials is a string, it might be the username directly
            # Check if this username exists in your User model
            if get_user_model().objects.filter(username=credentials).exists():
                username = credentials

        # Log the username associated with the failed login attempt
        logger.info(f"Login failed for user: {username}")

        # Attempt to retrieve the User instance
        user_instance = None
        if username != 'unknown':
            user_instance = get_user_model().objects.filter(username=username).first()

        # Only proceed if a user instance is found
        if user_instance and request:
            dal.create(UserActivity, user=user_instance, activity_type='login_failed', ip_address=request.META.get('REMOTE_ADDR', ''))
            logger.info(f"Recorded failed login attempt for user: {user_instance.username} from IP: {request.META.get('REMOTE_ADDR', '')}")
        else:
            logger.info(f"User instance not found or request is None for username: {username}")

        # Log the failed login attempt, check for suspicious activity, and alert if necessary
        alert_for_suspicious_activity(username, request)

    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in on_user_login_failed: {e}")



