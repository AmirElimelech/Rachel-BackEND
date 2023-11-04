
from django.contrib.gis.db import models as geomodels
from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import RegexValidator, FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date , timedelta
from django.utils import timezone






# Language Model
class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        """Check if the language is actively spoken by any support provider."""
        return Profile.objects.filter(
            languages_spoken=self,
            active=True,
            user__groups__name="SupportProvider"
        ).exists()
    
class Intentions(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# Profile Model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Group, on_delete=models.CASCADE)
    ID = models.CharField(max_length=9, unique=True)
    languages_spoken = models.ManyToManyField(Language, blank=True)
    active = models.BooleanField(default=True)
    active_until = models.DateField(null=True, blank=True)
    looking_to_earn = models.BooleanField(default=False)
    intentions = models.ManyToManyField(Intentions)
    address = models.CharField(max_length=200, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        verbose_name=_("Profile Picture")
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Enter a valid international mobile phone number starting with '+' and containing 9 to 15 digits.")
    )
    phone = models.CharField(validators=[phone_regex], max_length=15)

    def clean(self):
        """Validate the profile data."""
        super().clean()  # Call the base class clean method
        if self.role.name == "SupportProvider":
            if not self.languages_spoken.exists():
                raise ValidationError(_("A support provider must have at least one language spoken."))
        if self.active_until and self.active_until < date.today():
            raise ValidationError(_("The active until date cannot be in the past."))
        if not self.phone:
            raise ValidationError(_("A phone number is required."))
        
        if self.role.name == "Civilian" and not self.intentions.exists():
            raise ValidationError(_("At least one intention must be selected for civilians."))


    def __str__(self):
        return f"{self.user.username} Profile"




class SupportProviderCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name





class SupportProvider(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    category = models.ForeignKey(SupportProviderCategory, on_delete=models.CASCADE)
    additional_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.category.name} - {self.profile.user.username}"




# Shelters Model
class Shelters(models.Model):
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
        if self.capacity <= 0:
            raise ValidationError(_("Capacity must be a positive number."))
        if not self.geolocation:
            raise ValidationError(_("A shelter must have a valid geolocation."))
        if self.city is None or self.country is None:
            raise ValidationError(_("A shelter must be associated with a city and a country."))

    def __str__(self):
        return self.name

    @property
    def phone(self):
        if self.support_provider:
            return self.support_provider.profile.phone
        return None

    @property
    def email(self):
        if self.support_provider:
            return self.support_provider.profile.user.email
        return None




# Country Model
class Country(models.Model):
    name = models.CharField(max_length=100)
    phone_code = models.CharField(max_length=10)

    def __str__(self):
        return self.name




# City Model
class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=10)  # e.g., 'login', 'logout'
    ip_address = models.GenericIPAddressField()  # To store the IP address
    timestamp = models.DateTimeField(auto_now_add=True)  # Records the time of activity

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp}"
    


class FailedLoginAttempt(models.Model):
    username = models.CharField(max_length=150, unique=True)
    attempts = models.IntegerField(default=0)
    last_attempt_time = models.DateTimeField(auto_now=True)
    lockout_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Failed attempts for {self.username}: {self.attempts}"

    def is_locked_out(self):
        return self.lockout_until and timezone.now() < self.lockout_until

    def lock_out(self):
        self.lockout_until = timezone.now() + timedelta(minutes=5)
        self.save()