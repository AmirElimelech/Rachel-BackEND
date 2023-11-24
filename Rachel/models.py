
# Imports 

import datetime
from datetime import date 
from django.db import  models
from django_cryptography.fields import encrypt
from django_countries.fields import CountryField
from django.contrib.auth.models import User, Group
from django.core.exceptions import  ValidationError
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import FileExtensionValidator , MaxLengthValidator





#Models 


#TimestampedModel
class TimestampedModel(models.Model):

    """
    An abstract base model that provides timestamp fields for creation, update, and deletion.
    This model can be inherited by other models to avoid redundancy in defining these common fields.
    Fields:
    - created_at: The datetime when the record was created.
    - updated_at: The datetime when the record was last updated.
    - deleted_at: The datetime when the record was soft deleted, if applicable.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        abstract = True




# Country Model
class Country(TimestampedModel):

    """
    Basic model representing countries. It includes the country's name, its ISO code, and the phone code.
    This model can be used for storing information related to countries, such as in address details.
    Fields:
    - name: The name of the country.
    - region: The geographical or political region of the country.
    - iso3: A unique 3-letter ISO code for the country.
    - phone_code: The international phone code for the country.
    """


    name = models.CharField(max_length=100, unique=True)
    region = models.CharField(max_length=50, blank=False, null=False)
    iso3 = models.CharField(max_length=3, unique=True)
    phone_code = models.CharField(max_length=10)

    def __str__(self):
        return self.name




# City Model
class City(TimestampedModel):

    """
    Model representing cities. Each city is linked to a Country and includes population data.
    Useful for location-based information and services.
    Fields:
    - name: The name of the city.
    - country: A reference to the Country model, indicating which country the city belongs to.
    - population: The population count of the city.
    """
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    population = models.BigIntegerField()

    def __str__(self):
        return f"{self.name}, {self.country.name}"

#Intentions Model
class Intentions(models.Model):

    """
    Model representing various intentions or reasons for seeking assistance.
    Examples include seeking shelter, job opportunities, medical assistance, etc.
    This model allows users to select multiple intentions from predefined choices.
    Fields:
    - intentions: A ManyToManyField to associate multiple intentions using predefined choices.
    """

    INTENTION_CHOICES = [
        ('shelter', _('Seeking Shelter')),
        ('job', _('Looking for Job Opportunities')),
        ('medical', _('Medical Assistance')),
        ('education', _('Educational Support')),
        ('food', _('Food and Nutrition')),
        ('legal_aid', _('Legal Aid')),
        ('emotional_support', _('Emotional Support')),
        ('transportation', _('Transportation Assistance')),
        ('financial_help', _('Financial Help')),
        ('community_engagement', _('Community Engagement')),
        ('language_learning', _('Language Learning Support')),
        ('technology', _('Technology Assistance')),
        ('childcare', _('Childcare Services')),
        ('elderly_care', _('Elderly Care')),
        ('mental_health', _('Mental Health Support')),
        ('environmental_activism', _('Environmental Activism')),
        ('artistic_expression', _('Artistic Expression')),
        ('sports_recreation', _('Sports and Recreation')),
        ('volunteer_opportunities', _('Volunteer Opportunities')),
        ('skill_development', _('Skill Development')),
        # i can add more here if needed 
    ]

    # Use a ManyToManyField with choices
    name = models.CharField(max_length=100, choices=INTENTION_CHOICES, unique=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.get_name_display()

#SupportProviderCategory Model
class SupportProviderCategory(TimestampedModel):
    """
    Model representing predefined categories for support providers, such as shelter, medical assistance, etc.
    This helps in organizing support providers into different services they offer.
    """

    CATEGORY_CHOICES = [
        ('Shelter and Housing', _('Shelter and Housing')),
        ('Medical Assistance', _('Medical Assistance')),
        ('Food Services', _('Food Services')),
        ('Legal Aid', _('Legal Aid')),
        ('Mental Health Support', _('Mental Health Support')),
        ('Employment Assistance', _('Employment Assistance')),
        ('Educational Support', _('Educational Support')),
        ('Child Care Services', _('Child Care Services')),
        ('Senior Care Services', _('Senior Care Services')),
        ('Disability Support', _('Disability Support')),
        ('Substance Abuse Treatment', _('Substance Abuse Treatment')),
        ('Emergency Response', _('Emergency Response')),
        ('Financial Counseling', _('Financial Counseling')),
        ('Refugee Assistance', _('Refugee Assistance')),
        ('Veteran Services', _('Veteran Services')),
        ('Domestic Violence Support', _('Domestic Violence Support')),
        ('Transportation Services', _('Transportation Services')),
        ('Cultural Integration', _('Cultural Integration')),
        ('Community Outreach', _('Community Outreach')),
        ('Environmental Sustainability', _('Environmental Sustainability')),
        ('Youth Programs', _('Youth Programs')),
        ('Elderly Support', _('Elderly Support')),
        ('Rehabilitation Services', _('Rehabilitation Services')),


    ]

    name = models.CharField(max_length=100, choices=CATEGORY_CHOICES, unique=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.name


class CommonUserProfile(TimestampedModel):

    """
    An abstract base class that serves as a common foundation for different user profiles.

    This class inherits from TimestampedModel to include creation, update, and deletion timestamps. It centralizes common fields and methods used across various user types in the application, such as Civilians, Support Providers, and Administrators.

    Fields:
    - user: A one-to-one relationship with Django's User model for authentication and identification.
    - identification_number: A unique identifier for the user (e.g., national ID or passport number).
    - id_type: The type of identification document.
    - country_of_issue: The country issuing the identification.
    - languages_spoken: A many-to-many relationship to track languages spoken by the user.
    - active_until: A date field to specify until when the profile is considered active.
    - address: Encrypted field for storing user's address.
    - profile_picture: Field for uploading a profile picture.
    - city: Foreign key to the City model, representing the user's city.
    - country: Country field to represent the user's country.
    - phone_number: Field for storing a valid phone number.
    - terms_accepted: Boolean field to indicate whether the user has accepted terms and conditions.

    Methods:
    - clean: Validates the user profile data, ensuring all necessary fields are properly set.
    - full_phone_number: Property that returns the user's complete phone number in international format.
    """

    ID_TYPE_CHOICES = [
    ('israeli_id', _('Israeli ID')),
    ('passport', _('Passport')),
    ('other', _('Other Identification')),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    identification_number = models.CharField(max_length=20, unique=True, blank=False, null=False, help_text=_("Enter your national identification number."))
    id_type = models.CharField(max_length=30, choices=ID_TYPE_CHOICES, blank=False, null=False, help_text=_("Type of identification (e.g., 'Israeli ID', 'Passport')."))
    country_of_issue = CountryField(blank=False, null=False, default='IL',  help_text=_("Country of issue of the identification."))
    languages_spoken = models.ManyToManyField('Language', blank=True)
    active_until = models.DateField(null=True, blank=True)
    address = encrypt(models.CharField(max_length=200, blank=True, null=True))
    profile_picture = models.ImageField(
            upload_to='profile_pictures/',
            blank=True,
            null=True,
            default='path/to/default_image.jpg',
            verbose_name=_("Profile Picture")
        )    
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    country = CountryField(blank_label='(select country)', blank=True)
    phone_number = PhoneNumberField(blank=True, null=True)
    terms_accepted = models.BooleanField(default=False, verbose_name=_("Terms Accepted"))

    class Meta:
        abstract = True

    def clean(self):
        """Validate the common user profile data."""
        super().clean()
        errors = {}

        if not self.languages_spoken.exists():
            errors['languages_spoken'] = _("At least one language must be spoken.")

        if self.active_until and self.active_until < date.today():
            errors['active_until'] = _("The active until date cannot be in the past.")

        if not self.phone_number:
            errors['phone_number'] = _("A phone number is required.")

        if not self.terms_accepted:
            errors['terms_accepted'] = _("You must accept the terms to create an account.")

        if errors:
            raise ValidationError(errors)
        

    def __str__(self):
        return f"{self.user.username} Profile"
    

    @property
    def full_phone_number(self):
        """Return the combined international phone number."""
        if self.phone_number:
            return self.phone_number.as_e164
        return None



def get_default_role_civilian():
    return Group.objects.get(name='Civilian')

class Civilian(CommonUserProfile):
    """
    Model representing civilian users in the application.

    This model inherits from CommonUserProfile, which includes common fields and methods shared across different user types. It adds specific fields and validations related to civilians.

    Fields:
    - intentions: A many-to-many relationship to the Intentions model, allowing civilians to select multiple intentions or reasons for seeking assistance.

    Methods:
    - clean: Extends the validation logic from CommonUserProfile to include civilian-specific validations.
    """
    role = models.ForeignKey("auth.Group", default=get_default_role_civilian, editable=False, on_delete=models.CASCADE)
    intentions = models.ManyToManyField('Intentions', blank=True)
    history = HistoricalRecords()

    def clean(self):
        """Add specific validations for Civilian."""
        super().clean()  # Calls the clean method of CommonUserProfile
        errors = {}

        # Add Civilian-specific validations
        if not self.intentions.exists():
            errors['intentions'] = _("At least one intention must be selected for civilians.")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.user.username} - Civilian"
    

def get_default_role_supportprovider():
    return Group.objects.get(name='SupportProvider')

class SupportProvider(CommonUserProfile):

    """
    Model representing a support provider user.

    Inherits common fields and methods from CommonUserProfile and adds specific fields related to the support provider role.
    
    Fields:
    - looking_to_earn: Boolean field indicating whether the support provider is looking to earn through their services.
    - support_provider_categories: ManyToMany relationship to track categories of support provided by the user.
    - additional_info: Text field for storing additional information about the support services offered.

    Inherits all validations and the full_phone_number method from CommonUserProfile.
    """

    role = models.ForeignKey("auth.Group", default=get_default_role_supportprovider, editable=False, on_delete=models.CASCADE)
    looking_to_earn = models.BooleanField(default=False, help_text=_("Indicates if the user is looking to earn through their services."))
    support_provider_categories = models.ManyToManyField('SupportProviderCategory', blank=True, help_text=_("Categories of support provided."))
    additional_info = models.TextField(blank=True, null=True, max_length=250, help_text=_("Additional details about the services offered."))
    history = HistoricalRecords()

    def clean(self):
        """Add specific validations for SupportProvider."""
        super().clean()  # This calls the clean method of CommonUserProfile
        errors = {}

        # Add SupportProvider-specific validations
        if not self.support_provider_categories.exists():
            errors['support_provider_categories'] = _("At least one category must be selected for support providers.")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.user.username} - SupportProvider"



def get_default_role_administrator():
    return Group.objects.get(name='Administrator')

class Administrator(CommonUserProfile):

    """
    Model representing an administrator user.

    Inherits common fields and methods from CommonUserProfile. This model is tailored for users who manage and oversee the application, typically with higher-level access and control.

    Fields specific to the Administrator role can be added as needed. Currently, it includes only the common fields from CommonUserProfile.

    Inherits all validations and the full_phone_number method from CommonUserProfile.

    Fields:
    department: Administrator's department or area of responsibility, chosen from predefined choices.

    """

    DEPARTMENT_CHOICES = [
        ('HR', _('Human Resources')),
        ('IT', _('Information Technology')),
        ('FIN', _('Finance')),
        ('MKT', _('Marketing')),
        ('OPS', _('Operations')),
        # Add more departments as needed
    ]

    role = models.ForeignKey("auth.Group", default=get_default_role_administrator, editable=False, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, blank=False)
    history = HistoricalRecords()

    def clean(self):
        """Add specific validations for Administrator."""
        super().clean()  # This calls the clean method of CommonUserProfile
        # Add Administrator-specific validations here if necessary
        errors = {}

         # Validation to ensure department is not empty
        if not self.department:
            errors['department'] = _("Department cannot be empty for an Administrator.")

        if errors:
            raise ValidationError(errors)


    def __str__(self):
        return f"{self.user.username} - Administrator"





# Language Model
class Language(TimestampedModel):
    """
    Model representing a language. It includes the language name and a unique language code.
    This model can be used to track different languages spoken by users or supported by the application.
    Fields:
    - name: The name of the language.
    - lang_code: A unique 3-letter code representing the language.
    """

    name = models.CharField(max_length=100, unique=True)
    lang_code = models.CharField(
        max_length=3,
        unique=True,
        validators=[MaxLengthValidator(limit_value=3)]
    )
    def __str__(self):
        return self.name

    @property
    def is_active(self):
        """
        Checks if the language is actively spoken by any active user in the system.
        """
        return Civilian.objects.filter(languages_spoken=self, active_until__gte=date.today()).exists() or \
               SupportProvider.objects.filter(languages_spoken=self, active_until__gte=date.today()).exists() or \
               Administrator.objects.filter(languages_spoken=self, active_until__gte=date.today()).exists()




# Shelters Model
class Shelter(TimestampedModel):

    """
    Model representing shelters. Includes details like location, capacity, and related images.
    Shelters can be optionally linked to a SupportProvider for additional contact and service information.
    Fields:
    - name, address, city, country: Location details of the shelter.
    - geolocation: Geographical coordinates of the shelter.
    - capacity: The number of individuals the shelter can accommodate.
    - picture: Images of the shelter.
    - support_provider: Link to a support provider if applicable.
    Methods:
    - clean: Validates shelter data, ensuring all necessary information is accurate and complete.
    """


    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    city = models.ForeignKey('City', on_delete=models.CASCADE)
    country = models.ForeignKey('Country', on_delete=models.CASCADE)
    latitude = models.FloatField()  
    longitude = models.FloatField()
    capacity = models.PositiveIntegerField()
    history = HistoricalRecords()
    picture = models.ImageField(
        upload_to='shelter_pictures/',
        validators=[
            FileExtensionValidator(allowed_extensions=[
                'jpg', 'jpeg', 'jfif', 'pjpeg', 'pjp',
                'png', 'gif', 'webp', 'tif', 'tiff', 'bmp', 'dib',
                'ico', 'svg', 'heif', 'heifs', 'heic', 'heics'
            ]),
        ]
    )
    support_provider = models.ForeignKey(SupportProvider,on_delete=models.CASCADE,
    limit_choices_to={'support_provider_categories__name': "Shelter and Housing"},
    null=True,
    blank=True
)

    def clean(self):

        """Validate the shelter data."""
        super().clean()  # Call the base class clean method
        errors = {}

        if self.capacity <= 0:
            errors['capacity'] = _("Capacity must be a positive number.")

        # Latitude and Longitude validation
        if self.latitude is not None and not -90 <= self.latitude <= 90:
            errors['latitude'] = _("Latitude must be between -90 and 90 degrees.")

        if self.longitude is not None and not -180 <= self.longitude <= 180:
            errors['longitude'] = _("Longitude must be between -180 and 180 degrees.")

        if self.city is None or self.country is None:
            errors['location'] = _("A shelter must be associated with a city and a country.")

        if errors:
            raise ValidationError(errors)



    def __str__(self):
        return self.name

    @property
    def phone(self):
        if self.support_provider:
            return self.support_provider.phone_number
        return None

    @property
    def email(self):
        if self.support_provider:
            return self.support_provider.user.email
        return None




#UserActivity Model

class UserActivity(TimestampedModel):

    """
    Model for tracking various user activities, such as logins and logouts.
    It includes user identification, the type of activity, and the timestamp of the activity.
    Fields:
    - user: Reference to the User model for identifying the user.
    - activity_type: Type of activity performed (e.g., 'login', 'logout').
    - ip_address: IP address from which the activity was performed.
    - timestamp: The datetime when the activity occurred.
    """
    ACTIVITY_CHOICES = [
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('password_change', _('Password Change')),
        ('profile_update', _('Profile Update')),
        ('failed_login', _('Failed Login Attempt')),
        ('account_creation', _('Account Creation')),
        ('account_deletion', _('Account Deletion')),
        ('password_reset_request', _('Password Reset Request')),
        ('tos_acceptance', _('Terms of Service Acceptance')),
        ('session_timeout', _('Session Timeout')),
        ('file_upload', _('File Upload')),
        ('file_download', _('File Download')),
        ('api_access', _('API Access')),
        ('user_feedback', _('User Feedback Submission')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    ip_address = models.GenericIPAddressField()  # To store the IP address
    timestamp = models.DateTimeField(auto_now_add=True)  # Records the time of activity

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp}"
    


#UserFeedback Model
class UserFeedback(TimestampedModel):
    """
    Model for storing user feedback.
    Fields:
    - user: Reference to the User model for identifying the user giving feedback.
    - feedback_text: The actual feedback provided by the user.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback_text = models.TextField()
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.username} - Feedback at {self.created_at}"



