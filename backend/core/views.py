from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.exceptions import NotFound, PermissionDenied

from .models import Lesson, Student, Attendance, Branch, Subject, SubscriptionPlan, SubscriptionPrice, Group
from .serializers import (
    LessonSerializer, StudentSerializer, BranchSerializer, SubjectSerializer, 
    SubscriptionPlanSerializer, SubscriptionPriceSerializer, GroupSerializer, AttendanceSerializer
)
from .permissions import IsAdminOrReadOnly, IsAdminOrTeacher, IsAdminOrTeacherForAttendance

@login_required
def teacher_dashboard(request):
    user = request.user

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        group_id = request.POST.get('group')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        if subject_id and date and start_time and end_time:
            Lesson.objects.create(
                subject_id=subject_id,
                group_id=group_id if group_id else None,
                date=date,
                start_time=start_time,
                end_time=end_time,
                teacher=user
            )
            messages.success(request, "Урок успішно додано!")
            return redirect('teacher_dashboard')
        else:
            messages.error(request, "Будь ласка, заповніть усі поля форми.")

    lessons = Lesson.objects.filter(teacher=user).order_by('date', 'start_time')
    subjects = Subject.objects.all()
    groups = Group.objects.all()
    
    return render(request, 'core/teacher_dashboard.html', {
        'lessons': lessons, 
        'subjects': subjects,
        'groups': groups,
        'debug_id': user.id
    })

@login_required
def mark_attendance(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, teacher=request.user)
    students = lesson.group.students.all() if lesson.group else ([lesson.student] if lesson.student else [])
    
    if request.method == 'POST':
        custom_status = request.POST.get('lesson_status')
        if custom_status and hasattr(lesson, 'status'):
            lesson.status = custom_status
            lesson.save()

        for student in students:
            status_val = request.POST.get(f'status_{student.id}')
            comment_val = request.POST.get(f'comment_{student.id}', '')
            
            Attendance.objects.update_or_create(
                lesson=lesson,
                student=student,
                date=lesson.date, 
                defaults={
                    'is_present': (status_val == 'present'), 
                    'comment': comment_val
                }
            )
            
        messages.success(request, "Дані уроку та відвідуваність збережено!")
        return redirect('teacher_dashboard')

    return render(request, 'core/mark_attendance.html', {'lesson': lesson, 'students': students})

class TeacherLessonsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        lessons = Lesson.objects.filter(teacher=request.user)
        serializer = LessonSerializer(lessons, many=True)
        return Response(serializer.data)
    
class LessonStudentsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id, teacher=request.user)
        students = lesson.group.students.all() if lesson.group else ([lesson.student] if lesson.student else [])
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAdminOrTeacher]
    def get_queryset(self):
        user = self.request.user
        if user.is_staff: return super().get_queryset()
        if hasattr(user, 'role') and user.role == 'TEACHER': return Lesson.objects.filter(teacher=user)
        return Lesson.objects.none()
    def perform_create(self, serializer):
        if self.request.user.is_staff: serializer.save()
        else: serializer.save(teacher=self.request.user)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrReadOnly]

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAdminOrReadOnly]

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrReadOnly]

class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAdminOrReadOnly]

class SubscriptionPriceViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPrice.objects.all()
    serializer_class = SubscriptionPriceSerializer
    permission_classes = [IsAdminOrReadOnly]

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminOrReadOnly]

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAdminOrTeacherForAttendance]
    def perform_create(self, serializer):
        lesson = serializer.validated_data['lesson']
        if hasattr(self.request.user, 'role') and self.request.user.role == 'TEACHER' and lesson.teacher_id != self.request.user.id:
            raise PermissionDenied('Teacher can only mark attendance on their own lessons.')
        serializer.save()
