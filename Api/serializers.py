from rest_framework import serializers
from django.contrib.auth.models import User
from Rachel.models import (Country, City, Language,
                           UserActivity, UserFeedback, FeedbackResponse, Notification,
                           AddressLookup, SearchHistory, UnauthorizedAccessAttempt,
                           ConfirmationCode, PasswordResetRequest, CommonUserProfile, 
                           Administrator, SupportProvider, Shelter, UserPreference,
                           Civilian, Intentions, SupportProviderCategory, SupportProviderRating )



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'region', 'iso3', 'phone_code']

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'country', 'population']

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'lang_code']


class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'activity_type', 'ip_address', 'timestamp']

class UserFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeedback
        fields = ['id', 'user', 'support_provider', 'feedback_text', 'status', 'created_at']

class FeedbackResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackResponse
        fields = ['id', 'feedback', 'responder', 'response_text', 'created_at', 'feedback_image']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'title', 'message', 'read', 'notification_type']



class CommonUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonUserProfile
        fields = ['user', 'identification_number', 'id_type', 'country_of_issue', 'languages_spoken', 'active_until', 'address', 'profile_picture', 'city', 'country', 'phone_number', 'terms_accepted']


class AdministratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrator
        fields = '__all__'

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = '__all__'


class AddressLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressLookup
        fields = '__all__'

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = '__all__'

class UnauthorizedAccessAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnauthorizedAccessAttempt
        fields = '__all__'

class ConfirmationCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfirmationCode
        fields = '__all__'

class PasswordResetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PasswordResetRequest
        fields = '__all__'


class IntentionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intentions
        fields = '__all__'

class SupportProviderCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportProviderCategory
        fields = '__all__'

class ShelterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = '__all__'

class SupportProviderRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportProviderRating
        fields = '__all__'
        


class CivilianProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Civilian
        fields = '__all__' 

class SupportProviderProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportProvider
        fields = '__all__'



class CivilianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Civilian
        fields = '__all__'

class SupportProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportProvider
        fields = '__all__'