class FeedbackResponse(models.Model):
    """
    A model representing responses to user feedback. This model includes validations to ensure that:
    - Only administrators can respond.
    - Responses are not empty and adhere to a maximum length.
    - Feedback being responded to exists and is not too old.
    - Each piece of feedback receives only one response.
    """
    feedback = models.ForeignKey(UserFeedback, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"Response to {self.feedback.user.username}'s feedback"

    def clean(self):
        """Perform validations on the FeedbackResponse model, aggregating all errors."""

        errors = {}
        min_length = 5

        # Check if the responder is part of the 'Administrator' group
        if not self.responder.groups.filter(name='Administrator').exists():
            errors['responder'] = "Only administrators can respond to feedback."

        # Validation for empty or too short response text
        response_text_length = len(self.response_text.strip())
        if response_text_length == 0:
            errors['response_text'] = "Response text cannot be empty."
        elif response_text_length < min_length:
            errors['response_text'] = f"Response text must be at least {min_length} characters long."

        # Validation for response text length
        max_length = 1000  # Example: 1000 characters
        if len(self.response_text) > max_length:
            errors['response_text'] = f"Response text cannot exceed {max_length} characters."

        # Validation for feedback existence
        if not self.feedback:
            errors['feedback'] = "The feedback being responded to must exist."

        # Validation to prevent duplicate responses to the same feedback
        if FeedbackResponse.objects.filter(feedback=self.feedback).exclude(pk=self.pk).exists():
            errors['feedback'] = "This feedback has already been responded to."

        # Validation for response timing (e.g., not allowing responses to feedback older than 30 days)
        feedback_age_limit = 30  # days
        if self.feedback.created_at < datetime.date.today() - datetime.timedelta(days=feedback_age_limit):
            errors['feedback'] = "Cannot respond to feedback older than 30 days."

        # Raise all validation errors at once
        if errors:
            raise ValidationError(errors)
        





class Notification(TimestampedModel):
    """
    Model for handling notifications for users. Notifications can be of various types like alerts, reminders, or informational messages.
    Fields:
    - recipient: Reference to the User model indicating who will receive the notification.
    - title: A brief title for the notification.
    - message: The content of the notification.
    - read: Boolean field indicating whether the notification has been read.
    - notification_type: The type of notification (e.g., 'alert', 'reminder', 'info').
    - created_at: Timestamp for when the notification was created.
    - updated_at: Timestamp for when the notification was last updated.
    """
    NOTIFICATION_TYPES = [
        ('alert', _('Alert')),
        ('reminder', _('Reminder')),
        ('info', _('Information')),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    history = HistoricalRecords()


    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
