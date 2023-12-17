import logging
from django import forms
from Rachel.DAL import DAL
from django.utils import timezone
from django.forms import DateField
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation  import gettext_lazy as  _
from Rachel.utils import clean_phone_number , validate_image
from django.core.validators import MinValueValidator, MaxValueValidator
from Rachel.models import SupportProvider, Language, SupportProviderCategory, Group, City, Country



logger = logging.getLogger(__name__)




class SupportProviderRegisterForm(UserCreationForm):
    """
    Form for registering a new Support Provider. This form extends the UserCreationForm
    and includes additional fields specific to the SupportProvider model.
    """

    identification_number = forms.CharField(max_length=20, required=True)
    id_type = forms.ChoiceField(choices=SupportProvider.ID_TYPE_CHOICES, required=True)
    country_of_issue = forms.ModelChoiceField(queryset=Country.objects.all(), required=True)
    languages_spoken = forms.ModelMultipleChoiceField(queryset=Language.objects.all(), required=True , error_messages={'required': "At least one language must be chosen."})
    city = forms.ModelChoiceField(queryset=City.objects.all(), required=True)
    country = forms.ModelChoiceField(queryset=Country.objects.all(), required=True)
    phone_number = forms.CharField(required=True)
    terms_accepted = forms.BooleanField(required=True, error_messages={'required': "You must accept the terms to create an account."})
    support_provider_categories = forms.ModelMultipleChoiceField(queryset=SupportProviderCategory.objects.all(), required=True)
    additional_info = forms.CharField(widget=forms.Textarea, required=False)
    address = forms.CharField(max_length=200, required=True)
    looking_to_earn = forms.BooleanField(required=True)
    active_until = DateField(required=True, error_messages={'required': "A date must be set."})
    profile_picture = forms.ImageField(required=False, error_messages={'required': "A picture must be set to the profile"})
    kosher = forms.BooleanField(required=False, label=_("Offers Kosher Services"))
    rating = forms.IntegerField(required=False,
        initial=0,
        validators=[
            MinValueValidator(1, message=_("Rating cannot be less than 1")),
            MaxValueValidator(5, message=_("Rating cannot be more than 5"))
        ]
    )
    accessible_facilities = forms.BooleanField(required=False)
    service_hours = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User 
        fields = [
            'username', 'email', 'password1', 'password2', 'identification_number', 'id_type', 
            'country_of_issue', 'languages_spoken', 'city', 'country', 'phone_number',
            'terms_accepted', 'support_provider_categories', 'additional_info', 'address', 'looking_to_earn',
            'kosher', 'accessible_facilities', 'service_hours'
        ]


    def __init__(self, *args, **kwargs):
        super(SupportProviderRegisterForm, self).__init__(*args, **kwargs)
        self.dal = DAL()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existing_user = self.dal.filter(User, email=email).first()
        if existing_user and existing_user.username != self.cleaned_data.get('username'):
            raise forms.ValidationError("A user with that email already exists.", code='unique')
        return email

    def clean_phone_number(self):
        country = self.cleaned_data.get('country_of_issue')
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Phone number is required.")

        if country is None:
            raise forms.ValidationError("Country of issue is required to validate the phone number.")

        cleaned_phone_number = clean_phone_number(country.id, phone_number)

        # Check if phone number already exists for a different user
        existing_support_provider = self.dal.filter(SupportProvider, phone_number=cleaned_phone_number).exclude(user=self.instance).first()
        if existing_support_provider:
            raise forms.ValidationError("A user with that phone number already exists.", code='unique')

        return cleaned_phone_number
    
    def clean_identification_number(self):
        identification_number = self.cleaned_data.get('identification_number')
        existing_provider = self.dal.filter(SupportProvider, identification_number=identification_number).exclude(user=self.instance).first()
        if existing_provider:
            raise forms.ValidationError("A user with that identification number already exists.", code='unique')
        return identification_number

    def clean_support_provider_categories(self):
        categories = self.cleaned_data.get('support_provider_categories')
        if not categories:
            raise forms.ValidationError("At least one category must be selected.", code='required')
        return categories
    
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        logger.info(f"Received profile picture: {picture}")
        if picture:
            cleaned_picture = validate_image(picture, max_size_mb=2, resize_target=(1024, 1024))
            logger.info(f"Cleaned profile picture: {cleaned_picture}") 
            return cleaned_picture
        return picture
    
    def clean_city(self):
        city_id = self.data.get('city')
        if city_id:
            try:
                city_instance = self.dal.get_by_id(City, int(city_id))
                if city_instance:
                    return city_instance
                else:
                    raise forms.ValidationError("City not found.", code='not_found')
            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid city ID.", code='invalid')
        return None

    def clean_country(self):
        country_id = self.data.get('country')
        if country_id:
            try:
                country_instance = self.dal.get_by_id(Country, int(country_id))
                if country_instance:
                    return country_instance
                else:
                    raise forms.ValidationError("Country not found.", code='not_found')
            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid country ID.", code='invalid')
        return None

    def clean_terms_accepted(self):
        terms_accepted = self.cleaned_data.get('terms_accepted')
        if terms_accepted is not True:
            raise forms.ValidationError("You must accept the terms to provide services.")
        return terms_accepted
    
    def clean_languages_spoken(self):
        languages = self.cleaned_data.get('languages_spoken')
        if not languages:
            raise forms.ValidationError("At least one language must be selected.")
        return languages
    
    def clean_active_until(self):
        active_until = self.cleaned_data.get('active_until')
        if active_until and active_until < timezone.now().date():
            raise forms.ValidationError("The 'active until' date must be in the future.")
        return active_until


    def clean(self):
        cleaned_data = super().clean()

        # Validate mismatched passwords
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error('password2', forms.ValidationError("The two password fields didn’t match.", code='password_mismatch'))

        # Validate country and phone number
        country_of_issue = cleaned_data.get('country_of_issue')
        phone_number = cleaned_data.get('phone_number')
        if phone_number and not country_of_issue:
            self.add_error('country_of_issue', forms.ValidationError('Country of issue is required when a phone number is provided.', code='phone_country_required'))
        elif country_of_issue and not phone_number:
            self.add_error('phone_number', forms.ValidationError('Phone number is required when a country of issue is provided.', code='phone_required'))

        # Validate looking to earn with support provider categories
        looking_to_earn = cleaned_data.get('looking_to_earn')
        categories = cleaned_data.get('support_provider_categories')
        if looking_to_earn and not categories:
            self.add_error('support_provider_categories', forms.ValidationError("Please select at least one category of service you provide.", code='category_required'))




        return cleaned_data
    



    def save(self, commit=True):
        logger.info("Entering SupportProviderRegisterForm save method")
        user = super().save(commit=False)
        user.is_active = False


        logger.info(f"User instance created: {user}")
        if commit:
            user.save()
            # Add the user to the 'SupportProvider' group
            support_provider_group, created = Group.objects.get_or_create(name='SupportProvider')
            user.groups.add(support_provider_group)
            logger.info(f"User added to 'SupportProvider' group and saved: {user}")


        support_provider = SupportProvider(
            user=user,
            identification_number=self.cleaned_data['identification_number'],
            id_type=self.cleaned_data['id_type'],
            country_of_issue=self.cleaned_data['country_of_issue'],
            city=self.cleaned_data['city'],
            country=self.cleaned_data['country'],
            phone_number=self.cleaned_data.get('phone_number'),
            terms_accepted=self.cleaned_data['terms_accepted'],
            address=self.cleaned_data['address'],
            looking_to_earn=self.cleaned_data['looking_to_earn'],
            active_until=self.cleaned_data['active_until'],
            additional_info=self.cleaned_data['additional_info'],
            profile_picture=self.cleaned_data.get('profile_picture'),
            kosher=self.cleaned_data.get('kosher', False),
            accessible_facilities=self.cleaned_data['accessible_facilities'],
            service_hours=self.cleaned_data['service_hours'],  
        )
        support_provider.save()

        support_provider.languages_spoken.set(self.cleaned_data['languages_spoken'])
        support_provider.support_provider_categories.set(self.cleaned_data['support_provider_categories'])


        return user





