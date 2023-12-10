import logging
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django_countries.fields import CountryField
from django.contrib.auth.forms import UserCreationForm
from Rachel.utils import validate_image , clean_phone_number
from Rachel.models import Civilian, Language, Intentions, City, Country, UserFeedback


logger = logging.getLogger(__name__)


class CivilianRegisterForm(UserCreationForm):
    """
    Form for registering a new Civilian user. This form extends the UserCreationForm
    to include additional fields specific to the Civilian model.
    """

    identification_number = forms.CharField(max_length=20, required=True)
    id_type = forms.ChoiceField(choices=Civilian.ID_TYPE_CHOICES, required=True)
    country_of_issue = forms.ModelChoiceField(queryset=Country.objects.all(), required=True)
    languages_spoken = forms.ModelMultipleChoiceField(queryset=Language.objects.all(), required=False)
    city = forms.ModelChoiceField(queryset=City.objects.all(), required=False)
    country = CountryField().formfield()
    phone_number = forms.CharField(required=False)
    terms_accepted = forms.BooleanField(required=True)
    intentions = forms.ModelMultipleChoiceField(queryset=Intentions.objects.all(), required=False)
    profile_picture = forms.ImageField(required=False)
    address = forms.CharField(max_length=200, required=False)
    gender = forms.ChoiceField(choices=Civilian.GENDER_CHOICES, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 
                  'identification_number', 'id_type', 'country_of_issue', 
                  'languages_spoken', 'city', 'country', 'phone_number', 
                  'terms_accepted', 'intentions', 'profile_picture', 'address', 
                  'first_name', 'last_name']
        

    def clean_phone_number(self):
        country = self.cleaned_data.get('country_of_issue')
        phone_number = self.cleaned_data.get('phone_number')
        if country is not None:
            return clean_phone_number(country.id, phone_number)
        else:
            logger.error("Country of issue is None in clean_phone_number")
            return phone_number

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        logger.info(f"Received profile picture: {picture}")
        if picture:
            cleaned_picture = validate_image(picture, max_size_mb=2, resize_target=(1024, 1024))
            logger.info(f"Cleaned profile picture: {cleaned_picture}")
            return cleaned_picture
        return picture

    def clean(self):
        cleaned_data = super().clean()

        # Interdependent field validation
        country_of_issue = cleaned_data.get('country_of_issue')
        phone_number = cleaned_data.get('phone_number')

        if phone_number and not country_of_issue:
            self.add_error('country_of_issue', 'Country of issue is required when a phone number is provided.')
        elif country_of_issue and not phone_number:
            self.add_error('phone_number', 'Phone number is required when a country of issue is provided.')

        return cleaned_data

    def save(self, commit=True):
        logger.info("Entering CivilianRegisterForm save method")
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # Keep user inactive by default
        user.is_active = False


        logger.info(f"User instance created: {user}")
        if commit:
            user.save()
            # Add the user to the 'Civilian' group
            civilian_group, created = Group.objects.get_or_create(name='Civilian')
            user.groups.add(civilian_group)
            logger.info(f"User added to 'Civilian' group and saved: {user}")

        civilian = Civilian(
            user=user,
            identification_number=self.cleaned_data['identification_number'],
            id_type=self.cleaned_data['id_type'],
            country_of_issue=self.cleaned_data['country_of_issue'],
            city=self.cleaned_data['city'],
            country=self.cleaned_data['country'],
            phone_number=self.cleaned_data.get('phone_number'),
            terms_accepted=self.cleaned_data['terms_accepted'],
            profile_picture=self.cleaned_data['profile_picture'],
            address=self.cleaned_data['address'],
            gender=self.cleaned_data['gender']
        )
        civilian.save()
        civilian.languages_spoken.set(self.cleaned_data['languages_spoken'])
        civilian.intentions.set(self.cleaned_data['intentions'])
        logger.info(f"Civilian profile saved for user: {user.username}")

        return user

class CivilianUpdateForm(forms.ModelForm):
    """
    Form for updating the details of an existing Civilian user. This form allows for the modification
    of certain fields specific to the Civilian model, excluding identification_number, id_type, and 
    country_of_issue, which are not modifiable.
    """

    class Meta:
        model = Civilian
        fields = ['languages_spoken', 'city', 'country', 'phone_number', 'intentions', 'profile_picture', 'address']

    def clean_phone_number(self):
        country = self.cleaned_data.get('country')
        phone_number = self.cleaned_data.get('phone_number')
        return clean_phone_number(country.id, phone_number)

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            picture = validate_image(picture, max_size_mb=2, resize_target=(1024, 1024))
        return picture
    
    

class UserFeedbackForm(forms.ModelForm):

    """
    Form for submitting user feedback. Users can provide feedback through this form,
    which is then stored in the UserFeedback model.
    """

    class Meta:
        model = UserFeedback
        fields = ['feedback_text']
