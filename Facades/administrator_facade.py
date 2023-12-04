import logging
from Rachel.DAL import DAL
from django.urls import reverse
from django.utils import timezone
from axes.models import AccessAttempt
from django.core.mail  import  send_mail
from django.utils.encoding import force_bytes
from django.utils.http import   urlsafe_base64_encode
from Rachel.utils import request_password_reset , can_request_password_reset
from Rachel.models import User, SupportProvider, Shelter, UserActivity, UserFeedback, Notification




logger = logging.getLogger(__name__)


class AdministratorFacade:

    def __init__(self):
        super().__init__()

        self.dal = DAL()



    def close_feedback(self, admin_user_id, feedback_id):

        """
        Closes a specific feedback case, marking it as resolved.

        This method is restricted to users with 'Administrator' privileges. It updates the status of the feedback,
        indicating that it has been reviewed and closed by an administrator. It also records which administrator 
        closed the feedback and the timestamp when it was closed.

        Args:
            admin_user_id (int): The ID of the administrator attempting to close the feedback.
            feedback_id (int): The ID of the feedback to be closed.

        Returns:
            dict: A response indicating whether the operation was successful or not. 
                Returns an error message if unauthorized, if the feedback is not found, or if other issues occur.

        Raises:
            Exception: If an unexpected error occurs during the process.
        """
        
        admin_user = self.dal.get_by_id(User, admin_user_id)
        if not admin_user.groups.filter(name='Administrator').exists():
            logger.warning(f"User ID {admin_user_id} is not authorized to close feedback.")
            return {'error': 'Permission denied'}

        feedback = self.dal.get_by_id(UserFeedback, feedback_id)
        if feedback:
            feedback.status = 'closed'
            feedback.closed_by = admin_user  # Assuming you have a 'closed_by' field
            feedback.closed_at = timezone.now()  # Assuming you have a 'closed_at' field
            feedback.save()
            logger.info(f"Feedback ID {feedback_id} closed by Administrator ID {admin_user_id}.")
            # Optional: Notify relevant parties
            return {'success': True}
        else:
            logger.warning(f"No feedback found with ID {feedback_id}.")
            return {'error': 'Feedback not found'}



    def fetch_all_feedback(self):

        """
        Fetches all user feedback from the database.

        This method retrieves every feedback record, including details about the user who provided the feedback, 
        the support provider it is related to, and the feedback content. 

        Returns:
            list: A list of dictionaries, each representing a feedback record.

        Raises:
            Exception: If an unexpected error occurs during retrieval.
        """

        try:
            all_feedback = self.dal.get_all(UserFeedback)

            feedback_list = []
            for feedback in all_feedback:
                feedback_details = {
                    'feedback_id': feedback.id,
                    'user': feedback.user.username,
                    'support_provider': feedback.support_provider.user.username if feedback.support_provider else None,
                    'feedback_text': feedback.feedback_text,
                    'created_at': feedback.created_at,
                    'status': feedback.status,
                }
                
                feedback_list.append(feedback_details)

            logger.info(f"Fetched {len(feedback_list)} feedback records.")
            return feedback_list

        except Exception as e:
            logger.error(f"Error fetching all feedback: {e}", exc_info=True)
            raise




    def send_notification_to_all_civilians(self, request, admin_user_id, title, message, notification_type='info'):

        """
        Sends a notification to all civilian users.

        Args:
            request: The HTTP request object, used to get the administrator's IP address.
            admin_user_id (int): The ID of the administrator sending the notification.
            title (str): The title of the notification.
            message (str): The message content of the notification.
            notification_type (str): The type of the notification (default is 'info').

        Returns:
            dict: A response indicating success or an error message.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to send notifications.")
                return {'error': 'Permission denied'}

            civilians = User.objects.filter(groups__name='Civilian')
            for civilian in civilians:
                self.dal.create(Notification, 
                                recipient=civilian, 
                                title=title, 
                                message=message,
                                notification_type=notification_type)

            # Log the action
            user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            self.dal.create(UserActivity, user=admin_user, activity_type='notification_sent', ip_address=user_ip)

            logger.info(f"Notification sent to all civilians by Administrator ID {admin_user_id}.")
            return {'success': True}
        
        except Exception as e:
            logger.error(f"Error in sending notification to all civilians: {e}", exc_info=True)
            return {'error': 'An error occurred during notification dispatch'}
            




    def send_notification_to_all_support_providers(self, request, admin_user_id, title, message, notification_type='info'):

        """
        Sends a notification to all support provider users.

        Args:
            request: The HTTP request object, used to get the administrator's IP address.
            admin_user_id (int): The ID of the administrator sending the notification.
            title (str): The title of the notification.
            message (str): The message content of the notification.
            notification_type (str): The type of the notification (default is 'info').

        Returns:
            dict: A response indicating success or an error message.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to send notifications.")
                return {'error': 'Permission denied'}

            support_providers = User.objects.filter(groups__name='SupportProvider')
            for support_provider in support_providers:
                self.dal.create(Notification, 
                                recipient=support_provider, 
                                title=title, 
                                message=message,
                                notification_type=notification_type)

            # Log the action
            user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            self.dal.create(UserActivity, user=admin_user, activity_type='notification_sent', ip_address=user_ip)

            logger.info(f"Notification sent to all support providers by Administrator ID {admin_user_id}.")
            return {'success': True}
        
        except Exception as e:
            logger.error(f"Error in sending notification to all support providers: {e}", exc_info=True)
            return {'error': 'An error occurred during notification dispatch'}




    def activate_user(self, request, admin_user_id, user_id_to_activate):

        """
        Activates a user account.

        Args:
            request: The HTTP request object, used to get the administrator's IP address.
            admin_user_id (int): The ID of the administrator performing the activation.
            user_id_to_activate (int): The ID of the user whose account is to be activated.

        Returns:
            dict: A response indicating success or an error message.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to activate users.")
                return {'error': 'Permission denied'}

            user_to_activate = self.dal.get_by_id(User, user_id_to_activate)
            if user_to_activate.is_active:
                logger.warning(f"User ID {user_id_to_activate} is already active.")
                return {'error': 'User already active'}

            user_to_activate.is_active = True
            user_to_activate.save()

            # Log the action
            user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            self.dal.create(UserActivity, user=admin_user, activity_type='account_activated', ip_address=user_ip, description=f"Activated user ID {user_id_to_activate}")

            logger.info(f"User ID {user_id_to_activate} activated by Administrator ID {admin_user_id}.")
            return {'success': True}
        
        except Exception as e:
            logger.error(f"Error in activating user ID {user_id_to_activate}: {e}", exc_info=True)
            return {'error': 'An error occurred during user activation'}



    def deactivate_user(self, request, admin_user_id, user_id_to_deactivate):

        """
        Deactivates a user account.

        Args:
            request: The HTTP request object, used to get the administrator's IP address.
            admin_user_id (int): The ID of the administrator performing the deactivation.
            user_id_to_deactivate (int): The ID of the user whose account is to be deactivated.

        Returns:
            dict: A response indicating success or an error message.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to deactivate users.")
                return {'error': 'Permission denied'}

            user_to_deactivate = self.dal.get_by_id(User, user_id_to_deactivate)
            if not user_to_deactivate.is_active:
                logger.warning(f"User ID {user_id_to_deactivate} is already inactive.")
                return {'error': 'User already inactive'}

            user_to_deactivate.is_active = False
            user_to_deactivate.save()

            # Log the action
            user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            self.dal.create(UserActivity, user=admin_user, activity_type='account_deactivated_by_admin', ip_address=user_ip, description=f"Deactivated user ID {user_id_to_deactivate}")

            logger.info(f"User ID {user_id_to_deactivate} deactivated by Administrator ID {admin_user_id}.")
            return {'success': True}
        
        except Exception as e:
            logger.error(f"Error in deactivating user ID {user_id_to_deactivate}: {e}", exc_info=True)
            return {'error': 'An error occurred during user deactivation'}






    def clear_specific_access_attempts(self, request, admin_user_id, ip_address):

        """
        Clears access attempts for a specific IP address from the Axes AccessAttempt table.

        Args:
            request: The HTTP request object, used to get the administrator's IP address.
            admin_user_id (int): The ID of the administrator performing the operation.
            ip_address (str): The IP address for which the access attempts are to be cleared.

        Returns:
            dict: A response indicating success or an error message.
        """
        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to clear access attempts.")
                return {'error': 'Permission denied'}

            # Clear access attempts for the specified IP address
            AccessAttempt.objects.filter(ip_address=ip_address).delete()

            # Log the action
            admin_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            self.dal.create(UserActivity, user=admin_user, activity_type='access_attempts_cleared', ip_address=admin_ip, description=f"Cleared access attempts for IP {ip_address}")

            logger.info(f"Access attempts for IP {ip_address} cleared by Administrator ID {admin_user_id}.")
            return {'success': True}

        except Exception as e:
            logger.error(f"Error in clearing access attempts for IP {ip_address}: {e}", exc_info=True)
            return {'error': 'An error occurred during the clearing of access attempts'}



    def activate_shelter(self, request, admin_user_id, shelter_id):

        """
        Activates a shelter. Only administrators can perform this action.

        Args:
            request: The HTTP request object, used to get the administrator's IP address.
            admin_user_id (int): The ID of the administrator performing the action.
            shelter_id (int): The ID of the shelter to be activated.

        Returns:
            dict: A response indicating success or an error message.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to activate shelter.")
                return {'error': 'Permission denied'}

            shelter = self.dal.get_by_id(Shelter, shelter_id)
            if shelter:
                shelter.is_active = True
                shelter.save()

                # Log the action
                admin_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                self.dal.create(UserActivity, user=admin_user, activity_type='shelter_activated', ip_address=admin_ip, description=f"Activated shelter ID {shelter_id}")

                logger.info(f"Shelter ID {shelter_id} activated by Administrator ID {admin_user_id}.")
                return {'success': True}
            else:
                logger.warning(f"No shelter found with ID {shelter_id}.")
                return {'error': 'Shelter not found'}

        except Exception as e:
            logger.error(f"Error in activating shelter ID {shelter_id}: {e}", exc_info=True)
            return {'error': 'An error occurred during the activation of the shelter'}




    def deactivate_shelter(self, request, admin_user_id, shelter_id):

        """
        Deactivates a shelter. Only administrators can perform this action.

        Args:
            request: The HTTP request object, used to get the administrator's IP address.
            admin_user_id (int): The ID of the administrator performing the action.
            shelter_id (int): The ID of the shelter to be deactivated.

        Returns:
            dict: A response indicating success or an error message.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to deactivate shelter.")
                return {'error': 'Permission denied'}

            shelter = self.dal.get_by_id(Shelter, shelter_id)
            if shelter:
                shelter.is_active = False
                shelter.save()

                # Log the action
                admin_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                self.dal.create(UserActivity, user=admin_user, activity_type='shelter_deactivated', ip_address=admin_ip, description=f"Deactivated shelter ID {shelter_id}")

                logger.info(f"Shelter ID {shelter_id} deactivated by Administrator ID {admin_user_id}.")
                return {'success': True}
            else:
                logger.warning(f"No shelter found with ID {shelter_id}.")
                return {'error': 'Shelter not found'}

        except Exception as e:
            logger.error(f"Error in deactivating shelter ID {shelter_id}: {e}", exc_info=True)
            return {'error': 'An error occurred during the deactivation of the shelter'}






    def monitor_user_activity(self, admin_user_id, user_id):

        """
        Fetches the activity log for a specific user. Only administrators can access this method.

        Args:
            request: The HTTP request object, used to get the administrator's IP address.
            admin_user_id (int): The ID of the administrator performing the action.
            user_id (int): The ID of the user whose activity log is to be fetched.

        Returns:
            list: A list of dictionaries containing details of each user activity or an error message.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to monitor user activity.")
                return {'error': 'Permission denied'}

            target_user = self.dal.get_by_id(User, user_id)
            if not target_user:
                logger.warning(f"No user found with ID {user_id}.")
                return {'error': 'User not found'}

            activities = self.dal.filter(UserActivity, user=target_user).order_by('-timestamp') # activities are sorted in descending order of their timestamp.
            activity_log = [{
                'activity_type': activity.activity_type,
                'timestamp': activity.timestamp,
                'ip_address': activity.ip_address
            } for activity in activities]

            logger.info(f"User activities fetched for user ID {user_id} by Administrator ID {admin_user_id}.")
            return activity_log

        except Exception as e:
            logger.error(f"Error fetching user activities for user ID {user_id}: {e}", exc_info=True)
            return {'error': 'An error occurred while fetching user activities'}




    def admin_initiated_password_reset(self, admin_user_id, user_id_to_reset, request):

        """
        Allows an administrator to initiate the password reset process for a user.

        Args:
            admin_user_id (int): The ID of the administrator performing the reset.
            user_id_to_reset (int): The ID of the user whose password is to be reset.
            request: The HTTP request object, used to get the administrator's IP address.

        Returns:
            dict: A response indicating success or an error message.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                return {'error': 'Permission denied'}

            user_to_reset = self.dal.get_by_id(User, user_id_to_reset)
            if not user_to_reset:
                return {'error': 'User not found'}

            # Assuming the use of a function like can_request_password_reset() to check eligibility
            if not can_request_password_reset(user_to_reset):
                return {'error': 'Password reset not allowed for this user'}

            # Use the existing reset password logic
            token = request_password_reset(user_to_reset, request)
            uid = urlsafe_base64_encode(force_bytes(user_to_reset.pk))
            reset_link = f"https://your-frontend-domain.com{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"

            send_mail(
                subject='Password Reset Request',
                message=f"Please click on the link to reset your password: {reset_link}",
                from_email='Rachel.for.Israel@gmail.com',
                recipient_list=[user_to_reset.email],
                fail_silently=False,
            )

            # Log the action
            admin_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            self.dal.create(UserActivity, user=admin_user, activity_type='password_reset_request', ip_address=admin_ip, description=f"Password reset initiated for user ID {user_id_to_reset}")

            return {'success': 'Password reset email sent successfully'}

        except Exception as e:
            logger.error(f"Error in admin_initiated_password_reset method: {e}")
            return {'error': 'An error occurred during the password reset process'}



    def search_users(self, admin_user_id, search_criteria):
        
        """
        Dynamically searches and filters users based on a variety of criteria such as username, email, role, etc.
        This method builds a query dynamically based on the criteria provided by the frontend and uses the DAL for database operations.

        Args:
            admin_user_id (int): The ID of the administrator performing the search.
            search_criteria (dict): A dictionary containing the criteria to filter users by.

        Returns:
            list: List of users matching the criteria or an error message.
        """

        try:
            # Validate admin user using DAL
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user or not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User {admin_user_id} attempted to search without permission.")
                return {'error': 'Permission denied'}

            # Build dynamic query based on search criteria
            query_kwargs = {f"{key}__icontains": value for key, value in search_criteria.items()}

            # Execute query using DAL
            users = self.dal.filter(User, **query_kwargs)

            # Check if no users are found
            if not users:
                logger.info(f"No users found for search criteria: {search_criteria}")

            # Construct the response
            user_list = [{'username': user.username, 'email': user.email, 'role': [group.name for group in user.groups.all()]} for user in users]
            return user_list

        except Exception as e:
            logger.error(f"Error in searching users: {e}", exc_info=True)
            return {'error': str(e)}
        



    def generate_lowest_rated_support_provider_report(self, admin_user_id):

        """
        Generates a report for the lowest-rated support provider.

        Args:
            admin_user_id (int): The ID of the administrator requesting the report.

        Returns:
            dict: A dictionary containing the data of the lowest-rated support provider or an error message.

        Raises:
            Exception: If an unexpected error occurs during report generation.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to generate reports.")
                return {'error': 'Permission denied'}

            # Assuming 'rating' field exists in SupportProvider model
            lowest_rated_provider = SupportProvider.objects.order_by('rating').first()

            if not lowest_rated_provider:
                return {'message': 'No support providers available for reporting.'}

            feedbacks = self.dal.filter(UserFeedback, support_provider=lowest_rated_provider)
            responded_feedbacks = feedbacks.filter(response__isnull=False)

            report = {
                'support_provider': lowest_rated_provider.user.username,
                'total_feedback': feedbacks.count(),
                'responded_feedback': responded_feedbacks.count(),
                'average_rating': lowest_rated_provider.rating
            }

            logger.info(f"Lowest Rated Support Provider Report generated by Administrator ID {admin_user_id}.")
            return report

        except Exception as e:
            logger.error(f"Error generating Lowest Rated Support Provider Report: {e}", exc_info=True)
            return {'error': 'An error occurred during report generation'}




    def generate_highest_rated_support_provider_report(self, admin_user_id):

        """
        Generates a report for the highest-rated support provider.

        Args:
            admin_user_id (int): The ID of the administrator requesting the report.

        Returns:
            dict: A dictionary containing the data of the highest-rated support provider or an error message.

        Raises:
            Exception: If an unexpected error occurs during report generation.
        """

        try:
            admin_user = self.dal.get_by_id(User, admin_user_id)
            if not admin_user.groups.filter(name='Administrator').exists():
                logger.warning(f"User ID {admin_user_id} is not authorized to generate reports.")
                return {'error': 'Permission denied'}

            highest_rated_provider = SupportProvider.objects.order_by('-rating').first()

            if not highest_rated_provider:
                return {'message': 'No support providers available for reporting.'}

            feedbacks = self.dal.filter(UserFeedback, support_provider=highest_rated_provider)
            responded_feedbacks = feedbacks.filter(response__isnull=False)

            report = {
                'support_provider': highest_rated_provider.user.username,
                'total_feedback': feedbacks.count(),
                'responded_feedback': responded_feedbacks.count(),
                'average_rating': highest_rated_provider.rating
            }

            logger.info(f"Highest Rated Support Provider Report generated by Administrator ID {admin_user_id}.")
            return report

        except Exception as e:
            logger.error(f"Error generating Highest Rated Support Provider Report: {e}", exc_info=True)
            return {'error': 'An error occurred during report generation'}
   