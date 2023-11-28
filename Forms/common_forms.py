
import logging
from django import forms
from django.core.mail import send_mail
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import SetPasswordForm
from django.core.validators import  MinLengthValidator
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.password_validation import validate_password




logger = logging.getLogger(__name__)





class CustomChangePasswordForm(PasswordChangeForm):

    """
    A custom form for changing user passwords. It extends Django's PasswordChangeForm
    with customized field widgets and additional functionality to send an email notification
    to the user after successfully updating their password.
    """
    
    def __init__(self, *args, **kwargs):
        super(CustomChangePasswordForm, self).__init__(*args, **kwargs)

        # Customizing form fields
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Current Password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'New Password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        old_password = cleaned_data.get('old_password')

        # Check if the new password contains the old password as a substring
        if old_password and new_password1 and old_password in new_password1:
            errors['new_password1'] = _("New password should not contain the old password.")

        # Check for similarity between old and new passwords using a similarity threshold
        similarity_threshold = 0.5  # Adjust the threshold as needed from 0.5 ( less ) to 0.8 ( more )
        similarity_ratio = self.calculate_similarity_ratio(old_password, new_password1)

        if similarity_ratio > similarity_threshold:
            errors['new_password1'] = _("New password should not be too similar to the old password. Choose a more distinct password.")

        # Check if the new passwords match
        if new_password1 and new_password2 and new_password1 != new_password2:
            errors['new_password2'] = _("The two password fields didn't match.")

        # Check if the password is empty
        if not new_password1:
            errors['new_password1'] = _("The new password can't be empty.")

        # Check minimum length requirement
        min_length_validator = MinLengthValidator(limit_value=6)  # Adjust the minimum length as needed
        try:
            min_length_validator.validate(new_password1)
        except ValidationError as e:
            errors['new_password1'] = e.messages[0]


        if errors:
            raise ValidationError(errors)

        return cleaned_data

    def calculate_similarity_ratio(self, str1, str2):
        """
        Calculate the similarity ratio between two strings ( used to compare betweeb the old and the new password )
        """
        len_str1 = len(str1)
        len_str2 = len(str2)
        distance = sum(str1[i] != str2[i] for i in range(len_str1))  # Hamming distance
        max_len = max(len_str1, len_str2)
        similarity_ratio = (max_len - distance) / max_len
        return similarity_ratio

    def save(self, commit=True):
        user = super(CustomChangePasswordForm, self).save(commit=False)
        user.set_password(self.cleaned_data["new_password1"])
        if commit:
            user.save()

            try:
                send_mail(
                    subject='Password Changed',
                    message='Your password has been successfully changed.',
                    from_email='Rachel.for.Israel', # i should be having another mail with noreply . that will be used only to send and not to rx .
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                logger.info(f"Password change notification email sent to: {user.email}")

            except Exception as e:
                logger.error(f"Error in sending password change notification for {user.email}: {e}")

        return user
    





class DeactivateForm(forms.Form):

    """
    A form to handle account deactivation confirmation.

    Fields:
        confirm (BooleanField): A checkbox to confirm the user's intention to deactivate the account.
    """
    
    confirm = forms.BooleanField(
        label="I confirm that I want to deactivate my account",
        required=True
    )

    def clean_confirm(self):
        """
        Custom validation to ensure the user has confirmed their intention to deactivate the account.

        Returns:
            bool: The confirmation status.
        Raises:
            ValidationError: If the confirmation is not provided.
        """
        confirm = self.cleaned_data.get('confirm')

        if not confirm:
            raise forms.ValidationError("You must confirm to proceed with deactivation.")

        try:
            # Additional logging for deactivation confirmation
            logger.info(f"Account deactivation confirmed for user: {self.user.username}")
        except Exception as e:
            # Handle any potential logging errors gracefully
            logger.error(f"Error logging deactivation confirmation for user: {self.user.username}. Error: {e}")

        return confirm
    
class PasswordResetForm(SetPasswordForm):
    """
    A form for resetting a user's password. This form is used in the password reset
    process when the user has clicked on a password reset link and entered a new password.
    It validates that the password meets Django's set criteria and ensures that the
    password entries match.
    """

    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].validators.append(validate_password)
        self.fields['new_password2'].validators.append(validate_password)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                logger.warning("Password reset attempt failed due to mismatched passwords.")
                raise ValidationError(_("The two password fields didn't match."))
            validate_password(password2)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            logger.info(f"Password successfully reset for user: {user.username}")
        return user




