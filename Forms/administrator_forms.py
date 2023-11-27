from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import  ValidationError
from django.utils.translation import gettext_lazy as _
from Rachel.models import FeedbackResponse, Notification


class FeedbackResponseForm(forms.ModelForm):
    """
    Form for creating and managing feedback responses. This form includes fields to select the feedback
    and to provide a response text. Additional validations ensure that responses are appropriate and related
    to the feedback.
    """
    
    class Meta:
        model = FeedbackResponse
        fields = ['feedback', 'response_text']

    def clean_response_text(self):
        response_text = self.cleaned_data.get('response_text')
        # Validation: Ensure response text is not empty and of appropriate length
        if not response_text.strip():
            raise ValidationError("Response text cannot be empty.")
        if len(response_text) < 20:  # Example minimum length
            raise ValidationError("Response text must be at least 20 characters long.")
        return response_text

    def save(self, commit=True):
        feedback_response = super().save(commit=False)
        # Additional logic before saving (if necessary)
        if commit:
            feedback_response.save()
        return feedback_response


class NotificationForm(forms.ModelForm):
    """
    Form for creating and managing notifications. This form includes fields for selecting the recipient,
    setting the title and message of the notification, and specifying the notification type.
    Additional validations ensure the notification details are appropriate and complete.
    """

    class Meta:
        model = Notification
        fields = ['recipient', 'title', 'message', 'notification_type']

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title.strip():
            raise ValidationError("Title cannot be empty.")
        # Add more validation logic if necessary
        return title

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if not message.strip():
            raise ValidationError("Message cannot be empty.")
        # Add more validation logic if necessary
        return message
    
    def clean_notification_type(self):
        notification_type = self.cleaned_data.get('notification_type')
        valid_types = [choice[0] for choice in Notification.NOTIFICATION_TYPES]
        if notification_type not in valid_types:
            raise ValidationError("Invalid notification type selected.")
        return notification_type
    



class ActivationForm(forms.ModelForm):
    
    """
    Form for managing the activation status of users. This form allows administrators to activate or deactivate user accounts.
    
    The form directly updates the 'is_active' status of User model instances, which controls their ability to log in and access the system.
    """
    
    class Meta:
        model = User
        fields = ['is_active']

    def save(self, commit=True):
        user = super().save(commit=False)

        if commit:
            user.save()
        return user


class UserManagementForm(forms.ModelForm):

    """
    Form for managing user details within the system. This form allows administrators to edit user information
    such as username, email, active status, and group membership.

    Enhancements include:
    - Email Validation: Ensures no duplicate emails are used across user accounts.
    - Group Management: Facilitates the assignment of users to specific groups.
    - Save Method: Custom logic to save user data and update group membership as needed.

    This form is designed to be a comprehensive tool for user account management, enabling effective and efficient administration of user data.
    """

    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'is_active', 'group']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Validate that the email is not already in use
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("A user with that email already exists."))
        return email

    def clean_group(self):
        group = self.cleaned_data.get('group')
        # Ensure the selected group is one of the predefined groups
        predefined_groups = ['Administrator', 'SupportProvider', 'Civilian']
        if group and group.name not in predefined_groups:
            raise ValidationError(_("Invalid group selected. Please choose from Administrator, SupportProvider, or Civilian."))
        return group

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

            # Update the user's group
            if self.cleaned_data['group'] is not None:
                user.groups.clear()
                user.groups.add(self.cleaned_data['group'])

        return user