class SupportProviderUpdateForm(forms.ModelForm):
    """
    Form for updating the details of an existing Support Provider. This form allows for the modification
    of certain fields specific to the SupportProvider model.
    """

    phone_number = forms.CharField(required=True)
    profile_picture = forms.ImageField(required=False)
    kosher = forms.BooleanField(required=False, label=_("Offers Kosher Services"))
    rating = forms.IntegerField(
        validators=[
            MinValueValidator(1, message=_("Rating cannot be less than 1")),
            MaxValueValidator(5, message=_("Rating cannot be more than 5"))
        ],
        required=False
    )
    accessible_facilities = forms.BooleanField(required=False)
    service_hours = forms.CharField(max_length=255, required=False)

    def clean_phone_number(self):
        country = self.cleaned_data.get('country')
        phone_number = self.cleaned_data.get('phone_number')
        return clean_phone_number(country.id, phone_number)

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            picture = validate_image(picture, max_size_mb=2, resize_target=(1024, 1024))
        return picture

    class Meta:
        model = SupportProvider
        fields = [
            'languages_spoken', 'city', 'country', 'phone_number',
            'support_provider_categories', 'additional_info', 'address',
            'looking_to_earn', 'profile_picture', 'kosher',
            'accessible_facilities', 'service_hours'
        ]

    def save(self, commit=True):
        support_provider = super().save(commit=False)
        if commit:
            support_provider.save()
        
        # Handle the many-to-many fields and newly added fields
        support_provider.languages_spoken.set(self.cleaned_data['languages_spoken'])
        support_provider.support_provider_categories.set(self.cleaned_data['support_provider_categories'])
        # Update additional fields if provided
        if 'kosher' in self.cleaned_data:
            support_provider.kosher = self.cleaned_data['kosher']
        if 'accessible_facilities' in self.cleaned_data:
            support_provider.accessible_facilities = self.cleaned_data['accessible_facilities']
        if 'service_hours' in self.cleaned_data:
            support_provider.service_hours = self.cleaned_data['service_hours']
        
        support_provider.save()  # Save the updated data
        return support_provider

