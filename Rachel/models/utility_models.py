# Imports 

import random
from django.db import  models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import  ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_ipv46_address
from .core_models import  TimestampedModel ,  Country




class AddressLookup(TimestampedModel):

    """
    Model to store address lookup data retrieved from an external API (such as Nominatim).

    This model extends TimestampedModel, inheriting fields for creation, update, and deletion timestamps, 
    which helps in tracking the history of address lookups.

    Fields:
    - user: ForeignKey to the User model, linking the address lookup to a specific user.
    - query: The original query string used for the address lookup.
    - place_id: A unique identifier for the place as returned by the API.
    - latitude: Latitude coordinate of the location.
    - longitude: Longitude coordinate of the location.
    - display_name: A human-readable name representing the location.
    - boundingbox: JSON field containing the geographical bounding box of the location.

    The __str__ method returns a string representation of the model, 
    which includes the username of the user who made the query and the query itself.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    place_id = models.BigIntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    display_name = models.TextField()
    boundingbox = models.JSONField()


    def clean(self):
        """Validate the AddressLookup data."""
        super().clean()
        errors = {}

        if not self.query:
            errors['query'] = "The query string cannot be empty."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.user.username} - {self.query}"

    def save(self, *args, **kwargs):
        """Override the save method to include clean."""
        self.full_clean()
        super().save(*args, **kwargs)


    class Meta:
        verbose_name = _("Addresses Lookup")
        verbose_name_plural = _("Addresses Lookup")




class SearchHistory(TimestampedModel):
    """
    Model for tracking the search history of users.

    This model extends TimestampedModel to include creation, update, and deletion timestamps,
    which helps in tracking the history of user searches.

    Fields:
    - user: ForeignKey to the User model, linking each search query to a specific user.
    - query: The text of the search query.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)


    def __str__(self):
        return f"{self.user.username} - {self.query} - {self.created_at}"

    def clean(self):
        """Validate the SearchHistory data."""
        super().clean()
        errors = {}

        if not self.query:
            errors['query'] = "The query string cannot be empty."

        if errors:
            raise ValidationError(errors)
    class Meta:
        verbose_name = _("Search History")
        verbose_name_plural = _("Search Histories")
      

class UnauthorizedAccessAttempt(models.Model):

    """
    This model records unauthorized attempts to access user accounts.
    It stores the IP address from which the attempt was made, the timestamp of the attempt,
    and optionally the browser and operating system used for the attempt. The country field
    links to a Country model instance, providing geographical context for the attempt.

    Attributes:
    - user (ForeignKey): Reference to the User model for the account that was targeted.
    - ip_address (GenericIPAddressField): The IP address from where the attempt was made.
    - timestamp (DateTimeField): The date and time when the attempt occurred.
    - browser (CharField): The browser used for the attempt, if available.
    - operating_system (CharField): The operating system of the device used, if available.
    - country (ForeignKey): The country inferred from the IP address, linked to the Country model.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    ip_address = models.GenericIPAddressField(verbose_name=_("IP Address"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))
    browser = models.CharField(max_length=255, blank=True, verbose_name=_("Browser"))
    operating_system = models.CharField(max_length=255, blank=True, verbose_name=_("Operating System"))
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Country"))


    def __str__(self):
        return f"Unauthorized access attempt on {self.user.email} from IP: {self.ip_address}"

    def clean(self):
        """
        Perform validations on the UnauthorizedAccessAttempt model.
        """
        errors = {}

        # IP Address validation
        if not self.ip_address:
            errors['ip_address'] = _("IP Address cannot be empty.")
        else:
            try:
                validate_ipv46_address(self.ip_address)
            except ValidationError:
                errors['ip_address'] = _("Invalid IP address format.")


        # Browser field length validation
        if self.browser and len(self.browser) > 255:
            errors['browser'] = _("Browser field cannot exceed 255 characters.")

        if not self.browser:
            errors['browser'] = _("Browser information is required.")

        # Operating System field length validation
        if self.operating_system and len(self.operating_system) > 255:
            errors['operating_system'] = _("Operating System field cannot exceed 255 characters.")

        # User and Country existence check
        if not self.user_id:
            errors['user'] = _("User must be specified.")
        if self.country_id and not Country.objects.filter(id=self.country_id).exists():
            errors['country'] = _("Specified country does not exist.")

        # Raise all validation errors at once
        if errors:
            raise ValidationError(errors)
    

    class Meta:
        verbose_name = _("Unauthorized Access Attempt")
        verbose_name_plural = _("Unauthorized Access Attempts")



class ConfirmationCode(models.Model):

    """
    Model to store confirmation codes for various user actions such as password changes or account updates.
    Each code is linked to a specific user and action, and is valid for a limited time period.
    """


    ACTION_TYPES = [
        ('UpdateCivilian', 'Update Civilian'),
        ('UpdateSupportProvider', 'Update Support Provider'),
        ('DeactivateAccount', 'Deactivate Account'),
        ('UpdatePassword', 'Update Password'),
    ]


    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)


    def is_valid(self):
        """
        Check if the confirmation code is still within its validity period (5 minutes from creation).
        Returns True if valid, False otherwise.
        """
        return timezone.now() < self.created_at + timezone.timedelta(minutes=5)

    @classmethod
    def generate_code(cls, user, action_type):
        """
        Generate a unique 6-digit confirmation code for a given user and action type.
        Delete any existing codes for the same user and action type before creating a new one.
        """
        # Delete existing codes for the same user and action type
        cls.objects.filter(user=user, action_type=action_type).delete()

        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        return cls.objects.create(user=user, code=code, action_type=action_type)
    


    @classmethod
    def delete_expired_codes(cls):
        """
        Class method to delete confirmation codes that have expired.
        """
        expiration_time = timezone.now() - timezone.timedelta(minutes=5)
        cls.objects.filter(created_at__lt=expiration_time).delete()



    def clean(self):
        """
        Perform validations on the ConfirmationCode model.
        """
        errors = {}

        # User existence check
        if not self.user_id:
            errors['user'] = _("User must be specified.")

        # Code format and length validation
        if not self.code.isdigit() or len(self.code) != 6:
            errors['code'] = _("Code must be a 6-digit number.")

        # Action type validation
        valid_action_types = [choice[0] for choice in self.ACTION_TYPES]
        if self.action_type not in valid_action_types:
            errors['action_type'] = _("Invalid action type.")

        # Raise all validation errors at once
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """
        Override the save method to include the custom clean method for additional validations.
        """
        self.full_clean()
        return super(ConfirmationCode, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Confirmation Code")
        verbose_name_plural = _("Confirmation Codes")


class PasswordResetRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    token_used = models.BooleanField(default=False)  # Indicates if the reset token has been used
    request_count = models.IntegerField(default=0)   # Tracks the number of reset requests


    def __str__(self):
        return f"Password Reset Request for {self.user.username} at {self.timestamp}"

    def increment_request_count(self):
        """Increment the request count and save the model."""
        self.request_count += 1
        self.save()

    class Meta:
        verbose_name = _("Password Reset Request")
        verbose_name_plural = _("Password Reset Requests")