from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation  import gettext_lazy as  _
from Rachel.utils import clean_phone_number , validate_image
from django.core.validators import MinValueValidator, MaxValueValidator
from Rachel.models import SupportProvider, Language, SupportProviderCategory, City, Country







class SupportProviderRegisterForm(UserCreationForm):
    """
    Form for registering a new Support Provider. This form extends the UserCreationForm
    and includes additional fields specific to the SupportProvider model.
    """

    identification_number = forms.CharField(max_length=20, required=True)
    id_type = forms.ChoiceField(choices=SupportProvider.ID_TYPE_CHOICES, required=True)
    country_of_issue = forms.ModelChoiceField(queryset=Country.objects.all(), required=True)
    languages_spoken = forms.ModelMultipleChoiceField(queryset=Language.objects.all(), required=True)
    city = forms.ModelChoiceField(queryset=City.objects.all(), required=True)
    country = forms.ModelChoiceField(queryset=Country.objects.all(), required=True)
    phone_number = forms.CharField(required=True)
    terms_accepted = forms.BooleanField(required=True)
    support_provider_categories = forms.ModelMultipleChoiceField(queryset=SupportProviderCategory.objects.all(), required=True)
    additional_info = forms.CharField(widget=forms.Textarea, required=False)
    address = forms.CharField(max_length=200, required=True)
    looking_to_earn = forms.BooleanField(required=True)
    profile_picture = forms.ImageField(required=True)
    kosher = forms.BooleanField(required=False, label=_("Offers Kosher Services"))
    rating = forms.IntegerField(
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
            'kosher', 'rating', 'accessible_facilities', 'service_hours'
        ]

    def clean_phone_number(self):
        country = self.cleaned_data.get('country_of_issue')
        phone_number = self.cleaned_data.get('phone_number')
        return clean_phone_number(country.id, phone_number)
    
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            picture = validate_image(picture, max_size_mb=2, resize_target=(1024, 1024))
        return picture

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

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
            profile_picture=self.cleaned_data.get('profile_picture'),
            kosher=self.cleaned_data.get('kosher', False),
            rating=self.cleaned_data['rating'],
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
            'looking_to_earn', 'profile_picture', 'kosher', 'rating', 
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
        if 'rating' in self.cleaned_data:
            support_provider.rating = self.cleaned_data['rating']
        if 'accessible_facilities' in self.cleaned_data:
            support_provider.accessible_facilities = self.cleaned_data['accessible_facilities']
        if 'service_hours' in self.cleaned_data:
            support_provider.service_hours = self.cleaned_data['service_hours']
        
        support_provider.save()  # Save the updated data
        return support_provider

