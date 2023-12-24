# Imports 


from datetime import date
from django.db import  models
from django_cryptography.fields import encrypt
from .support_models import SupportProviderRating
from django.contrib.auth.models import User, Group
from django.core.exceptions import  ValidationError
from simple_history.models import  HistoricalRecords
from django.utils.translation import  gettext_lazy  as _
from .core_models import TimestampedModel , City, Country
from django.core.validators import MinValueValidator, MaxValueValidator




#CommonUserProfile model

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
    country_of_issue = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True ,related_name='user_profiles_country_of_issue')
    languages_spoken = models.ManyToManyField('Language', blank=True)
    active_until = models.DateField(null=True, blank=True)
    address = encrypt(models.CharField(max_length=200, blank=True, null=True))
    profile_picture = models.ImageField(
            upload_to='users/',
            blank=True,
            null=True,
            default='/users/default_user.png',
            verbose_name=_("Profile Picture")
        )    
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True ,related_name='user_profiles_country')
    phone_number = models.CharField(max_length=20, blank=False, null=False)
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
    
    class Meta:
        verbose_name = _("Common User Profile")
        verbose_name_plural = _("Common Users Profiles")



def get_default_role_civilian():
    return Group.objects.get(name='Civilian')


#Civilian model

class Civilian(CommonUserProfile):

    """
    Model representing civilian users in the application.

    This model inherits from CommonUserProfile, which includes common fields and methods shared across different user types. It adds specific fields and validations related to civilians.

    Fields:
    - intentions: A many-to-many relationship to the Intentions model, allowing civilians to select multiple intentions or reasons for seeking assistance.

    Methods:
    - clean: Extends the validation logic from CommonUserProfile to include civilian-specific validations.
    """


    GENDER_CHOICES = [
        ('male', _('Male')),
        ('female', _('Female')),
    ]



    role = models.ForeignKey("auth.Group", default=get_default_role_civilian, editable=False, on_delete=models.CASCADE)
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES)
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
    


    class Meta:
        verbose_name = _("Civilian")
        verbose_name_plural = _("Civilians")
    

def get_default_role_supportprovider():
    return Group.objects.get(name='SupportProvider')


#SupportProvider model

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
    support_provider_categories = models.ManyToManyField('SupportProviderCategory', blank=False, help_text=_("Categories of support provided."))
    additional_info = models.TextField(blank=True, null=True, max_length=250, help_text=_("Additional details about the services offered."))
    kosher = models.BooleanField(default=False, help_text=_("Indicates if the provider offers Kosher services."))
    rating = models.IntegerField(
        default=0, 
        help_text=_("Average rating from 1 to 5"), 
        validators=[
            MinValueValidator(1, message=_("Rating cannot be less than 1")),
            MaxValueValidator(5, message=_("Rating cannot be more than 5"))
        ]
    )
    accessible_facilities = models.BooleanField(
        default=False, 
        help_text=_("Indicates if the provider offers facilities accessible for individuals with disabilities")
    )
    service_hours = models.CharField(
        max_length=255, 
        blank=True, 
        help_text=_("Service hours of the provider, e.g., 'Mon-Fri 9 AM to 5 PM'")
    )
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


    def update_average_rating(self):
        """
        Update the average rating for this support provider.
        """
        ratings = SupportProviderRating.objects.filter(support_provider=self)
        if ratings.exists():
            avg_rating = ratings.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = avg_rating
            self.save()

   
    def __str__(self):
        return f"{self.user.username} - SupportProvider"
    

    class Meta:
        verbose_name = _("Support Provider")
        verbose_name_plural = _("Support Providers")



def get_default_role_administrator():
    return Group.objects.get(name='Administrator')



#Administrator model
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
    
    class Meta:
        verbose_name = _("Administrator")
        verbose_name_plural = _("Administrators")





# UserPreference model 

class UserPreference(TimestampedModel):
    """
    Model for storing user-specific preferences and settings.

    Each user has a unique set of preferences which can be adjusted according to their needs.
    This model extends TimestampedModel to include creation and update timestamps.

    Fields:
    - user: A one-to-one link to the User model.
    - dark_mode: Boolean field to enable or disable dark mode.
    - notification_enabled: Boolean field to enable or disable notifications.
    - language_preference: User's preferred language.
    - email_updates: Boolean field to enable or disable email updates.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dark_mode = models.BooleanField(default=False)
    notification_enabled = models.BooleanField(default=True)
    language_preference = models.CharField(max_length=100, default='English')
    email_updates = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.user.username}'s Preferences"

    def clean(self):
        """Validate the UserPreference data."""
        super().clean()
        errors = {}

        # Add specific validations if required
        # Example: Validate language_preference if you have a predefined list of languages

        if errors:
            raise ValidationError(errors)
    
    class Meta:
        verbose_name = _("User Preference")
        verbose_name_plural = _("User Preferences")
        



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



