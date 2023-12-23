import logging
import traceback
from Rachel.DAL import DAL
from rest_framework import status
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.core.exceptions import ValidationError
from Facades.anonymous_facade import AnonymousFacade
from Rachel.models import Civilian, SupportProvider, City, Country
from rest_framework.decorators import api_view , permission_classes
from Api.serializers import UserSerializer, CivilianProfileSerializer, SupportProviderProfileSerializer, CountrySerializer,CitySerializer

logger = logging.getLogger(__name__)







@api_view(['POST'])
@permission_classes([AllowAny])
def register_user_api(request):
    """
    API endpoint for user registration.

    This endpoint processes the registration of a new user. It expects 'user_type' and other
    registration-related data in the request body.

    Args:
        request: The HTTP request object containing user data.

    Returns:
        Response: A Response object containing the serialized user data if registration is successful,
                  otherwise an error message with appropriate status code.
    """
    logger.info("Processing user registration request")

    user_type = request.data.get('user_type')
    if user_type not in ['civilian', 'support_provider']:
        return Response({"error": "Invalid user type"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        facade = AnonymousFacade()
        user = facade.register_user(request, user_type, request.data)
        if user:
            # Determine the appropriate serializer for the user type
            profile_instance = Civilian.objects.get(user=user) if user_type == 'civilian' else SupportProvider.objects.get(user=user)
            profile_serializer = CivilianProfileSerializer(profile_instance) if user_type == 'civilian' else SupportProviderProfileSerializer(profile_instance)
            
            return Response({
                'user': UserSerializer(user).data,
                'profile': profile_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            logger.warning("User registration failed due to form validation errors")
            return Response({"error": "Registration failed"}, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError as e:
        logger.error(f"Database integrity error during registration: {e}")
        return Response({"error": "Database integrity error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except ValidationError as e:
        error_message = e.message_dict if hasattr(e, 'message_dict') else {'error': [str(e)]}
        custom_error_message = {}
        for field, errors in error_message.items():
            if field in ['username', 'email', 'identification_number', 'phone_number', 'password2', 'city','profile_picture', 'active_until' ,'support_provider_categories', 'languages_spoken','terms_accepted', 'database']:
                custom_error_message[field] = errors[0] if errors else "Invalid input"
        if custom_error_message:
            logger.warning(f"Validation error during registration: {custom_error_message}")
            return Response({"errors": custom_error_message}, status=status.HTTP_400_BAD_REQUEST)


    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}, type: {type(e).__name__}, args: {e.args}, cause: {getattr(e, '__cause__', None)}, traceback: {traceback.format_exc()}")
        return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    # Return a generic error if no user is created and no specific exception is caught
    logger.warning("User registration failed for an unknown reason.")
    return Response({"error": "Registration failed for an unknown reason"}, status=status.HTTP_400_BAD_REQUEST)









@api_view(['POST'])
@permission_classes([AllowAny])
def login_user_api(request):

    """
    API endpoint for user login.

    This endpoint authenticates a user and provides a token upon successful login.
    It expects 'username' and 'password' in the request body.

    Args:
        request: The HTTP request object containing login credentials.

    Returns:
        Response: A Response object containing the authentication token if login is successful,
                  otherwise an error message with appropriate status code.
    """

    logger.info("Processing user login request")
    try:
        facade = AnonymousFacade()
        token_key = facade.login_user(request, request.data.get('username'), request.data.get('password'))
        if token_key:
            logger.info("User login successful")
            return Response({'token': token_key}, status=status.HTTP_200_OK)
        else:
            logger.warning("Invalid login credentials")
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    except ValidationError as e:
        logger.warning(f"Validation error during login: {e}")
        return Response({"error": str(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['POST'])
@permission_classes([AllowAny])
def contact_us_api(request):

    """
    API endpoint for handling 'Contact Us' form submissions.

    This endpoint expects 'name', 'email', 'subject', and 'message' in the request body.

    Args:
        request: The HTTP request object containing contact form data.

    Returns:
        Response: A Response object indicating successful form submission or failure with an appropriate status code.
    """


    logger.info("Processing contact us request")
    try:
        facade = AnonymousFacade()
        success = facade.contact_us(
            request.data.get('name'),
            request.data.get('email'),
            request.data.get('subject'),
            request.data.get('message')
        )
        if success:
            logger.info("Contact form submitted successfully")
            return Response({"message": "Your query has been sent successfully"}, status=status.HTTP_200_OK)

    except ValidationError as e:
        # Format the validation errors for the response
        formatted_errors = {field: [str(error) for error in errors] for field, errors in e.message_dict.items()}
        return Response({"errors": formatted_errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Unexpected error in contact us: {e}")
        return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_api(request):

    """
    API endpoint for password reset requests.

    This endpoint processes password reset requests. It expects the 'email' of the user
    who wants to reset their password in the request body.

    Args:
        request: The HTTP request object containing the user's email.

    Returns:
        Response: A Response object indicating whether the password reset email was sent successfully
                  or if there was a failure, along with an appropriate status code.
    """
    
    logger.info("Processing password reset request")
    try:
        facade = AnonymousFacade()
        success = facade.reset_password(request, request.data.get('email'))
        if success:
            logger.info("Password reset email sent successfully")
            return Response({"message": "Password reset email sent successfully"}, status=status.HTTP_200_OK)
    except ValidationError as e:
        if hasattr(e, 'message_dict'):
            # If the errors have a dictionary structure
            formatted_errors = {field: e.message_dict[field] for field in e.message_dict}
            return Response({"errors": formatted_errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Single message or list of messages
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error in password reset: {e}")
        return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([AllowAny])
def country_list_api(request):

    """
    API endpoint for retrieving a list of countries.

    Returns:
        Response: A Response object containing a list of countries.
    """

    logger.info("Processing country list request")
    try:
        countries = DAL().get_all(Country)
        serializer = CountrySerializer(countries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error during country list retrieval: {e}")
        return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['GET'])
@permission_classes([AllowAny])
def city_list_api(request):

    """
    API endpoint for retrieving a list of cities. Filters cities by country.

    Query Parameters:
        country_id: The ID of the country to filter cities.

    Returns:
        Response: A Response object containing a list of cities or an error message.
    """

    logger.info("Processing city list request")
    try:
        country_id = request.query_params.get('country_id')
        if not country_id:
            return Response({"error": "A country_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the country exists
        country_exists = DAL().get_by_id(Country, country_id)
        if not country_exists:
            return Response({"error": "No such country exists"}, status=status.HTTP_404_NOT_FOUND)

        cities = DAL().filter(City, country_id=country_id)
        if not cities:
            return Response({"message": "No cities found for the specified country"}, status=status.HTTP_404_NOT_FOUND)

        serializer = CitySerializer(cities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Unexpected error during city list retrieval: {e}")
        return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
