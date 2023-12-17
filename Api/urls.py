from django.urls import path
from .views.anonymous_api import register_user_api , login_user_api, contact_us_api, reset_password_api

urlpatterns = [
    path('register/', register_user_api, name='register_user_api'),
    path('login/',login_user_api, name='login_user_api'),
    path('contact_us/', contact_us_api, name='contact_us_api'),
    path('reset_password_request/', reset_password_api, name='reset_password_api'),
] 