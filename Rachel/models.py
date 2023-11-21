
from django.contrib.gis.db import models as geomodels
from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import RegexValidator, FileExtensionValidator , MaxLengthValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date , timedelta
from django.utils import timezone
from axes.models import AccessAttempt
from fernet_fields import EncryptedCharField
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField





class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)


    class Meta:
        abstract = True



# Language Model
class Language(TimestampedModel):
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




class Intentions(models.Model):
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
    intentions = models.ManyToManyField('Intentions', choices=INTENTION_CHOICES)

    def __str__(self):
        return ', '.join([self.get_intentions_display() for intention in self.intentions.all()])





class Profile(TimestampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Group, on_delete=models.CASCADE)
    ID = models.CharField(max_length=9, unique=True)
    languages_spoken = models.ManyToManyField('Language', blank=True)
    active = models.BooleanField(default=True)
    active_until = models.DateField(null=True, blank=True)
    looking_to_earn = models.BooleanField(default=False)
    intentions = models.ManyToManyField('Intentions', blank=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        default='path/to/default_image.jpg',
        verbose_name=_("Profile Picture")
    )
    country = CountryField(blank_label='(select country)', blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True, help_text=_('Enter a valid phone number'))

    def clean(self):
        """Validate the profile data."""
        super().clean()  # Call the base class clean method
        errors = {}

        if self.role.name == "SupportProvider" and not self.languages_spoken.exists():
            errors['languages_spoken'] = _("A support provider must have at least one language spoken.")

        if self.active_until and self.active_until < date.today():
            errors['active_until'] = _("The active until date cannot be in the past.")

        if not self.phone_number:
            errors['phone_number'] = _("A phone number is required.")

        if self.role.name == "Civilian" and not self.intentions.exists():
            errors['intentions'] = _("At least one intention must be selected for civilians.")

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

class SupportProviderCategory(TimestampedModel):

    """
    Defines categories for support providers: shelter, medical assistance, resturant , Taxi station , school  etc...
    """

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name





class SupportProvider(TimestampedModel):

    """
    Represents support providers, linked to a Profile and categorized by SupportProviderCategory.
    Additional info can be provided in a text field.
    """

    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    category = models.ForeignKey(SupportProviderCategory, on_delete=models.CASCADE)
    additional_info = models.TextField(blank=True, null=True , max_length= 250)

    def __str__(self):
        return f"{self.category.name} - {self.profile.user.username}"




# Shelters Model
class Shelters(TimestampedModel):

    """
    Represents shelters with address, geolocation, capacity, and related images.
    Each shelter is optionally linked to a SupportProvider.
    The clean method ensures valid data for capacity and geolocation.
    Includes properties for phone and email derived from the linked support provider.
    """


    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    geolocation = geomodels.PointField()
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

        if not self.geolocation:
            errors['geolocation'] = _("A shelter must have a valid geolocation.")

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




# Country Model
class Country(TimestampedModel):

    """
    Basic model for countries, including name, ISO code, and phone code.
    """


    name = models.CharField(max_length=100)
    iso3 = models.CharField(max_length=3, unique=True)
    phone_code = models.CharField(max_length=10)

    def __str__(self):
        return self.name




# City Model
class City(TimestampedModel):
    """
    Represents cities, each linked to a Country and includes a population field.
    """
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    population = models.BigIntegerField()

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class UserActivity(TimestampedModel):

    """
    Tracks user activities like login, logout, etc., along with the user's IP address and timestamp of the activity.
    """


    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=10)  # e.g., 'login', 'logout'
    ip_address = models.GenericIPAddressField()  # To store the IP address
    timestamp = models.DateTimeField(auto_now_add=True)  # Records the time of activity

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp}"
    


class FailedLoginAttempt(TimestampedModel):


    """
    Tracks failed login attempts and implements a lockout mechanism.
    Uses the AccessAttempt model from the `axes` package.
    Includes methods to check if an account is locked out and to initiate a lockout.
    """


    attempt = models.OneToOneField(AccessAttempt, on_delete=models.CASCADE)
    lockout_until = models.DateTimeField(null=True, blank=True)

    def is_locked_out(self):
        return self.lockout_until and timezone.now() < self.lockout_until

    def lock_out(self):
        self.lockout_until = timezone.now() + timedelta(minutes=5)
        self.save()