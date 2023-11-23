
import logging
from .DAL import DAL
from django.dispatch import receiver
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.contrib.auth import  get_user_model
from .utils import alert_for_suspicious_activity
from django.core.exceptions import ObjectDoesNotExist
from .models import User, Shelters, SupportProvider, UserActivity
from django.contrib.auth.signals import user_logged_in, user_login_failed , user_logged_out



logger = logging.getLogger(__name__)


dal = DAL()



@receiver(post_save, sender=User, dispatch_uid="create_shelter_signal")
def create_shelter_signal(sender, instance, created, **kwargs):
    """
    Create a shelter signal for new SupportProvider users who are categorized as "Shelter".

    This method includes logging to track its execution, logging both the process of checking 
    for the necessary conditions to create a shelter and the outcome of these checks. It helps 
    in identifying and resolving issues related to shelter creation based on user profiles.

    :param sender: The model class (User) sending the signal.
    :param instance: The instance of the model just saved.
    :param created: Boolean indicating if a new record was created.
    :param kwargs: Additional keyword arguments.
    """
    try:
        if created:
            logger.info(f"Checking for shelter creation conditions for user: {instance.username}")

            # Check if the user has a profile
            try:
                user_profile = instance.profile
            except ObjectDoesNotExist:
                logger.error(f"User {instance.username} does not have a profile associated")
                return

            # Check if the profile is associated with a SupportProvider
            try:
                support_provider_profile = user_profile.supportprovider
            except ObjectDoesNotExist:
                logger.error(f"Profile {user_profile} does not have a SupportProvider associated")
                return

            # Additional logging for category check
            logger.info(f"Checking category for SupportProvider profile: {support_provider_profile}")

            if support_provider_profile.category.name == "Shelter":
                # Check if a Shelter with this provider does not exist
                if not dal.filter(Shelters, support_provider=support_provider_profile):
                    logger.info(f"Creating new shelter for SupportProvider: {support_provider_profile}")

                    # Create a new Shelter instance
                    new_shelter = dal.create(Shelters, name=f"Shelter by {instance.username}", support_provider=support_provider_profile)

                    # Notify administrators of the new shelter
                    send_mail(
                        'New Shelter Registration',
                        f'A new shelter {new_shelter.name} has been created and needs review.',
                        'Rachel.for.Israel@gmail.com',
                        ['sapinhopreto@gmail.com'],
                        fail_silently=False,
                    )

                    logger.info(f"New shelter created and notification sent for {new_shelter.name}")

    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in create_shelter_signal for user {instance.username}: {e}")





@receiver(post_save, sender=SupportProvider)
def account_activation_notification(sender, instance, **kwargs):
    """
    Send an account activation notification to support providers upon the activation of their account.

    This method is enhanced with logging to track its execution. 
    It logs when an attempt is made to send an account activation notification 
    and reports success or failure, providing visibility into the process 
    and aiding in troubleshooting if any issues arise.

    :param sender: The model class (SupportProvider) sending the signal.
    :param instance: The instance of the model just saved.
    :param kwargs: Additional keyword arguments.
    """
    try:
        if instance.is_active:  # Assuming `is_active` is a field on SupportProvider.
            # Log the initiation of the email sending process
            logger.info(f"Attempting to send account activation email to: {instance.profile.user.email}")

            send_mail(
                'Account Activated',
                f'Your shelter account {instance.profile.user.username} has been activated.',
                'Please login again , Thank you for generous support',
                'Rachel.for.Israel@gmail.com',
                [instance.profile.user.email],
                fail_silently=False,
            )

            # Log the successful email sending
            logger.info(f"Account activation email successfully sent to: {instance.profile.user.email}")

    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in account_activation_notification for {instance.profile.user.email}: {e}")





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
        # Use DAL to create a record of the user's login activity
        dal.create(UserActivity, user=user, activity_type='login', ip_address=request.META.get('REMOTE_ADDR', ''))

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
        dal.create(UserActivity, user=user, activity_type='logout', ip_address=request.META.get('REMOTE_ADDR', ''))

        # Optionally, log the tracking of the logout
        logger.info(f"Logged out user: {user.username} from IP: {request.META.get('REMOTE_ADDR', '')}")
    except Exception as e:
        # Log the exception and handle accordingly
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

            send_mail(
                'Welcome to Our Service',
                'Here’s how to get started...',
                'now i should remember to right something about the project etc...',
                'Rachel.for.Israel@gmail.com',
                [instance.email],
                fail_silently=False,
            )

            # Log the successful email sending
            logger.info(f"Welcome email successfully sent to: {instance.email}")

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

        # Log the failed login attempt, check for suspicious activity, and alert if necessary
        alert_for_suspicious_activity(username, request)
    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in on_user_login_failed: {e}")