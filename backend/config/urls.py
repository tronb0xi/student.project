from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from backend.core.views import TeacherLessonsAPIView, LessonStudentsAPIView
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('teacher/', include('backend.core.urls')),
    path('', include('backend.users.urls')),
    path('api/lessons/', TeacherLessonsAPIView.as_view(), name='api_lessons'),
    path('api/lessons/<int:lesson_id>/students/', LessonStudentsAPIView.as_view(), name='api_lesson_students'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
