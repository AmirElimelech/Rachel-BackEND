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
)




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

    def get_queryset(self, request):
        """
        Override the queryset to filter out any entries that have a deleted timestamp.
        This is in line with the logic used in other admin classes where 'deleted_at' is excluded.
        """
        return super().get_queryset(request).filter(deleted_at__isnull=True)
    

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'dark_mode', 'notification_enabled', 'language_preference', 'email_updates')
    exclude = ('deleted_at',)



@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'created_at')
    exclude = ('deleted_at',)