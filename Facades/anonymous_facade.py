

import logging
from Rachel.DAL import DAL
from django.urls import reverse
from django.db import transaction
from django.core.mail import send_mail
from django.contrib.auth.models import User 
from django.utils.encoding import force_bytes
from Forms.miscellaneous_forms import ContactForm
from rest_framework.authtoken.models import  Token
from django.core.exceptions import  ValidationError
from django.utils.http import  urlsafe_base64_encode
from django.contrib.auth import  authenticate, login
from django.utils.translation import gettext_lazy as  _
from django.contrib.auth.tokens import default_token_generator
from Rachel.utils import alert_for_suspicious_activity , request_password_reset , can_request_password_reset
from Rachel.models import City , Country , Language , SupportProvider , Civilian , Intentions , SupportProviderCategory 







logger = logging.getLogger(__name__)



class AnonymousFacade:

    def __init__(self):


        self.dal = DAL()


    
    def register_user(self, user_type, username, email, password, identification_number, id_type, country_of_issue_id, languages_spoken_ids, city_id, country_id, phone_number, terms_accepted, profile_picture, address, gender=None, support_provider_categories_ids=None, looking_to_earn=None, **extra_fields):
        logger.info("Processing user registration request")

        errors = {}
        user = None

        logger.info("Validating registration request")

        try:
            with transaction.atomic(): 

        
                if not terms_accepted:
                    logger.error(f"terms are not accepted yet.")
                    errors['terms_accepted'] = _("You must accept the terms and conditions to register.")

                if self.dal.get_by_field(User, username=username):
                    logger.error(f"Username {username} already exists.")
                    errors['username'] = _("A user with this username already exists.")

                if self.dal.get_by_field(User, email=email):
                    logger.error(f"Email {email} already exists.")
                    errors['email'] = _("A user with this email already exists.")

                if self.dal.filter(User, phone_number=phone_number).exists():
                    logger.error(f"Phone number {phone_number} already exists.")
                    errors['phone_number'] = _("A user with this phone number already exists.")

                identification_filter_kwargs = {
                    'identification_number': identification_number, 
                    'country_of_issue_id': country_of_issue_id, 
                    'id_type': id_type
                }
                if self.dal.filter(Civilian, **identification_filter_kwargs).exists() or \
                   self.dal.filter(SupportProvider, **identification_filter_kwargs).exists():
                    errors['identification_number'] = _("A user with this ID number, country of issue, and ID type already exists.")

                if errors:
                    logger.info("Erros List")
                    raise ValidationError(errors)

                user_data = {
                    'username': username,
                    'email': email,
                    'password': password,
                    **extra_fields
                }

                logger.info(f"User info approved, registering user {username}!")
                user = self.dal.create(User, **user_data)
                logger.info(f"User {username} registered successfully")


        
        

                country_of_issue = self.dal.get_by_id(Country, country_of_issue_id)
                city = self.dal.get_by_id(City, city_id)
                country = self.dal.get_by_id(Country, country_id)
                languages_spoken = self.dal.filter(Language, id__in=languages_spoken_ids)

                if not all([country_of_issue, city, country]):
                    logger.error("Invalid country, city, or language information.")
                    raise ValidationError("Invalid country, city, or language information.")

                common_fields = {
                    'user': user,
                    'identification_number': identification_number,
                    'id_type': id_type,
                    'country_of_issue': country_of_issue,
                    'city': city,
                    'country': country,
                    'phone_number': phone_number,
                    'terms_accepted': terms_accepted,
                    'profile_picture': profile_picture,
                    'address': address,
                    'languages_spoken': languages_spoken,
                }

                if user_type == 'civilian':
                    civilian_data = {**common_fields, 'gender': gender}
                    logger.info("Creating civilian profile")
                    civilian = self.dal.create(Civilian, **civilian_data)

                    if 'intentions_ids' in extra_fields:
                        intentions = self.dal.filter(Intentions, id__in=extra_fields['intentions_ids'])
                        civilian.intentions.set(intentions)
                        logger.info(f"Set intentions for civilian user {username}")

                    logger.info(f"Civilian user {username} created successfully")


                elif user_type == 'support_provider':
                    support_provider_data = {**common_fields, 'looking_to_earn': looking_to_earn}
                    logger.info("Creating support provider profile")
                    support_provider = self.dal.create(SupportProvider, **support_provider_data)

                    if support_provider_categories_ids:
                        categories = self.dal.filter(SupportProviderCategory, id__in=support_provider_categories_ids)
                        support_provider.support_provider_categories.set(categories)
                        logger.info(f"Set categories for support provider user {username}")

                    logger.info(f"Support provider user {username} created successfully")


                else:
                    errors['user_type'] = _("Invalid user type provided. Expected 'civilian' or 'support_provider'.")
                    logger.error(f"Invalid user type provided: {user_type}")
                    raise ValidationError(errors)

        except ValidationError as e:
            logger.warning(f"Validation error during registration: {e}")
            raise e  # Rethrow to be handled by the caller

        except Exception as e:
            logger.error(f"Unexpected error during registration: {e}", exc_info=True)
            raise Exception("An unexpected error occurred during registration. Please try again later.")

        return user if user_type in ['civilian', 'support_provider'] else None






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
            return token.key
        else:
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
        





    def reset_password(self, email):
        """
        Initiates the password reset process for a user.

        Args:
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
            token = request_password_reset(user)

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
