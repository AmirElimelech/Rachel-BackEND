import logging
import requests
from Rachel.DAL import DAL 
from django.db.models import Q
from .base_facade import BaseFacade
from django.contrib.auth.models import User
from Forms.user_forms import UserFeedbackForm
from Rachel.models import Shelter , SearchHistory, UserFeedback, UserActivity, SupportProvider, SupportProviderRating, Notification




 

logger = logging.getLogger(__name__)

class CivilianFacade(BaseFacade):

    def __init__(self):
        super().__init__()

        self.dal = DAL()  # Initialize the DAL instance




    def view_shelter(self, shelter_id):
        """
        Retrieves details of a specific shelter.

        Args:
            shelter_id (int): The ID of the shelter to retrieve.

        Returns:
            dict: Shelter details if found; an empty dict otherwise.

        """
        try:
            shelter = self.dal.get_by_id(Shelter, shelter_id)
            if not shelter:
                logger.warning(f"No shelter found with ID {shelter_id}.")
                return {}

            shelter_details = {
                'name': shelter.name,
                'address': shelter.address,
                'city': shelter.city.name if shelter.city else None,
                'country': shelter.country.name if shelter.country else None,
                'latitude': shelter.latitude,
                'longitude': shelter.longitude,
                'capacity': shelter.capacity,
                'phone': shelter.phone if shelter.support_provider else None,
                'email': shelter.email if shelter.support_provider else None,
                'picture_url': shelter.picture.url if shelter.picture else None
            }
            logger.info(f"Shelter details retrieved for ID {shelter_id}.")
            return shelter_details

        except Exception as e:
            logger.error(f"Error retrieving shelter with ID {shelter_id}: {e}", exc_info=True)
            raise


    def view_search_history(self, user_id):

        """
        Retrieves the search history for a civilian user.

        Args:
            user_id (int): The ID of the user whose search history to retrieve.

        Returns:
            list: A list of search history records; each record is a dict.
        """

        try:
            user = self.dal.get_by_id(User, user_id)
            if not user:
                logger.warning(f"No user found with ID {user_id}.")
                return []

            search_histories = self.dal.filter(SearchHistory, user=user)
            history_list = []

            for history in search_histories:
                history_record = {
                    'query': history.query,
                    'searched_on': history.created_at.strftime("%d-%m-%Y %H:%M:%S")
                    
                }
                history_list.append(history_record)

            logger.info(f"Search history retrieved for user ID {user_id}.")
            return history_list

        except Exception as e:
            logger.error(f"Error retrieving search history for user ID {user_id}: {e}", exc_info=True)
            raise



    def send_feedback(self, user_id, feedback_text, support_provider_id, request):

        """
        Allows a civilian to submit feedback and logs the activity.

        Args:
            user_id (int): The ID of the user submitting the feedback.
            feedback_text (str): The text of the feedback being submitted.
            support_provider_id (int): The ID of the support provider to whom the feedback is directed.
            request: The HTTP request object for getting the IP address.

        Returns:
            bool: True if feedback submission is successful, False otherwise.
        """

        try:
            feedback_data = {'feedback_text': feedback_text}
            feedback_form = UserFeedbackForm(data=feedback_data)

            feedback_submission_successful = False  # Initialize the variable

            if feedback_form.is_valid():
                user_feedback = UserFeedback(
                    user_id=user_id,
                    support_provider_id=support_provider_id,
                    feedback_text=feedback_form.cleaned_data['feedback_text']
                )
                user_feedback.save()

                # Log the user feedback activity
                user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                self.dal.create(UserActivity, user_id=user_id, activity_type='user_feedback', ip_address=user_ip)

                logger.info(f"Feedback submitted successfully by user ID {user_id}.")
                feedback_submission_successful = True  # Set the variable to True if feedback submission is successful

                # Send notification to the Support Provider about the new feedback
                support_provider = self.dal.get_by_id(SupportProvider, support_provider_id)
                if support_provider:
                    self.dal.create(
                        Notification,
                        recipient=support_provider.user,
                        title="New Feedback Received",
                        message=f"You have received new feedback from {user_feedback.user.username}.",
                        notification_type='feedback'
                    )
            else:
                logger.warning(f"Feedback form validation errors: {feedback_form.errors.as_json()}")

        except Exception as e:
            logger.error(f"Unexpected error during feedback submission by user ID {user_id}: {e}", exc_info=True)
            raise

        return feedback_submission_successful





    def rate_support_provider(self, user_id, support_provider_id, rating, experience, request):

        """
        Allows a user to rate a support provider and write about their experience.

        Args:
            user_id (int): The ID of the user submitting the rating.
            support_provider_id (int): The ID of the support provider being rated.
            rating (int): The rating given by the user.
            experience (str): The user's experience with the support provider.
            request: The HTTP request object for getting the IP address.

        Returns:
            bool: True if the rating and experience submission is successful, False otherwise.
        """
         
        try:
            user = self.dal.get_by_id(User, user_id)
            support_provider = self.dal.get_by_id(SupportProvider, support_provider_id)

            # Create or update the rating
            rating_obj, created = SupportProviderRating.objects.get_or_create(
                user=user,
                support_provider=support_provider,
                defaults={'rating': rating, 'experience': experience}
            )

            if not created:
                rating_obj.rating = rating
                rating_obj.experience = experience
                rating_obj.save()

            # Update the average rating of the support provider
            support_provider.update_average_rating()

            # Log the user activity
            user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            self.dal.create(UserActivity, user=user, activity_type='support_provider_rated', ip_address=user_ip)

            self.dal.create(
            Notification,
            recipient=support_provider.user,
            title="New Rating Received",
            message=f"You have received a new rating from {user.username}.",
            notification_type='rating'
            )
            

            return True
        except Exception as e:
            logger.error(f"Error in rate_support_provider: {e}")
            return False
        





    def search_for_support_provider(self, name=None, city=None, kosher=None, rating=None, looking_to_earn=None, accessible_facilities=None, languages=None, categories=None):
        """
        Search for support providers based on various criteria. If no criteria are provided, returns all support providers.

        Args:
            name (str): Partial or full name to search.
            city (str): City name to filter support providers.
            kosher (bool): Filter for kosher services.
            rating (int): Minimum rating to filter.
            looking_to_earn (bool): Filter providers looking to earn.
            accessible_facilities (bool): Filter providers with accessible facilities.
            languages (list): List of language IDs to filter providers by the languages they speak.
            categories (list): List of category IDs to filter providers by their service categories.

        Returns:
            list: List of support providers matching the criteria.
        """
        try:
            filters = Q()

            if name:
                filters &= Q(user__username__icontains=name) | Q(user__first_name__icontains=name) | Q(user__last_name__icontains=name)
            if city:
                filters &= Q(city__name__icontains=city)
            if kosher is not None:
                filters &= Q(kosher=kosher)
            if rating is not None:
                filters &= Q(rating__gte=rating)
            if looking_to_earn is not None:
                filters &= Q(looking_to_earn=looking_to_earn)
            if accessible_facilities is not None:
                filters &= Q(accessible_facilities=accessible_facilities)
            if languages:
                filters &= Q(languages_spoken__id__in=languages)
            if categories:
                filters &= Q(support_provider_categories__id__in=categories)

            support_providers = self.dal.filter(SupportProvider, filters).distinct()

            return [{
                'username': provider.user.username,
                'name': f"{provider.user.first_name} {provider.user.last_name}",
                'city': provider.city.name if provider.city else None,
                'country': provider.country.name if provider.country else None,
                'kosher': provider.kosher,
                'rating': provider.rating,
                'looking_to_earn': provider.looking_to_earn,
                'accessible_facilities': provider.accessible_facilities,
                'languages': [language.name for language in provider.languages_spoken.all()],
                'categories': [category.name for category in provider.support_provider_categories.all()],
                'additional_info': provider.additional_info,
                'phone_number': provider.phone_number.as_e164 if provider.phone_number else None,
                'address': provider.address  
            } for provider in support_providers]

        except Exception as e:
            logger.error(f"Error searching for support providers: {e}", exc_info=True)
            raise



    def search_for_shelter(self, city=None):
        
        """
        Search for shelters based on the city.

        Args:
            city (str): City name to filter shelters.

        Returns:
            list: List of shelters in the specified city.
        """

        try:
            shelters = self.dal.filter(Shelter, city__name__icontains=city) if city else self.dal.get_all(Shelter)

            shelter_list = []
            for shelter in shelters:
                shelter_details = {
                    'name': shelter.name,
                    'address': shelter.address,
                    'city': shelter.city.name if shelter.city else None,
                    'country': shelter.country.name if shelter.country else None,
                    'phone': shelter.phone if shelter.support_provider else None,
                    'email': shelter.email if shelter.support_provider else None,
                    'picture_url': shelter.picture.url if shelter.picture else None
                }
                shelter_list.append(shelter_details)

            logger.info(f"{len(shelter_list)} shelters found in city: {city}")
            return shelter_list

        except Exception as e:
            logger.error(f"Error retrieving shelters in city {city}: {e}", exc_info=True)
            raise




    
        

    def address_lookup(self, user_id, query, request):

        """
        Perform an address lookup and log the activity.

        Args:
            user_id (int): ID of the user performing the lookup.
            query (str): The address query string.
            request: The HTTP request object for getting the IP address.

        Returns:
            dict: The results from the Nominatim API or an error message.
        """

        try:
            # API Call to Nominatim
            base_url = "https://nominatim.openstreetmap.org/search.php"
            params = {'q': query, 'format': 'jsonv2'}
            response = requests.get(base_url, params=params)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Address lookup successful for query: {query}")
            else:
                logger.error(f"Address lookup failed for query: {query}")
                data = {'error': 'Unable to fetch location data'}

            # Log the user activity
            user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
            self.dal.create(UserActivity, user_id=user_id, activity_type='address_lookup', ip_address=user_ip)

            return data

        except Exception as e:
            logger.error(f"Error during address lookup for query: {query}: {e}", exc_info=True)
            return {'error': 'An error occurred during the address lookup'}
        


    def get_my_notifications(self, user_id):

        """
        Retrieve notifications for the civilian user.

        Args:
            user_id (int): The ID of the civilian user.

        Returns:
            list: Notifications list for the civilian user.
        """

        return self.get_user_notifications(user_id)