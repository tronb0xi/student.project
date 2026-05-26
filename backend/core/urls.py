from django.urls import path, include
from .views import (
    teacher_dashboard, mark_attendance, lessons_view, reports_view,
    admin_panel, admin_students, admin_teachers, admin_branches
)
from rest_framework.routers import DefaultRouter
from .views import (
    LessonViewSet, BranchViewSet, SubjectViewSet, SubscriptionPlanViewSet,
    SubscriptionPriceViewSet, StudentViewSet, GroupViewSet, AttendanceViewSet,
    SubscriptionViewSet, LessonTemplateViewSet,
    AttendanceHistoryView, TeacherScheduleView, BranchStatisticsView
)

router = DefaultRouter()
router.register(r'lessons', LessonViewSet)
router.register(r'branches', BranchViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'plans', SubscriptionPlanViewSet)
router.register(r'plan-prices', SubscriptionPriceViewSet)
router.register(r'students', StudentViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'subscriptions', SubscriptionViewSet)
router.register(r'lesson-templates', LessonTemplateViewSet)

urlpatterns = [
    path('', teacher_dashboard, name='teacher_dashboard'),
    path('mark-attendance/<int:lesson_id>/', mark_attendance, name='mark_attendance'),
    path('lessons/', lessons_view, name='lessons'),
    path('reports/', reports_view, name='reports'),
    path('admin-panel/', admin_panel, name='admin_panel'),
    path('admin-panel/students/', admin_students, name='admin_students'),
    path('admin-panel/teachers/', admin_teachers, name='admin_teachers'),
    path('api/', include(router.urls)),
    path('api/reports/attendance-history/', AttendanceHistoryView.as_view(), name='attendance_history'),
    path('api/reports/teacher-schedule/', TeacherScheduleView.as_view(), name='teacher_schedule'),
    path('api/reports/branch-statistics/', BranchStatisticsView.as_view(), name='branch_statistics'),
    path('admin-panel/branches/', admin_branches, name='admin_branches'),
]