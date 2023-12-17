
from django import forms
from better_profanity import profanity
from Rachel.utils import validate_image
from Rachel.models import Shelter, City, Country
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _







class ContactForm(forms.Form):

    """
    Form for handling 'Contact Us' submissions.

    This form collects a user's name, email, subject, and message for contact inquiries.
    It includes validations for each field, such as presence, length, and content checks,
    to ensure that the submitted data is appropriate and informative.
    """

    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Your Name'}),
        error_messages={'required': "Name is required."}
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Your Email'}),
        validators=[EmailValidator(message=_("Enter a valid email address."))],
        error_messages={'required': "Email is required."}
    )
    subject = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Subject'}),
        error_messages={'required': "Subject cannot be empty."}
    )
    message = forms.CharField(
        max_length=750,
        widget=forms.Textarea(attrs={'placeholder': 'Your Message'}),
        required=True,
        error_messages={'required': "Message cannot be empty."}
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        return email

    def clean_subject(self):
        subject = self.cleaned_data.get('subject')
        if len(subject) < 5:
            raise forms.ValidationError("Subject must be at least 5 characters long.")
        return subject

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if not message.strip():
            raise forms.ValidationError("Message text cannot be empty.")

        if len(message) < 10:
            raise forms.ValidationError("Message too short. Please send a valid message that is at least 10 characters long.")

        if profanity.contains_profanity(message):
            raise ValidationError("Please avoid using inappropriate language in your message.")

        return message

    def clean(self):
        # Basic clean method
        return super().clean()    



class ShelterForm(forms.ModelForm):

    """
    Form for creating and updating Shelter details. This form includes fields for the shelter's name,
    address, geographic location (city, country, latitude, longitude), capacity, and a picture.

    Real-world scenarios covered in validation:
    - Picture: Ensures the uploaded picture is of a valid format and size.
    - Latitude & Longitude: Validates the geographical coordinates are within appropriate ranges.
    - Capacity: Checks that the shelter's capacity is a positive number.
    """
    
    city = forms.ModelChoiceField(queryset=City.objects.all(), required=True)
    country = forms.ModelChoiceField(queryset=Country.objects.all(), required=True)
    picture = forms.ImageField(required=True)

    class Meta:
        model = Shelter
        fields = ['name', 'address', 'city', 'country', 'latitude', 'longitude', 'capacity', 'picture', 'support_provider']

    def clean_picture(self):
        picture = self.cleaned_data.get('picture')
        if picture:
            return validate_image(picture, max_size_mb=2, resize_target=(1024, 1024))
        return picture

    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude < -90 or latitude > 90:
            raise forms.ValidationError("Latitude must be between -90 and 90 degrees.")
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude < -180 or longitude > 180:
            raise forms.ValidationError("Longitude must be between -180 and 180 degrees.")
        return longitude

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity <= 0:
            raise forms.ValidationError("Capacity must be a positive number.")
        return capacity
    
    def save(self, commit=True):
        shelter = super().save(commit=False)
        if commit:
            shelter.save()
        return shelter




class ShelterUpdateForm(forms.ModelForm):
    
    """
    Form for updating existing Shelter details, restricting updates to picture and capacity only.
    """

    picture = forms.ImageField(required=True)

    class Meta:
        model = Shelter
        fields = ['capacity', 'picture']

    def clean_picture(self):
        picture = self.cleaned_data.get('picture')
        if picture:
            return validate_image(picture, max_size_mb=2, resize_target=(1024, 1024))
        return picture

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity <= 0:
            raise forms.ValidationError("Capacity must be a positive number.")
        return capacity
    

    def save(self, commit=True):
        shelter = super().save(commit=False)
        if commit:
            shelter.save()
        return shelter