from django.conf import settings
from django.db import models


class Branch(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='subjects')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('name', 'branch')

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class SubscriptionPlan(models.Model):
    TYPE_CHOICES = [('INDIVIDUAL', 'Individual'), ('GROUP', 'Group')]
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='plans')
    plan_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    subjects = models.ManyToManyField(Subject, related_name='plans', blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class SubscriptionPrice(models.Model):
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='prices')
    lessons_per_month = models.PositiveIntegerField()
    price_per_lesson = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ('plan', 'lessons_per_month')

    def __str__(self):
        return f"{self.plan.name}: {self.lessons_per_month} -> {self.price_per_lesson}"


class Student(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)

    parent_name = models.CharField(max_length=255, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True)
    parent_email = models.EmailField(blank=True)
    parent_relationship = models.CharField(max_length=50, blank=True)

    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='students')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Subscription(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='subscriptions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student} - {self.subject.name} ({self.plan.name})"


class Group(models.Model):
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='groups')
    students = models.ManyToManyField(Student, related_name='groups', blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.branch.name})"


class Lesson(models.Model):
    LESSON_TYPE = [
        ('INDIVIDUAL', 'Individual'),
        ('GROUP', 'Group')
    ]

    STATUS = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]

    SCHEDULE_TYPE = [
        ('single', 'Один урок'),
        ('recurring', 'Повторюваний урок')
    ]

    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPE,
        default='GROUP'
    )

    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPE,
        default='single'
    )

    repeat_until = models.DateField(
        null=True,
        blank=True
    )

    repeat_days = models.CharField(
        max_length=100,
        blank=True
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='lessons'
    )

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'TEACHER'},
        related_name='lessons'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='individual_lessons'
    )

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='group_lessons'
    )

    date = models.DateField(
        null=True,
        blank=True
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='SCHEDULED'
    )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    'teacher',
                    'date',
                    'start_time',
                    'end_time'
                ]
            )
        ]

    def __str__(self):
        who = self.student or self.group
        return f"{self.subject.name} - {who} ({self.date} {self.start_time})"
    
class LessonTemplate(models.Model):
    LESSON_TYPE = [('INDIVIDUAL', 'Individual'), ('GROUP', 'Group')]
    DAYS_OF_WEEK = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ]

    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='templates')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='templates')

    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='individual_templates')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_templates')

    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    date_from = models.DateField()
    date_to = models.DateField()

    is_active = models.BooleanField(default=True)

    def __str__(self):
        who = self.student or self.group
        return f"{self.subject.name} - {who} ({self.get_day_of_week_display()} {self.start_time})"


class Attendance(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    is_present = models.BooleanField(default=False)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('lesson', 'student')

    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.student} - {self.lesson.date}: {status}"