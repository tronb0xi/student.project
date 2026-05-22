from django.urls import path, include
from .views import teacher_dashboard, mark_attendance
from rest_framework.routers import DefaultRouter
from .views import (
    LessonViewSet, BranchViewSet, SubjectViewSet, SubscriptionPlanViewSet,
    SubscriptionPriceViewSet, StudentViewSet, GroupViewSet, AttendanceViewSet
)
from . import views

router = DefaultRouter()
router.register(r'lessons', LessonViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'plans', SubscriptionPlanViewSet)
router.register(r'plan-prices', SubscriptionPriceViewSet)
router.register(r'students', StudentViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'attendance', AttendanceViewSet)

urlpatterns = [
    path('', teacher_dashboard, name='teacher_dashboard'),
    path('mark-attendance/<int:lesson_id>/', mark_attendance, name='mark_attendance'),
    path('api/', include(router.urls)),
]
