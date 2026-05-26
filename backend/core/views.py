from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, status, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
import datetime

from .models import Lesson, Student, Attendance, Branch, Subject, SubscriptionPlan, SubscriptionPrice, Group, Subscription, LessonTemplate
from .serializers import (
    LessonSerializer, StudentSerializer, BranchSerializer, SubjectSerializer,
    SubscriptionPlanSerializer, SubscriptionPriceSerializer, GroupSerializer,
    AttendanceSerializer, SubscriptionSerializer, LessonTemplateSerializer
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
    if request.user.role == 'ADMIN' or request.user.is_staff:
        lesson = get_object_or_404(Lesson, id=lesson_id)
    else:
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
                defaults={
                    'is_present': (status_val == 'present'),
                    'comment': comment_val
                }
            )

        messages.success(request, "Дані уроку та відвідуваність збережено!")

        if request.user.role == 'ADMIN' or request.user.is_staff:
            return redirect('lessons')

        if request.user.role == 'ADMIN' or request.user.is_staff:
            return redirect('lessons')

        return redirect('/teacher/lessons/')

    return render(request, 'core/mark_attendance.html', {
        'lesson': lesson,
        'students': students
    })

@login_required
def lessons_view(request):
    from backend.users.models import User

    if request.method == 'POST':

        subject_id = request.POST.get('subject')
        group_id = request.POST.get('group') or None
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        lesson_type = request.POST.get('lesson_type')
        teacher_id = request.POST.get('teacher')

        schedule_type = request.POST.get('schedule_type')
        date_to = request.POST.get('date_to')
        week_days = request.POST.getlist('week_days')

        days_map = {
            '0': 'Пн',
            '1': 'Вт',
            '2': 'Ср',
            '3': 'Чт',
            '4': 'Пт',
            '5': 'Сб',
            '6': 'Нд',
        }

        repeat_days_text = ', '.join(
            [days_map[day] for day in week_days]
        )

        created_count = 0
        conflict_count = 0

        if schedule_type == 'recurring' and date_to and week_days:

            current_date = datetime.datetime.strptime(
                date,
                "%Y-%m-%d"
            ).date()

            end_repeat_date = datetime.datetime.strptime(
                date_to,
                "%Y-%m-%d"
            ).date()

            selected_week_days = [
                int(day) for day in week_days
            ]

            while current_date <= end_repeat_date:

                if current_date.weekday() in selected_week_days:

                    conflict = Lesson.objects.filter(
                        teacher_id=teacher_id,
                        date=current_date,
                        start_time__lt=end_time,
                        end_time__gt=start_time
                    ).exclude(
                        status='CANCELLED'
                    ).exists()

                    if conflict:

                        conflict_count += 1

                    else:

                        Lesson.objects.create(
                            lesson_type=lesson_type,
                            schedule_type='recurring',
                            repeat_until=end_repeat_date,
                            repeat_days=repeat_days_text,
                            subject_id=subject_id,
                            group_id=group_id,
                            date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                            teacher_id=teacher_id,
                            status='SCHEDULED'
                        )

                        created_count += 1

                current_date += datetime.timedelta(days=1)

            if created_count > 0:
                messages.success(
                    request,
                    f"Створено повторюваних уроків: {created_count}"
                )

            if conflict_count > 0:
                messages.error(
                    request,
                    f"Пропущено через конфліктів: {conflict_count}"
                )

        else:

            conflict = Lesson.objects.filter(
                teacher_id=teacher_id,
                date=date,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(
                status='CANCELLED'
            ).exists()

            if conflict:

                messages.error(
                    request,
                    "Конфлікт: вчитель вже має урок в цей час!"
                )

            else:

                Lesson.objects.create(
                    lesson_type=lesson_type,
                    schedule_type='single',
                    subject_id=subject_id,
                    group_id=group_id,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    teacher_id=teacher_id,
                    status='SCHEDULED'
                )

                messages.success(
                    request,
                    "Урок успішно створено!"
                )

    lessons = Lesson.objects.all().select_related(
        'subject',
        'teacher',
        'group',
        'student'
    ).order_by(
        'date',
        'start_time'
    )

    subjects = Subject.objects.filter(
        is_active=True
    )

    groups = Group.objects.filter(
        is_active=True
    )

    branches = Branch.objects.filter(
        is_active=True
    )

    teachers = User.objects.filter(
        role='TEACHER',
        is_active=True
    )

    return render(
        request,
        'core/lessons.html',
        {
            'lessons': lessons,
            'subjects': subjects,
            'groups': groups,
            'teachers': teachers,
            'branches': branches,
        }
    )


@login_required
def reports_view(request):

    user = request.user

    if user.role == 'TEACHER' and not user.is_staff:

        lessons = Lesson.objects.filter(
            teacher=user
        )

    else:

        lessons = Lesson.objects.all()

    total_lessons = lessons.count()

    completed_lessons = lessons.filter(
        status='COMPLETED'
    ).count()

    cancelled_lessons = lessons.filter(
        status='CANCELLED'
    ).count()

    scheduled_lessons = lessons.filter(
        status='SCHEDULED'
    ).count()

    attendance = Attendance.objects.filter(
        lesson__in=lessons
    )

    total_attendance = attendance.count()

    present_count = attendance.filter(
        is_present=True
    ).count()

    absent_count = total_attendance - present_count

    attendance_percent = round(
        (present_count / total_attendance) * 100,
        1
    ) if total_attendance > 0 else 0

    context = {
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'cancelled_lessons': cancelled_lessons,
        'scheduled_lessons': scheduled_lessons,
        'total_attendance': total_attendance,
        'present_count': present_count,
        'absent_count': absent_count,
        'attendance_percent': attendance_percent,

        'lessons': lessons.order_by(
            'date',
            'start_time'
        )[:10],
    }

    return render(
        request,
        'core/reports.html',
        context
    )


@login_required
def admin_panel(request):

    if not request.user.is_staff and getattr(
        request.user,
        'role',
        None
    ) != 'ADMIN':

        return redirect('teacher_dashboard')

    from backend.users.models import User

    context = {
        'students_count': Student.objects.filter(
            is_active=True
        ).count(),

        'teachers_count': User.objects.filter(
            role='TEACHER',
            is_active=True
        ).count(),

        'lessons_count': Lesson.objects.count(),

        'groups_count': Group.objects.filter(
            is_active=True
        ).count(),
    }

    return render(
        request,
        'core/admin_panel.html',
        context
    )

@login_required
def admin_branches(request):
    if not request.user.is_staff and getattr(request.user, 'role', None) != 'ADMIN':
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        Branch.objects.create(
            name=request.POST.get('name'),
            city=request.POST.get('city', ''),
            address=request.POST.get('address', ''),
            is_active=True
        )
        messages.success(request, 'Філію створено!')
        return redirect('admin_branches')

    branches = Branch.objects.filter(is_active=True)

    return render(request, 'core/admin_branches.html', {
        'branches': branches
    })

@login_required
def admin_students(request):
    if not request.user.is_staff and getattr(request.user, 'role', None) != 'ADMIN':
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        Student.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            branch_id=request.POST.get('branch'),
            is_active=True
        )
        messages.success(request, 'Студента створено!')
        return redirect('admin_students')
    students = Student.objects.filter(is_active=True).select_related('branch')
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'core/admin_students.html', {'students': students, 'branches': branches})

