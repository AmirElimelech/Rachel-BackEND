
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import User, Shelters, SupportProvider, UserActivity
from django.contrib.auth.signals import user_logged_in, user_login_failed
from .DAL import DAL
from .utils import alert_for_suspicious_activity
import logging




logger = logging.getLogger(__name__)


dal = DAL()

@receiver(post_save, sender=User, dispatch_uid="create_shelter_signal")
def create_shelter_signal(sender, instance, created, **kwargs):
    try:
        if created:
            # Check if the user is associated with a profile and is a support provider
            support_provider_profile = dal.get_related(instance, 'profile__supportprovider')
            if support_provider_profile and support_provider_profile.category.name == "Shelter":
                # Check if a Shelter with this provider does not exist
                if not dal.filter(Shelters, support_provider=support_provider_profile):
                    # Create a new Shelter instance
                    new_shelter = dal.create(Shelters, name=f"Shelter by {instance.username}", support_provider=support_provider_profile)
                    # Notify administrators of the new shelter
                    send_mail(
                        'New Shelter Registration',
                        f'A new shelter {new_shelter.name} has been created and needs review.',
                        'from@example.com',
                        ['admin@example.com'],
                        fail_silently=False,
                    )
    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in create_shelter_signal: {e}")




@receiver(post_save, sender=SupportProvider)
def account_activation_notification(sender, instance, **kwargs):
    try:
        if instance.is_active:  # Assuming `is_active` is a field on SupportProvider.
            send_mail(
                'Account Activated',
                f'Your shelter account {instance.profile.user.username} has been activated.',
                'from@example.com',
                [instance.profile.user.email],
                fail_silently=False,
            )
    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in account_activation_notification: {e}")




@receiver(user_logged_in)
def track_user_login(sender, request, user, **kwargs):
    try:
        dal.create(UserActivity, user=user, activity_type='login', ip_address=request.META.get('REMOTE_ADDR', ''))
    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in track_user_login: {e}")




@receiver(post_save, sender=User, dispatch_uid="send_welcome_email")
def send_welcome_email(sender, instance, created, **kwargs):
    try:
        if created:
            send_mail(
                'Welcome to Our Service',
                'Here’s how to get started...',
                'welcome@example.com',
                [instance.email],
                fail_silently=False,
            )
    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in send_welcome_email: {e}")




@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, **kwargs):
    try:
        # Log the failed login attempt, check if there are many in a short time, and alert if necessary
        alert_for_suspicious_activity(credentials.get('username', 'unknown'))
    except Exception as e:
        # Log the exception and handle accordingly
        logger.error(f"Error in on_user_login_failed: {e}")
