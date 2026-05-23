from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('api/me/', views.CurrentUserAPIView.as_view(), name='api_me'),
    path('register/', views.register_view, name='register'),
]