@login_required  
def admin_teachers(request):
    if not request.user.is_staff and getattr(request.user, 'role', None) != 'ADMIN':
        return redirect('teacher_dashboard')
    from backend.users.models import User
    if request.method == 'POST':
        User.objects.create_user(
            phone_number=request.POST.get('phone_number'),
            password=request.POST.get('password'),
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            role='TEACHER'
        )
        messages.success(request, 'Вчителя створено!')
        return redirect('admin_teachers')
    from backend.users.models import User
    teachers = User.objects.filter(role='TEACHER', is_active=True)
    return render(request, 'core/admin_teachers.html', {'teachers': teachers})

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
        if user.is_staff:
            return super().get_queryset()
        if hasattr(user, 'role') and user.role == 'TEACHER':
            return Lesson.objects.filter(teacher=user)
        return Lesson.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_staff:
            serializer.save()
        else:
            serializer.save(teacher=self.request.user)


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


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
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


class LessonTemplateViewSet(viewsets.ModelViewSet):
    queryset = LessonTemplate.objects.all()
    serializer_class = LessonTemplateSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer):
        template = serializer.save()
        self.generate_lessons(template)

    def generate_lessons(self, template):
        current_date = template.date_from
        while current_date <= template.date_to:
            if current_date.weekday() == template.day_of_week:
                teacher_conflict = Lesson.objects.filter(
                    teacher=template.teacher,
                    date=current_date,
                    start_time__lt=template.end_time,
                    end_time__gt=template.start_time
                ).exclude(status='CANCELLED').exists()

                if not teacher_conflict:
                    Lesson.objects.create(
                        lesson_type=template.lesson_type,
                        subject=template.subject,
                        teacher=template.teacher,
                        student=template.student,
                        group=template.group,
                        date=current_date,
                        start_time=template.start_time,
                        end_time=template.end_time,
                        status='SCHEDULED'
                    )
            current_date += datetime.timedelta(days=1)

class AttendanceHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        student_id = request.query_params.get('student_id')
        subject_id = request.query_params.get('subject_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if not student_id:
            return Response({'error': 'student_id is required'}, status=400)

        qs = Attendance.objects.filter(student_id=student_id).select_related('lesson', 'lesson__subject')

        if subject_id:
            qs = qs.filter(lesson__subject_id=subject_id)
        if date_from:
            qs = qs.filter(lesson__date__gte=date_from)
        if date_to:
            qs = qs.filter(lesson__date__lte=date_to)

        total = qs.count()
        present = qs.filter(is_present=True).count()
        absent = total - present

        data = []
        for record in qs.order_by('lesson__date'):
            data.append({
                'date': record.lesson.date,
                'subject': record.lesson.subject.name,
                'is_present': record.is_present,
                'comment': record.comment,
                'lesson_status': record.lesson.status,
            })

        return Response({
            'student_id': student_id,
            'total': total,
            'present': present,
            'absent': absent,
            'records': data
        })


class TeacherScheduleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        teacher_id = request.query_params.get('teacher_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if user.is_staff and teacher_id:
            qs = Lesson.objects.filter(teacher_id=teacher_id)
        else:
            qs = Lesson.objects.filter(teacher=user)

        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)

        qs = qs.select_related('subject', 'student', 'group').order_by('date', 'start_time')

        data = []
        for lesson in qs:
            data.append({
                'id': lesson.id,
                'date': lesson.date,
                'start_time': lesson.start_time,
                'end_time': lesson.end_time,
                'subject': lesson.subject.name,
                'student': str(lesson.student) if lesson.student else None,
                'group': str(lesson.group) if lesson.group else None,
                'status': lesson.status,
            })

        return Response(data)


class BranchStatisticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        branch_id = request.query_params.get('branch_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        if not branch_id:
            return Response({'error': 'branch_id is required'}, status=400)

        active_students = Student.objects.filter(branch_id=branch_id, is_active=True).count()

        lessons_qs = Lesson.objects.filter(subject__branch_id=branch_id)
        if date_from:
            lessons_qs = lessons_qs.filter(date__gte=date_from)
        if date_to:
            lessons_qs = lessons_qs.filter(date__lte=date_to)

        total_lessons = lessons_qs.count()
        completed = lessons_qs.filter(status='COMPLETED').count()
        cancelled = lessons_qs.filter(status='CANCELLED').count()

        attendance_qs = Attendance.objects.filter(lesson__subject__branch_id=branch_id)
        if date_from:
            attendance_qs = attendance_qs.filter(lesson__date__gte=date_from)
        if date_to:
            attendance_qs = attendance_qs.filter(lesson__date__lte=date_to)

        total_attendance = attendance_qs.count()
        present_count = attendance_qs.filter(is_present=True).count()
        attendance_pct = round((present_count / total_attendance * 100), 1) if total_attendance > 0 else 0

        return Response({
            'branch_id': branch_id,
            'active_students': active_students,
            'lessons': {
                'total': total_lessons,
                'completed': completed,
                'cancelled': cancelled,
            },
            'attendance_percentage': attendance_pct,
        })