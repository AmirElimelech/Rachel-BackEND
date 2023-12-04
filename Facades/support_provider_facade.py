
import logging
from Rachel.DAL import DAL
from .base_facade import BaseFacade
from Rachel.models import User, SupportProvider, FeedbackResponse, UserFeedback,UserActivity,Shelter,Notification




logger = logging.getLogger(__name__)


class SupportProviderFacade(BaseFacade):


    def __init__(self):
        super().__init__()
        self.dal = DAL()  # Initialize the DAL instance






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
            support_provider = self.dal.get_by_id(SupportProvider, support_provider_id)

            # Check if feedback is related to this support provider
            if not feedback or feedback.support_provider != support_provider:
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
                # Update the feedback status
                feedback.status = 'responded'
                feedback.save()

                # Log the user activity for feedback response submission
                user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                self.dal.create(UserActivity, user=support_provider.user, activity_type='feedback_responded', ip_address=user_ip)
                
                # Send notification to the civilian who submitted the feedback
                self.dal.create(
                    Notification,
                    recipient=feedback.user,
                    title="Feedback Response",
                    message=f"Your feedback has been responded to by {support_provider.user.username}.",
                    notification_type='feedback'
                )

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
        



    def view_my_feedback(self, requesting_user_id, support_provider_id):

        """
        Retrieves all feedback associated with a specific support provider. 
        Ensures that support providers can only see their own feedback.

        Args:
            requesting_user_id (int): The ID of the user making the request.
            support_provider_id (int): The ID of the support provider whose feedback is being retrieved.

        Returns:
            list: A list of dictionaries containing details of each feedback if authorized; otherwise, an empty list or error message.
        """
        
        try:
            # Check if the requesting user is the same as the support provider
            if requesting_user_id != support_provider_id:
                logger.warning(f"User ID {requesting_user_id} is not authorized to view feedback of Support Provider ID {support_provider_id}.")
                return {'error': 'Permission denied'}

            support_provider = self.dal.get_by_id(SupportProvider, support_provider_id)
            if not support_provider:
                logger.warning(f"No support provider found with ID {support_provider_id}.")
                return []

            feedbacks = self.dal.filter(UserFeedback, support_provider=support_provider)
            feedback_list = [{
                'feedback_id': feedback.id,
                'user': feedback.user.username,
                'feedback_text': feedback.feedback_text,
                'created_at': feedback.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'status': getattr(feedback, 'status', 'pending')  # Assuming a 'status' field
            } for feedback in feedbacks]

            logger.info(f"Retrieved feedback for Support Provider ID {support_provider_id}.")
            return feedback_list

        except Exception as e:
            logger.error(f"Error retrieving feedback for Support Provider ID {support_provider_id}: {e}", exc_info=True)
            return []