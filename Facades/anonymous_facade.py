

import logging
from Rachel.DAL import DAL
from django.urls import reverse
from Rachel.models import UserActivity
from django.core.mail  import  send_mail
from django.contrib.auth.models import User 
from django.utils.encoding import force_bytes
from django.db import transaction,IntegrityError
from Forms.miscellaneous_forms import ContactForm
from Forms.user_forms import  CivilianRegisterForm
from rest_framework.authtoken.models  import  Token
from django.core.exceptions import   ValidationError
from django.utils.http import   urlsafe_base64_encode
from django.contrib.auth import    authenticate, login
from django.utils.translation  import gettext_lazy as  _
from Forms.support_provider_forms import SupportProviderRegisterForm
from Rachel.utils import alert_for_suspicious_activity , request_password_reset , can_request_password_reset








logger = logging.getLogger(__name__)



class AnonymousFacade:

    def __init__(self):


        self.dal = DAL()




    def register_user(self, request, user_type, form_data):

        """
        Registers a new user using the appropriate form based on user type.

        Args:
        request: HTTP request object for context.
        user_type (str): Type of user ('civilian' or 'support_provider').
        form_data (dict): Data submitted in the registration form.

        Returns:
        User object if registration is successful, None otherwise.

        Raises:
        ValidationError if form validation fails.
        Exception for unexpected errors.
        """

        user_ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        logger.info(f"Registering new {user_type} from IP: {user_ip}")

        registration_successful = False  # Initialize the variable

        try:
            with transaction.atomic():
                if user_type == 'civilian':
                    form = CivilianRegisterForm(form_data)
                elif user_type == 'support_provider':
                    form = SupportProviderRegisterForm(form_data)
                else:
                    raise ValueError(f"Invalid user type: {user_type}")

                if form.is_valid():
                    user = form.save(commit=True)
                    logger.info(f"User {user.username} ({user_type}) registered successfully")
                    self.dal.create(UserActivity, user=user, activity_type='account_creation', ip_address=user_ip)
                    registration_successful = True  # Set the variable to True if registration is successful
                else:
                    error_messages = form.errors.as_json()
                    logger.warning(f"Form validation errors for {user_type}: {error_messages}")
                    raise ValidationError(form.errors)

        except IntegrityError as e:
            logger.error(f"Database integrity error during registration of {user_type}: {e}")
            raise ValidationError("A database integrity error occurred. Please try again.")
        except ValueError as e:
            logger.error(f"Value error during registration of {user_type}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during registration of {user_type}: {e}")
            raise Exception("An unexpected error occurred during registration. Please try again later.")

        if registration_successful:
            return user  # Return the User object if registration is successful
        else:
            return None



    def login_user(self, request, username, password):
        """
        Authenticates and logs in a user.

        Args:
            request: The HTTP request object.
            username (str): The username of the user.
            password (str): The password of the user.

        Returns:
            str: The authentication token for the logged-in user.

        Raises:
            ValidationError: If the authentication fails.
        """

        
        user = self.dal.get_by_field(User, username=username)

        # Check if user exists
        if not user:
            logger.warning(f"No such user exists: {username}")
            raise ValidationError("No such user exists.")

        # Check if user is inactive
        if not user.is_active:
            logger.warning(f"Inactive user tried to login: {username}")
            raise ValidationError("User inactive, please contact support to activate your account.")

        # Authenticate the user
        authenticated_user = authenticate(request, username=username, password=password)
        if authenticated_user is not None:
            login(request, authenticated_user)
            # Django's login function triggers the track_user_login signal automatically

            # Generate or retrieve the authentication token
            token, _ = Token.objects.get_or_create(user=authenticated_user)
            logger.info(f"User {username} logged in successfully")
            self.dal.create(UserActivity, user=authenticated_user, activity_type='login', ip_address=request.META.get('REMOTE_ADDR', '0.0.0.0'))

            return token.key
        else:
            if user:
                self.dal.create(UserActivity, user=user, activity_type='login_failed', ip_address=request.META.get('REMOTE_ADDR', '0.0.0.0'))
                # Log and handle failed login attempt
                logger.warning(f"Failed login attempt for username: {username}")
                alert_for_suspicious_activity(username, request)
            raise ValidationError("Invalid username or password")
        

    


    def contact_us(self, name, email, subject, message):

        """
        Handles the 'Contact Us' form submission.

        Args:
            name (str): The name of the person submitting the form.
            email (str): The email address of the person submitting the form.
            subject (str): The subject of the message.
            message (str): The content of the message.

        Raises:
            ValidationError: If the form data is invalid.
        """

        form_data = {'name': name, 'email': email, 'subject': subject, 'message': message}
        contact_form = ContactForm(data=form_data)

        if contact_form.is_valid():
            cleaned_data = contact_form.cleaned_data

            try:

                # Log attempt to send email
                logger.info(f"Attempting to send email from {cleaned_data['email']} with subject '{cleaned_data['subject']}'")

                # Send an email using the cleaned data
                send_mail(
                    subject=cleaned_data['subject'],
                    message=f"Name: {cleaned_data['name']}\nEmail: {cleaned_data['email']}\n\n{cleaned_data['message']}",
                    from_email='Rachel.for.Israel@gmail.com',  # Use your actual sender email --- should be no reply email
                    recipient_list=['Rachel.for.Israel@gmail.com'],  # Update with your actual recipient email
                    fail_silently=False,
                )
                # Log successful email sending
                logger.info("Email sent successfully , Contact form submitted successfully")
        
            except Exception as e:
                logger.error(f"Error sending contact form email: {e}")
                raise Exception("An error occurred while sending your message. Please try again later.")

        else:
            # Log and raise form validation errors
            errors = contact_form.errors.as_json()
            logger.warning(f"Contact form validation errors: {errors}")
            raise ValidationError("Invalid form data. Please correct the errors and try again.")
        





    def reset_password(self, request, email):

        """
        Initiates the password reset process for a user.

        Args:
            request: The HTTP request object, used to get the user's IP address.
            email (str): The email of the user who wants to reset their password.

        Raises:
            ValidationError: If the email does not exist or other errors occur.
        """
        
        try:
            # Check if the user exists and can request a password reset
            user = self.dal.get_by_field(User, email=email)
            if not user:
                logger.error(f"Password reset requested for non-existing email: {email}")
                raise Exception("No user associated with this email address.")

            if not can_request_password_reset(user):
                logger.error("Password reset limit reached or token already used.")
                raise Exception("Password reset limit reached. Please contact support.")

            # Use the request_password_reset function
            token = request_password_reset(user, request)

            # Encode the user's ID
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            # Construct the password reset link
            reset_link = f"https://your-frontend-domain.com{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"

            # Send the password reset email
            logger.info(f"Attempting to send password reset email to {email}")

            send_mail(
                subject='Password Reset Request',
                message=f"Please click on the link to reset your password: {reset_link}",
                from_email='Rachel.for.Israel@gmail.com',  # should be replaced with no-reply email 
                recipient_list=[email],
                fail_silently=False,
            )

          
            logger.info("Password reset email sent successfully")

        except Exception as e:
            logger.error(f"Error in reset_password method: {e}")
            raise Exception("An error occurred while processing your password reset request. Please try again later.")
