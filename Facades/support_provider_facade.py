
import logging
from Rachel.DAL import DAL
from .base_facade import BaseFacade
from Rachel.models import User, SupportProvider, FeedbackResponse, UserFeedback,UserActivity,Shelter




logger = logging.getLogger(__name__)


class SupportProviderFacade(BaseFacade):


    def __init__(self):
        super().__init__()
        self.dal = DAL()  # Initialize the DAL instance





    def view_profile(self, requesting_user_id, profile_user_id):

        """
        Retrieves the profile details of a support provider user. Ensures that users can only access their own profile.

        Args:
            requesting_user_id (int): The ID of the user making the request.
            profile_user_id (int): The ID of the user whose profile to retrieve.

        Returns:
            dict: Support provider user profile details if found and authorized; an empty dict otherwise.
        """

        try:
            # Check if the requesting user is trying to view their own profile
            if requesting_user_id != profile_user_id:
                logger.warning(f"User ID {requesting_user_id} is not authorized to view profile of User ID {profile_user_id}.")
                return {'error': 'Permission denied'}

            user = self.dal.get_by_id(User, profile_user_id)
            if not user:
                logger.warning(f"No user found with ID {profile_user_id}.")
                return {}

            support_provider = self.dal.get_related(user, 'supportprovider')
            if not support_provider:
                logger.warning(f"No support provider profile found for user ID {profile_user_id}.")
                return {}

            profile_details = {
                'username': support_provider.user.username,
                'email': support_provider.user.email,
                'identification_number': support_provider.identification_number,
                'id_type': support_provider.get_id_type_display(),
                'country_of_issue': support_provider.country_of_issue.name if support_provider.country_of_issue else None,
                'languages_spoken': [language.name for language in support_provider.languages_spoken.all()],
                'active_until': support_provider.active_until,
                'address': support_provider.address,
                'city': support_provider.city.name if support_provider.city else None,
                'country': support_provider.country.name if support_provider.country else None,
                'phone_number': support_provider.phone_number,
                'terms_accepted': support_provider.terms_accepted,
                'looking_to_earn': support_provider.looking_to_earn,
                'kosher': support_provider.kosher,
                'rating': support_provider.rating,
                'accessible_facilities': support_provider.accessible_facilities,
                'service_hours': support_provider.service_hours,
                'profile_picture_url': support_provider.profile_picture.url if support_provider.profile_picture else None,
                'additional_info': support_provider.additional_info
            }

            logger.info(f"Support provider profile details retrieved for user ID {profile_user_id}.")
            return profile_details

        except Exception as e:
            logger.error(f"Error retrieving support provider profile for user ID {profile_user_id}: {e}", exc_info=True)
            raise
    


    def respond_to_feedback(self, support_provider_id, feedback_id, response_text, request):
        """
        Allows a support provider to respond to feedback specifically related to them.

        Args:
            support_provider_id (int): The ID of the support provider responding.
            feedback_id (int): The ID of the feedback to respond to.
            response_text (str): The response text.
            request: The HTTP request object for getting the IP address.

        Returns:
            dict: A response indicating success or error message.
        """
        try:
            # Retrieve the feedback and the support provider using DAL
            feedback = self.dal.get_by_id(UserFeedback, feedback_id)
            if feedback:
                feedback.status = 'responded'
                feedback.save()
            support_provider = self.dal.get_by_id(SupportProvider, support_provider_id)

            # Check if feedback is related to this support provider
            if feedback and feedback.target_support_provider_id != support_provider_id:
                logger.warning(f"Support Provider {support_provider_id} not authorized to respond to feedback {feedback_id}.")
                return {'error': 'Not authorized to respond to this feedback'}

            # Create a feedback response using DAL
            response_data = {
                'feedback': feedback,
                'responder': support_provider.user,
                'response_text': response_text
            }
            feedback_response = self.dal.create(FeedbackResponse, **response_data)

            if feedback_response:
                # Log the user activity for feedback response submission
                user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                self.dal.create(UserActivity, user=support_provider.user, activity_type='feedback_responded', ip_address=user_ip)
                logger.info(f"Feedback {feedback_id} responded by Support Provider {support_provider_id}.")
                return {'success': True}

            return {'error': 'Failed to create feedback response'}

        except Exception as e:
            logger.error(f"Error in responding to feedback by Support Provider {support_provider_id}: {e}", exc_info=True)
            return {'error': str(e)}
        

    
    def get_my_notifications(self, user_id):

        """
        Retrieve notifications for the support provider user.

        Args:
            user_id (int): The ID of the support provider user.

        Returns:
            list: Notifications list for the support provider user.
        """
        
        return self.get_user_notifications(user_id)
    



    def update_shelter(self, support_provider_id, shelter_id, shelter_data, request):
        """
        Updates the details of a shelter associated with a support provider.

        Args:
            support_provider_id (int): The ID of the support provider making the update.
            shelter_id (int): The ID of the shelter to be updated.
            shelter_data (dict): A dictionary containing the updated shelter details.
            request: The HTTP request object for getting the IP address.

        Returns:
            bool: True if the shelter update is successful, False otherwise.

        Raises:
            Exception: If an unexpected error occurs during the update.
        """
        try:
            support_provider = self.dal.get_by_id(SupportProvider, support_provider_id)
            shelter = self.dal.get_by_id(Shelter, shelter_id)

            # Check if the shelter is associated with the support provider
            if shelter.support_provider != support_provider:
                logger.warning(f"Support Provider {support_provider_id} not authorized to update shelter {shelter_id}.")
                return False

            # Update the shelter details
            updated_shelter = self.dal.update(shelter, **shelter_data)

            if updated_shelter:
                # Log the activity
                user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                self.dal.create(UserActivity, user=support_provider.user, activity_type='shelter_updated', ip_address=user_ip)
                logger.info(f"Shelter {shelter_id} updated successfully by Support Provider {support_provider_id}.")
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating shelter for Support Provider {support_provider_id}: {e}", exc_info=True)
            return False