from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from Rachel.utils import clean_phone_number , validate_image
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

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password1', 'password2', 'identification_number', 'id_type',
            'country_of_issue', 'languages_spoken', 'city', 'country', 'phone_number',
            'terms_accepted', 'support_provider_categories', 'additional_info', 'address', 'looking_to_earn'
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
            'looking_to_earn', 'profile_picture'  
        ]

    def save(self, commit=True):
        support_provider = super().save(commit=False)
        if commit:
            support_provider.save()

        # Handle the many-to-many fields
        support_provider.languages_spoken.set(self.cleaned_data['languages_spoken'])
        support_provider.support_provider_categories.set(self.cleaned_data['support_provider_categories'])

        return support_provider

