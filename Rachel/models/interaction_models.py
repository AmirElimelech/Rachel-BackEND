# Imports 


import datetime
from django.db import  models
from .user_models import SupportProvider
from .core_models import TimestampedModel
from django.contrib.auth.models import User
from django.core.exceptions import  ValidationError
from simple_history.models import  HistoricalRecords
from django.utils.translation import gettext_lazy as _










#UserActivity Model

class UserActivity(TimestampedModel):

    """
    Model for tracking various user activities, such as logins and logouts.
    It includes user identification, the type of activity, and the timestamp of the activity.
    Fields:
    - user: Reference to the User model for identifying the user.
    - activity_type: Type of activity performed (e.g., 'login', 'logout').
    - ip_address: IP address from which the activity was performed.
    - timestamp: The datetime when the activity occurred.
    """
    ACTIVITY_CHOICES = [
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('welcome_email_sent',_('Welcome Email Sent')),
        ('account_activated', _('Account Activated')),
        ('account_deactivated', _('Account Deactivated')),
        ('password_change', _('Password Change')),
        ('profile_updated', _('Profile Updated')),
        ('login_failed', _('Failed Login Attempt')),
        ('account_creation', _('Account Creation')),
        ('password_reset_request', _('Password Reset Request')),
        ('password_reset_completed', _('Password Reset Completed')),
        ('tos_accepted', _('Terms of Service Accepted')),
        ('preferences_updated', _('Preferences Updated')),
        ('user_feedback', _('User Feedback Submission')),
        ('support_provider_rated', _('Support Provider Rated')),
        ('address_lookup', _('Address Searched')),
        ('feedback_responded', _('Feedback Responded')),



        
        
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    ip_address = models.GenericIPAddressField()  # To store the IP address
    timestamp = models.DateTimeField(auto_now_add=True)  # Records the time of activity

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp}"
    

    class Meta:
        verbose_name = _("User Activity")
        verbose_name_plural = _("User Activities")
    


#UserFeedback Model
class UserFeedback(TimestampedModel):

    """
    Model for storing user feedback.
    Fields:
    - user: Reference to the User model for identifying the user giving feedback.
    - support_provider: Reference to the SupportProvider model for identifying the support provider being reviewed.
    - feedback_text: The actual feedback provided by the user.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    support_provider = models.ForeignKey(SupportProvider, on_delete=models.CASCADE, null=True, blank=True)
    feedback_text = models.TextField()
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.user.username} - Feedback for {self.support_provider.user.username} at {self.created_at}"

    class Meta:
        verbose_name = _("User Feedback")
        verbose_name_plural = _("User Feedbacks")



class FeedbackResponse(models.Model):

    """
    A model representing responses to user feedback. This model includes validations to ensure that:
    - Only administrators can respond.
    - Responses are not empty and adhere to a maximum length.
    - Feedback being responded to exists and is not too old.
    - Each piece of feedback receives only one response.
    """
    FEEDBACK_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]

    feedback = models.ForeignKey(UserFeedback, on_delete=models.CASCADE, related_name='responses')
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    response_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=FEEDBACK_STATUS_CHOICES,default='pending',)
    history = HistoricalRecords()

    def __str__(self):
        return f"Response to {self.feedback.user.username}'s feedback"

    def clean(self):

        """Perform validations on the FeedbackResponse model, aggregating all errors."""
        errors = {}
        min_length = 5
        max_length = 1000  # Example: 1000 characters

        # Check if the responder is an administrator or a support provider
        if not (self.responder.groups.filter(name='Administrator').exists() or 
                self.responder.groups.filter(name='SupportProvider').exists()):
            errors['responder'] = "Only administrators or support providers can respond to feedback."

        # Validation for empty or too short response text
        if len(self.response_text.strip()) == 0:
            errors['response_text'] = "Response text cannot be empty."
        elif len(self.response_text.strip()) < min_length:
            errors['response_text'] = f"Response text must be at least {min_length} characters long."

        # Validation for response text length
        if len(self.response_text) > max_length:
            errors['response_text'] = f"Response text cannot exceed {max_length} characters."

        # Validation for feedback existence and duplicate responses
        if not self.feedback:
            errors['feedback'] = "The feedback being responded to must exist."
        elif FeedbackResponse.objects.filter(feedback=self.feedback).exclude(pk=self.pk).exists():
            errors['feedback'] = "This feedback has already been responded to."

        # Validation for response timing
        feedback_age_limit = 30  # days
        if self.feedback.created_at < datetime.date.today() - datetime.timedelta(days=feedback_age_limit):
            errors['feedback'] = "Cannot respond to feedback older than 30 days."

        if errors:
            raise ValidationError(errors)
        

    class Meta:
        verbose_name = _("Feedback Response")
        verbose_name_plural = _("Feedback Responses")
        





class Notification(TimestampedModel):
    """
    Model for handling notifications for users. Notifications can be of various types like alerts, reminders, or informational messages.
    Fields:
    - recipient: Reference to the User model indicating who will receive the notification.
    - title: A brief title for the notification.
    - message: The content of the notification.
    - read: Boolean field indicating whether the notification has been read.
    - notification_type: The type of notification (e.g., 'alert', 'reminder', 'info').
    - created_at: Timestamp for when the notification was created.
    - updated_at: Timestamp for when the notification was last updated.
    """
    NOTIFICATION_TYPES = [
        ('alert', _('Alert')),
        ('reminder', _('Reminder')),
        ('info', _('Information')),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.TextField()
    read = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    history = HistoricalRecords()


    def mark_as_read(self):
        """Marks the notification as read."""
        if not self.read:
            self.read = True
            self.save()

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
    

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")