# Imports 

from datetime import date
from django.db import  models
from django.utils.translation import gettext_lazy as _
from django.core.validators import  MaxLengthValidator





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
    
    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")




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
    country = models.ForeignKey('Country', on_delete=models.CASCADE)
    population = models.BigIntegerField()

    def __str__(self):
        return f"{self.name}, {self.country.name}"
    
    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")




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
        return models.Civilian.objects.filter(languages_spoken=self, active_until__gte=date.today()).exists() or \
            models.SupportProvider.objects.filter(languages_spoken=self, active_until__gte=date.today()).exists() or \
            models.Administrator.objects.filter(languages_spoken=self, active_until__gte=date.today()).exists()

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")