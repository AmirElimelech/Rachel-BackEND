import logging
from django import forms
from Rachel.DAL import DAL
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
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
    country_of_issue = forms.ModelChoiceField(queryset=Country.objects.all(), required=False)
    languages_spoken = forms.ModelMultipleChoiceField(queryset=Language.objects.all(), required=False)
    city = forms.ModelChoiceField(queryset=City.objects.all(), required=False)
    country = forms.ModelChoiceField(queryset=Country.objects.all(), required=True)
    phone_number = forms.CharField(required=False)
    terms_accepted = forms.BooleanField(required=True, error_messages={'required': "You must accept the terms to create an account."})
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
        

    def __init__(self, *args, **kwargs):
        super(CivilianRegisterForm, self).__init__(*args, **kwargs)
        self.dal = DAL()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existing_user = self.dal.filter(User, email=email).first()
        if existing_user and existing_user.username != self.cleaned_data.get('username'):
            raise forms.ValidationError("A user with that email already exists.", code='unique')
        return email
    

    def clean_phone_number(self):
        country = self.cleaned_data.get('country')
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number:
            raise forms.ValidationError("Phone number is required.")

        if country is None:
            raise forms.ValidationError("Country of issue is required to validate the phone number.")

        cleaned_phone_number = clean_phone_number(country.id, phone_number)

        # Check if phone number already exists for a different user
        existing_civilian = self.dal.filter(Civilian, phone_number=cleaned_phone_number).exclude(user=self.instance).first()
        if existing_civilian:
            raise forms.ValidationError("A user with that phone number already exists.", code='unique')

        return cleaned_phone_number


    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        logger.info(f"Received profile picture: {picture}")
        if picture:
            cleaned_picture = validate_image(picture, max_size_mb=2, resize_target=(1024, 1024))
            logger.info(f"Cleaned profile picture: {cleaned_picture}") 
            return cleaned_picture
        return picture


    def clean_city(self):
        city_id = self.data.get('city')  # Directly accessing raw data from the form

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
        country_id = self.data.get('country')  # Directly accessing raw data from the form

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
            raise forms.ValidationError("You must accept the terms to create an account.")
        return terms_accepted
            
    def clean_identification_number(self):
        identification_number = self.cleaned_data.get('identification_number')
        existing_provider = self.dal.filter(Civilian, identification_number=identification_number).exclude(user=self.instance).first()
        if existing_provider:
            raise forms.ValidationError("A user with that identification number already exists.", code='unique')
        return identification_number
    
    def clean(self):
        cleaned_data = super().clean()

        # Mismatched passwords check
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error('password2', forms.ValidationError("The two password fields didn’t match.", code='password_mismatch')) 

        # Interdependent field validation for country_of_issue
        id_type = cleaned_data.get('id_type')
        country_of_issue = cleaned_data.get('country_of_issue')
        if id_type == 'other' and not country_of_issue:
            self.add_error('country_of_issue', forms.ValidationError('Country of issue is required for Other Identification type.', code='required'))

        # Phone number validation
        phone_number = cleaned_data.get('phone_number')
        if not phone_number:
            self.add_error('phone_number', forms.ValidationError('Phone number is required.', code='phone_required'))

        # New validation for city and country match
        city_instance = cleaned_data.get('city')
        country_instance = cleaned_data.get('country')
        
        if city_instance and country_instance and city_instance.country != country_instance:
            self.add_error('city', forms.ValidationError("The selected city does not belong to the chosen country.", code='city_country_mismatch'))

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
