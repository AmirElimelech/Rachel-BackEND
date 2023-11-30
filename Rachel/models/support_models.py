# Imports 


from django.db import  models
from .user_models import SupportProvider
from .core_models import TimestampedModel
from django.core.exceptions import  ValidationError
from simple_history.models import HistoricalRecords
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator 







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
    

    class Meta:
        verbose_name = _("Intentions")
        verbose_name_plural = _("Intentions")






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
    

    class Meta:
        verbose_name = _("Support Provider Category")
        verbose_name_plural = _("Support Providers Categories")






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
        upload_to='shelters/',
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
    
    class Meta:
        verbose_name = _("Shelter")
        verbose_name_plural = _("Shelters")

