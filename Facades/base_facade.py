import logging
from Rachel.DAL import DAL
from django.db import transaction
from django.db import DatabaseError
from django.contrib.auth import  logout
from axes.helpers import get_client_ip_address
from Forms.user_forms import CivilianUpdateForm
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import update_session_auth_hash
from Forms.support_provider_forms import SupportProviderUpdateForm
from Forms.common_forms import CustomChangePasswordForm , DeactivateForm
from Rachel.models import  UnauthorizedAccessAttempt,  UserActivity, User, Civilian, Administrator,SupportProvider, UserPreference, SupportProviderCategory,CommonUserProfile,Notification







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





    def view_profile(self, requesting_user_id, profile_user_id):
        """
        Retrieves the profile details of a user based on their role. Administrators can access any user's profile, 
        while other users can only access their own profile.

        Args:
            requesting_user_id (int): The ID of the user making the request. Used to verify permission to access the profile.
            profile_user_id (int): The ID of the user whose profile is to be retrieved.

        Returns:
            dict: User's profile details if found and authorized. Structure varies based on user's role.
            Returns an empty dictionary or an error message if unauthorized or not found.

        Raises:
            Exception: If an unexpected error occurs during retrieval.
        """
        try:
            requesting_user = self.dal.get_by_id(User, requesting_user_id)
            profile_user = self.dal.get_by_id(User, profile_user_id)

            # Check if the user is authorized to view the profile
            if requesting_user_id != profile_user_id and not requesting_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {requesting_user_id} is not authorized to view profile of User ID {profile_user_id}.")
                return {'error': 'Permission denied'}

            if not profile_user:
                logger.warning(f"No user found with ID {profile_user_id}.")
                return {}

            # Fetch the common user profile fields
            common_profile = self.dal.get_related(profile_user, 'commonuserprofile')
            profile_details = self._extract_common_profile_fields(common_profile)

            # Extend with role-specific details
            if Civilian.objects.filter(user=profile_user).exists():
                profile_details.update(self._extract_civilian_specific_fields(profile_user))
            elif SupportProvider.objects.filter(user=profile_user).exists():
                profile_details.update(self._extract_support_provider_specific_fields(profile_user))
            elif Administrator.objects.filter(user=profile_user).exists():
                profile_details.update(self._extract_administrator_specific_fields(profile_user))
            else:
                logger.warning(f"No specific profile found for user ID {profile_user_id}.")
                return {}

            logger.info(f"Profile details retrieved for user ID {profile_user_id}.")
            return profile_details

        except Exception as e:
            logger.error(f"Error retrieving profile for user ID {profile_user_id}: {e}", exc_info=True)
            raise



    def _extract_common_profile_fields(self, common_profile):
        # Extract fields common to all users
        fields = {
            'username': common_profile.user.username,
            'email': common_profile.user.email,
            'identification_number': common_profile.identification_number,
            'id_type': common_profile.get_id_type_display(),
            'country_of_issue': common_profile.country_of_issue.name if common_profile.country_of_issue else None,
            'languages_spoken': [language.name for language in common_profile.languages_spoken.all()],
            'active_until': common_profile.active_until,
            'address': common_profile.address,
            'city': common_profile.city.name if common_profile.city else None,
            'country': common_profile.country.name if common_profile.country else None,
            'phone_number': common_profile.phone_number.as_e164 if common_profile.phone_number else None,
            'terms_accepted': common_profile.terms_accepted,
            'profile_picture_url': common_profile.profile_picture.url if common_profile.profile_picture else None,
        }
        return fields
    


    def _extract_civilian_specific_fields(self, civilian):
        # Extract fields specific to Civilian users
        fields = {
            'gender': civilian.get_gender_display(),
            'intentions': [intention.get_name_display() for intention in civilian.intentions.all()]
        }
        return fields

    def _extract_support_provider_specific_fields(self, support_provider):
        # Extract fields specific to Support Provider users
        fields = {
            'looking_to_earn': support_provider.looking_to_earn,
            'kosher': support_provider.kosher,
            'rating': support_provider.rating,
            'accessible_facilities': support_provider.accessible_facilities,
            'service_hours': support_provider.service_hours,
            'additional_info': support_provider.additional_info,
            'categories': [category.name for category in support_provider.support_provider_categories.all()]
        }
        return fields

    def _extract_administrator_specific_fields(self, administrator):
        # Extract fields specific to Administrator users
        fields = {
            'department': administrator.department,
        }
        return fields


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
    



    def update_profile(self, user_id, profile_data, request):

        """
        Updates the profile of a user based on their role (Civilian or Support Provider).
        
        Args:
            user_id (int): The ID of the user whose profile is to be updated.
            profile_data (dict): The data to update the user's profile with.
            request: The HTTP request object, used for session updates and IP address retrieval.
        
        Returns:
            bool: True if the update is successful, False otherwise.
        
        Raises:
            ValidationError: If the form validation fails or if the user does not exist.
        """
        
        update_successful = False  # Initializing the variable
        
        try:
            with transaction.atomic():
                # Fetch user and determine the role
                user = self.dal.get_by_id(User, user_id)
                if Civilian.objects.filter(user=user).exists():
                    civilian_instance = self.dal.get_related(user, 'civilian')
                    form = CivilianUpdateForm(data=profile_data, instance=civilian_instance)
                elif SupportProvider.objects.filter(user=user).exists():
                    support_provider_instance = self.dal.get_related(user, 'supportprovider')
                    form = SupportProviderUpdateForm(data=profile_data, instance=support_provider_instance)
                else:
                    logger.error("User role not identified for user_id: " + str(user_id))
                    return False  # Return False immediately if user role is not identified
            
                # Validate and save the form
                if form.is_valid():
                    form.save(commit=True)
                    # Record the activity
                    user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                    self.dal.create(UserActivity, user=user, activity_type='profile_updated', ip_address=user_ip)
                    logger.info(f"Profile updated successfully for user_id: {user_id}")
                    update_successful = True  # Set the variable to True if update is successful
                else:
                    logger.warning(f"Profile update failed due to form validation errors for user_id: {user_id}")
        
        except ValidationError as e:
            logger.error(f"Validation error during profile update for user_id {user_id}: {e}")
        
        except Exception as e:
            logger.error(f"Unexpected error during profile update for user_id {user_id}: {e}")

        if update_successful:
            logger.debug(f"Profile update successful for user_id: {user_id}")
        else:
            logger.warning(f"Profile update unsuccessful for user_id: {user_id}")

        return update_successful  # Return the variable at the end
    



    def user_preferences(self, user_id, preferences_data=None, request=None):

        """
        Retrieves or updates the preferences for a given user.

        Args:
            user_id (int): The ID of the user whose preferences are to be managed.
            preferences_data (dict, optional): The data to update the user's preferences with.
                If None, the method retrieves the current preferences.
            request: The HTTP request object, used to get the user's IP address.

        Returns:
            dict or bool: The user's preferences if preferences_data is None, or True if the update is successful.

        Raises:
            ValidationError: If an error occurs during processing.
        """

        operation_successful = False  # Flag to track success of the operation

        try:
            user_preferences = self.dal.get_by_field(UserPreference, user_id=user_id)

            if preferences_data is None:
                if user_preferences:
                    return vars(user_preferences)  # Return all user preferences attributes
                return {}

            user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0') if request else '0.0.0.0'
            if user_preferences:
                self.dal.update(user_preferences, **preferences_data)
                operation_successful = True
            else:
                preferences_data['user_id'] = user_id
                self.dal.create(UserPreference, **preferences_data)
                operation_successful = True

            if operation_successful:
                self.dal.create(UserActivity, user_id=user_id, activity_type='preferences_updated', ip_address=user_ip)
                logger.info(f"User preferences updated for user_id: {user_id}, IP: {user_ip}")

        except ValidationError as e:
            logger.error(f"Validation error in user_preferences for user_id {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in user_preferences for user_id {user_id}: {e}")
            raise ValidationError("An unexpected error occurred.")

        return operation_successful
    




    def fetch_user_activity(self, user_id):
        """
        Fetches the activity log for a specific user.

        Args:
            user_id (int): The ID of the user whose activity log is to be fetched.

        Returns:
            list: A list of dictionaries containing details of each user activity.
        """
        logger.info(f"Initiating fetch for user activity log. User ID: {user_id}")

        try:
            # list the activities from the most recent and so on ... 
            activities = self.dal.filter(UserActivity, user_id=user_id).order_by('-timestamp')

            if not activities.exists():
                logger.warning(f"No activities found for user ID {user_id}")
                return []

            activity_log = [{
                'activity_type': activity.activity_type,
                'timestamp': activity.timestamp,
                'ip_address': activity.ip_address
            } for activity in activities]

            logger.info(f"Fetched {len(activity_log)} activities for user ID {user_id}")
            return activity_log

        except ValidationError as ve:
            logger.error(f"Validation error occurred while fetching activities for user ID {user_id}: {ve}")
            raise ve

        except Exception as e:
            logger.error(f"Unexpected error occurred while fetching activities for user ID {user_id}: {e}")
            raise ValidationError("An unexpected error occurred while retrieving user activities.")
        


    def list_support_provider_categories(self):

        """
        Retrieves a list of all support provider categories from the database.

        Returns:
            list of dict: A list where each dict represents a support provider category.
        """

        logger.info("Starting retrieval of support provider categories.")
        try:
            categories = self.dal.get_all(SupportProviderCategory)
            category_list = [{'id': category.id, 'name': category.name} for category in categories]
            logger.info(f"Successfully retrieved {len(category_list)} support provider categories.")
            return category_list

        except DatabaseError as db_err:
            logger.error(f"Database error in list_support_provider_categories: {db_err}")
            raise ValidationError("A database error occurred while retrieving categories.")
        except Exception as e:
            logger.error(f"Error in list_support_provider_categories: {e}")
            raise ValidationError("An error occurred while retrieving support provider categories.")
        

    def get_user_image(self, user_id):
        """
        Retrieves the profile image of the logged-in user.

        Args:
            user_id (int): The ID of the logged-in user.

        Returns:
            str: URL of the user's profile image.

        Raises:
            ValidationError: If the user's profile or image is not found.
        """
        logger.info(f"Attempting to retrieve profile image for user_id: {user_id}")

        try:
            profile = self.dal.get_by_field(CommonUserProfile, user_id=user_id)
            
            if not profile or not profile.profile_picture:
                logger.warning(f"No profile image found for user_id: {user_id}")
                raise ValidationError("No profile image found for the user.")

            image_url = profile.profile_picture.url
            logger.info(f"Profile image retrieved successfully for user_id: {user_id}: {image_url}")

            return image_url

        except ValidationError as e:
            logger.error(f"Validation error in get_image for user_id {user_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_image for user_id {user_id}: {e}")
            raise ValidationError("An unexpected error occurred while fetching the image.")
        


    def get_user_notifications(self, user_id):

        """
        Retrieve notifications for a given user.

        Args:
            user_id (int): The ID of the user whose notifications are to be retrieved.

        Returns:
            list: A list of dictionaries containing notification details.
        """

        try:
            user_notifications = self.dal.filter(Notification, recipient_id=user_id)
            notifications_list = [{
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'read': notification.read,
                'notification_type': notification.notification_type,
                'created_at': notification.created_at
            } for notification in user_notifications]

            logger.info(f"Retrieved {len(notifications_list)} notifications for user ID {user_id}.")
            return notifications_list

        except Exception as e:
            logger.error(f"Error retrieving notifications for user ID {user_id}: {e}", exc_info=True)
            raise

    

    def mark_notification_as_read(self, notification_id):

        """
        Marks a specific notification as read.

        Args:
            notification_id (int): The ID of the notification to be marked as read.

        Returns:
            bool: True if the operation is successful, False otherwise.
        """
        
        try:
            notification = self.dal.get_by_id(Notification, notification_id)
            if notification:
                notification.mark_as_read()
                logger.info(f"Marked notification ID {notification_id} as read.")
                return True
            else:
                logger.warning(f"No notification found with ID {notification_id}.")
                return False

        except Exception as e:
            logger.error(f"Error marking notification ID {notification_id} as read: {e}", exc_info=True)
            return False