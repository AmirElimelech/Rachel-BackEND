from django import forms
from Rachel.utils import validate_image
from Rachel.utils import clean_phone_number
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from Rachel.models import Civilian, Language, Intentions, City, Country, UserFeedback






class CivilianRegisterForm(UserCreationForm):

    """
    Form for registering a new Civilian user. This form extends the UserCreationForm
    to include additional fields specific to the Civilian model, such as identification
    number, country of issue, languages spoken, and intentions.
    """

    identification_number = forms.CharField(max_length=20, required=True)
    id_type = forms.ChoiceField(choices=Civilian.ID_TYPE_CHOICES, required=True)
    country_of_issue = forms.ModelChoiceField(queryset=Country.objects.all(), required=True)
    languages_spoken = forms.ModelMultipleChoiceField(queryset=Language.objects.all(), required=False)
    city = forms.ModelChoiceField(queryset=City.objects.all(), required=False)
    country = forms.ModelChoiceField(queryset=Country.objects.all(), required=True)
    phone_number = forms.CharField(required=False)
    terms_accepted = forms.BooleanField(required=True)
    intentions = forms.ModelMultipleChoiceField(queryset=Intentions.objects.all(), required=False)
    profile_picture = forms.ImageField(required=False)
    address = forms.CharField(max_length=200, required=False)
    gender = forms.ChoiceField(choices=Civilian.GENDER_CHOICES, required=True, initial='rather_not_say')


    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'identification_number', 'id_type', 'country_of_issue', 'languages_spoken', 'city', 'country', 'phone_number', 'terms_accepted', 'intentions', 'profile_picture', 'address']

    def clean_phone_number(self):
        country = self.cleaned_data.get('country_of_issue')
        phone_number = self.cleaned_data.get('phone_number')
        return clean_phone_number(country.id, phone_number)
    

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            # Resize image if larger than 2MB to 1024x1024
            picture = validate_image(picture, max_size_mb=2, resize_target=(1024, 1024))
        return picture




    def save(self, commit=True):
        # Save the user instance
        user = super().save(commit=False)
        if commit:
            user.save()
        
        # Now save the Civilian profile
        civilian = Civilian(
            user=user,
            identification_number=self.cleaned_data['identification_number'],
            id_type=self.cleaned_data['id_type'],
            country_of_issue=self.cleaned_data['country_of_issue'],
            city=self.cleaned_data['city'],
            country=self.cleaned_data['country'],
            phone_number=self.cleaned_data.get('phone_number'),  # This will use the processed phone number
            terms_accepted=self.cleaned_data['terms_accepted'],
            profile_picture=self.cleaned_data['profile_picture'],
            address=self.cleaned_data['address'],
            gender=self.cleaned_data['gender']

        )
        civilian.save()

        # Handle the many-to-many fields
        civilian.languages_spoken.set(self.cleaned_data['languages_spoken'])
        civilian.intentions.set(self.cleaned_data['intentions'])
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
