from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Branch, Subject, Student, Lesson, Attendance
import datetime

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            phone_number='+380991234567',
            password='testpass123',
            role='TEACHER'
        )
        self.assertEqual(user.phone_number, '+380991234567')
        self.assertEqual(user.role, 'TEACHER')
        self.assertTrue(user.is_active)

class LessonConflictTest(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name='Test', city='Kyiv')
        self.subject = Subject.objects.create(name='Python', branch=self.branch)
        self.teacher = User.objects.create_user(
            phone_number='+380991234569',
            password='testpass123',
            role='TEACHER'
        )
        self.lesson = Lesson.objects.create(
            lesson_type='GROUP',
            subject=self.subject,
            teacher=self.teacher,
            date=datetime.date(2026, 6, 1),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
            status='SCHEDULED'
        )

    def test_conflict_exists(self):
        conflict = Lesson.objects.filter(
            teacher=self.teacher,
            date=datetime.date(2026, 6, 1),
            start_time__lt=datetime.time(11, 0),
            end_time__gt=datetime.time(10, 0)
        ).exclude(status='CANCELLED').exists()
        self.assertTrue(conflict)

class AttendanceTest(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name='Test', city='Kyiv')
        self.subject = Subject.objects.create(name='Python', branch=self.branch)
        self.teacher = User.objects.create_user(
            phone_number='+380991234570',
            password='testpass123',
            role='TEACHER'
        )
        self.student = Student.objects.create(
            first_name='Олена',
            last_name='Коваленко',
            branch=self.branch
        )
        self.lesson = Lesson.objects.create(
            lesson_type='INDIVIDUAL',
            subject=self.subject,
            teacher=self.teacher,
            student=self.student,
            date=datetime.date(2026, 6, 1),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 0),
            status='SCHEDULED'
        )

    def test_create_attendance(self):
        attendance = Attendance.objects.create(
            lesson=self.lesson,
            student=self.student,
            is_present=True
        )
        self.assertTrue(attendance.is_present)