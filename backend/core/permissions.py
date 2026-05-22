from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsAdminOrTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True
        return hasattr(request.user, 'role') and request.user.role == 'TEACHER'

class IsAdminOrTeacherForAttendance(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return hasattr(request.user, 'role') and request.user.role == 'TEACHER' and obj.lesson.teacher_id == request.user.id
