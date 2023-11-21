
# Imports 

from django.db import models
from django.utils import timezone
from axes.models import AccessAttempt
from datetime import date ,  timedelta
from django_cryptography.fields import encrypt
from django_countries.fields import CountryField
from django.contrib.auth.models import User, Group
from django.core.exceptions import  ValidationError
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
        Checks if the language is actively spoken by any support provider.
        It looks for profiles marked as active and associated with the "SupportProvider" group.
        """

        return Profile.objects.filter(
            languages_spoken=self,
            active=True,
            user__groups__name="SupportProvider"
        ).exists()


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
    intentions = models.ManyToManyField('Intentions', choices=INTENTION_CHOICES, related_name='intention_set')

    def __str__(self):
        return ', '.join([self.get_intentions_display() for intention in self.intentions.all()])

#SupportProviderCategory Model
class SupportProviderCategory(TimestampedModel):

    """
    Model representing categories for support providers. Categories could include
    shelter, medical assistance, food services, etc. This helps in organizing
    support providers into different services they offer.
    Fields:
    - name: The name of the category.
    """

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name




#Profile Model
class Profile(TimestampedModel):

    """
    Model representing user profiles. It includes personal information, preferences,
    and other relevant details. It is linked to Django's User model for authentication purposes.
    Fields include identification details, language proficiency, activity status, and more.
    Methods:
    - clean: Validates the profile data according to specific rules.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roles = models.ManyToManyField(Group, blank=False)
    identification_number = models.CharField(max_length=20, unique=True, blank=False, null=False, help_text=_("Enter your national identification number."))
    id_type = models.CharField(max_length=30, blank=False, null=False, help_text=_("Type of identification (e.g., 'Israeli ID', 'Passport')."))
    country_of_issue = CountryField(blank=False, null=False, default='IL',  help_text=_("Country of issue of the identification."))
    languages_spoken = models.ManyToManyField('Language', blank=True)
    active = models.BooleanField(default=False)
    active_until = models.DateField(null=True, blank=True)
    looking_to_earn = models.BooleanField(default=False)
    intentions = models.ManyToManyField('Intentions', blank=True)
    address = encrypt(models.CharField(max_length=200, blank=True, null=True))
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        default='path/to/default_image.jpg',
        verbose_name=_("Profile Picture")
    )
    country = CountryField(blank_label='(select country)', blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True, help_text=_('Enter a valid phone number'))
    terms_accepted = models.BooleanField(default=False, verbose_name=_("Terms Accepted"))



    def clean(self):
        """Validate the profile data."""
        super().clean()  # Call the base class clean method
        errors = {}

        if not self.languages_spoken.exists():
            errors['languages_spoken'] = _("At least one language must be spoken.")

        if self.active_until and self.active_until < date.today():
            errors['active_until'] = _("The active until date cannot be in the past.")

        if not self.phone_number:
            errors['phone_number'] = _("A phone number is required.")

        if 'Civilian' in self.roles.values_list('name', flat=True) and not self.intentions.exists():
            errors['intentions'] = _("At least one intention must be selected for civilians.")

        if not self.terms_accepted:
            errors['terms_accepted'] = _("You must accept the terms to create an account.")


        if errors:
            raise ValidationError(errors)


    def __str__(self):
        return f"{self.user.username} Profile"

    @property
    def full_phone_number(self):
        """
        Return the combined international phone number, consisting of the country's dialing code and the user's local phone number.
        """
        if self.phone_number:
            return self.phone_number.as_e164
        return None



#SupportProvider Model
class SupportProvider(TimestampedModel):

    """
    Model representing support providers, individuals or organizations that offer
    assistance or services. Each support provider is linked to a profile and categorized.
    Additional information about the services provided can be included.
    Fields:
    - profile: A link to the user profile of the support provider.
    - category: The category of services provided.
    - additional_info: Additional details about the services offered.
    """

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    category = models.ForeignKey(SupportProviderCategory, on_delete=models.CASCADE)
    additional_info = models.TextField(blank=True, null=True , max_length= 250)

    def __str__(self):
        return f"{self.category.name} - {self.profile.user.username}"




# Shelters Model
class Shelters(TimestampedModel):

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
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    latitude = models.FloatField()  
    longitude = models.FloatField()
    capacity = models.PositiveIntegerField()
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
    support_provider = models.OneToOneField(
        SupportProvider,
        on_delete=models.CASCADE,
        limit_choices_to={'category__name': "Shelter"},
        null=True,
        blank=True
    )

    def clean(self):
        """Validate the shelter data."""
        super().clean()  # Call the base class clean method
        errors = {}

        if self.capacity <= 0:
            errors['capacity'] = _("Capacity must be a positive number.")

        # Geolocation validation
        if self.geolocation:
            latitude, longitude = self.geolocation.y, self.geolocation.x
            if not (-90 <= latitude <= 90):
                errors['geolocation'] = _("Latitude must be between -90 and 90 degrees.")
            if not (-180 <= longitude <= 180):
                errors['geolocation'] += _(" Longitude must be between -180 and 180 degrees.")

        if self.city is None or self.country is None:
            errors['location'] = _("A shelter must be associated with a city and a country.")

        if errors:
            raise ValidationError(errors)



    def __str__(self):
        return self.name

    @property
    def phone(self):
        if self.support_provider:
            return self.support_provider.profile.phone_number
        return None

    @property
    def email(self):
        if self.support_provider:
            return self.support_provider.profile.user.email
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

    def __str__(self):
        return f"{self.user.username} - Feedback at {self.created_at}"




#FailedLoginAttempt Model
class FailedLoginAttempt(TimestampedModel):


    """
    Model tracking failed login attempts. It is used to implement security measures like
    account lockouts after a certain number of failed attempts. It utilizes the AccessAttempt
    model from the 'axes' package.
    Fields:
    - attempt: A link to the AccessAttempt model instance.
    - lockout_until: The datetime until which the account is locked.
    Methods:
    - is_locked_out: Checks if the account is currently locked out.
    - lock_out: Initiates a lockout for a set duration.
    """


    attempt = models.OneToOneField(AccessAttempt, on_delete=models.CASCADE)
    lockout_until = models.DateTimeField(null=True, blank=True)

    def is_locked_out(self):
        return self.lockout_until and timezone.now() < self.lockout_until

    def lock_out(self):
        self.lockout_until = timezone.now() + timedelta(minutes=5)
        self.save()