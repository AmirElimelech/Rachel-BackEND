import logging
from django.contrib import admin
from .models import (
    Country,
    City,
    Intentions,
    SupportProviderCategory,
    Civilian,
    SupportProvider,
    Administrator,
    Language,
    Shelter,
    UserActivity,
    UserFeedback,
    Notification,
    FeedbackResponse,
    AddressLookup,
    UserPreference,
    SearchHistory,
    UnauthorizedAccessAttempt,
    ConfirmationCode
)
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

logger = logging.getLogger(__name__)



# Custom UserAdmin
class UserAdmin(BaseUserAdmin):
    def save_model(self, request, obj, form, change):
        # Check if 'is_active' has changed to True
        is_activating = 'is_active' in form.changed_data and obj.is_active

        # Save the user object
        super().save_model(request, obj, form, change)

        # If 'is_active' changed to True, send the activation email
        if is_activating:
            # Your email sending logic
            subject = 'Account Activated'
            body = f'Your account {obj.username} has been activated. You can now login, thank you.'
            message = EmailMessage(
                subject=subject,
                body=body,
                from_email='your_email@example.com',
                to=[obj.email],  # Ensure this is a list
            )
            message.send()
            logger.info(f"Account activation email successfully sent to: {obj.email}")

# Unregister the original User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'iso3', 'phone_code')
    exclude = ('deleted_at',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'population')
    exclude = ('deleted_at',)


@admin.register(Intentions)
class IntentionsAdmin(admin.ModelAdmin):
    list_display = ('name',)
    exclude = ('deleted_at',)


@admin.register(SupportProviderCategory)
class SupportProviderCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    exclude = ('deleted_at',)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'lang_code')
    exclude = ('deleted_at',)


@admin.register(Shelter)
class ShelterAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'city', 'country', 'latitude', 'longitude', 'capacity')
    exclude = ('deleted_at',)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'timestamp')
    exclude = ('deleted_at',)


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'feedback_text', 'created_at')
    exclude = ('deleted_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'message', 'read', 'notification_type')
    exclude = ('deleted_at',)


@admin.register(Civilian)
class CivilianAdmin(admin.ModelAdmin):
    list_display = ('user', 'identification_number', 'id_type', 'country_of_issue', 'active_until', 'city', 'country', 'phone_number', 'terms_accepted')
    exclude = ('deleted_at',)


@admin.register(SupportProvider)
class SupportProviderAdmin(admin.ModelAdmin):
    list_display = ('user', 'identification_number', 'id_type', 'country_of_issue', 'active_until', 'city', 'country', 'phone_number', 'terms_accepted')
    exclude = ('deleted_at',)


@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('user', 'identification_number', 'id_type', 'country_of_issue', 'active_until', 'city', 'country', 'phone_number', 'terms_accepted', 'department')
    exclude = ('deleted_at',)



@admin.register(FeedbackResponse)
class FeedbackResponseAdmin(admin.ModelAdmin):
    list_display = ('feedback', 'responder', 'response_text', 'created_at')

    


@admin.register(AddressLookup)
class AddressLookupAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'place_id', 'latitude', 'longitude', 'display_name')
    exclude = ('deleted_at',)

    

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'dark_mode', 'notification_enabled', 'language_preference', 'email_updates')
    exclude = ('deleted_at',)



@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'created_at')
    exclude = ('deleted_at',)


@admin.register(UnauthorizedAccessAttempt)
class UnauthorizedAccessAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'timestamp', 'browser', 'operating_system', 'country')
    search_fields = ('user__email', 'ip_address')
    list_filter = ('timestamp', 'country')
    

@admin.register(ConfirmationCode)
class ConfirmationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'action_type')
    list_filter = ('user',)
