import logging
from Rachel.DAL import DAL
from django.db import DatabaseError
from django.contrib.auth import  logout
from axes.helpers import get_client_ip_address
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from Forms.common_forms import CustomChangePasswordForm , DeactivateForm
from Rachel.models import  UnauthorizedAccessAttempt,  UserActivity , User



logger = logging.getLogger(__name__)



class BaseFacade:


    def __init__(self):
        self.dal = DAL()


    def logout_user(self, request):
        """
        Logs out the current user.

        Args:
            request (HttpRequest): The HTTP request object containing user session data.
        """
        try:
            user = request.user
            logout(request)

            # Log this action for audit purposes
            self.dal.create(UserActivity, user=user, activity_type='logout', ip_address=get_client_ip_address(request))

            logger.info(f"User {user.username} logged out successfully.")
        except Exception as e:
            logger.exception(f"Unexpected error during logout for user {user.username if user.is_authenticated else 'Unknown'}: {e}")
            raise ValidationError("An error occurred during logout.")




    def view_failed_login_attempts(self, user):
        """
        Retrieves all failed login attempts related to the specified user.

        Args:
            user (User): The user whose failed login attempts are to be retrieved.

        Returns:
            list: A list of dictionaries containing details of each failed login attempt.
        """
        try:
            failed_attempts = self.dal.filter(UnauthorizedAccessAttempt, user=user)

            attempts_data = []
            for attempt in failed_attempts:
                attempt_data = {
                    'timestamp': attempt.timestamp,
                    'ip_address': attempt.ip_address,
                    'browser': attempt.browser,
                    'operating_system': attempt.operating_system,
                    'country': attempt.country.name if attempt.country else None
                }
                attempts_data.append(attempt_data)

            logger.info(f"Retrieved {len(attempts_data)} failed login attempts for user: {user.username}")
            return attempts_data

        except Exception as e:
            logger.exception(f"Unexpected error in view_failed_login_attempts for user {user.username}: {e}")
            raise ValidationError("An error occurred while retrieving failed login attempts.")






    def deactivate_profile(self, user_id, request):

        """
        Deactivates a user's profile after confirming their intention through a form.

        Args:
            user_id (int): The ID of the user whose profile is to be deactivated.
            request: The HTTP request object, used to get the user's IP address.

        Raises:
            ValidationError: If an error occurs during the deactivation process or if the user's confirmation is not validated.
        """

        try:
            # Fetch the user by ID
            user = self.dal.get_by_id(User, user_id)
            # Validate the user's intention using DeactivateForm
            form = DeactivateForm(request.POST, user=user)

            if form.is_valid() and form.cleaned_data.get('confirm'):
                # Deactivate the user's account
                user.is_active = False
                user.save()

                # Log the deactivation for audit purposes
                user_ip = get_client_ip_address(request)
                self.dal.create(UserActivity, user=user, activity_type='account_deactivated', ip_address=user_ip)
                logger.info(f"User {user.username}'s account has been deactivated.")
            else:
                # Log specific form errors for debugging
                form_errors = form.errors.as_json()
                logger.warning(f"Form validation failed during deactivation of user {user.username}: {form_errors}")
                raise ValidationError("Account deactivation confirmation failed.")

        except DatabaseError as e:
            logger.error(f"Database error during deactivation of user with ID {user_id}: {e}")
            raise ValidationError("An error occurred while accessing the database.")
        except ValidationError as e:
            # Handle specific validation errors
            logger.error(f"Validation error during deactivation of user {user_id}: {e}")
            raise
        except Exception as e:
            # Catch-all for any other unexpected errors
            logger.error(f"Unexpected error during deactivation of user with ID {user_id}: {e}")
            raise ValidationError("An unexpected error occurred.")

        return True


 


    def change_password(self, user, old_password, new_password, confirm_new_password, request):

        """
        Handles the process of changing a user's password using a custom form.

        This method leverages the CustomChangePasswordForm to validate the user's old password,
        the new password, and the confirmation of the new password. It ensures the new password adheres
        to defined security and similarity standards. Post-validation, it updates the user's password and
        maintains the session integrity. Additionally, it logs the password change activity and manages the 
        notification process.

        Args:
            user (User): The user instance whose password is to be changed.
            old_password (str): The current password of the user.
            new_password (str): The new password for the user.
            confirm_new_password (str): Confirmation of the new password.
            request: The HTTP request object, used for session updates.

        Raises:
            ValidationError: If the form validation fails, detailing the specific validation errors.

        Returns:
            bool: True if the password change process is successful, otherwise raises an exception.
        """


        form_data = {
            'old_password': old_password,
            'new_password1': new_password,
            'new_password2': confirm_new_password,
        }
        password_form = CustomChangePasswordForm(user=user, data=form_data)

        if password_form.is_valid():
            password_form.save(commit=True)  # This also handles the password change and email notification

            # Updating the session after password change
            update_session_auth_hash(request, user)

            # Record user activity for password change
            user_ip = get_client_ip_address(request)
            self.dal.create(UserActivity, user=user, activity_type='password_change', ip_address=user_ip)
            logger.info(f"Password change recorded for user: {user.username} from IP: {user_ip}")

        else:
            # Log and raise form validation errors
            errors = password_form.errors.as_json()
            logger.warning(f"Password change failed: {errors}")
            raise ValidationError(password_form.errors)

        return True