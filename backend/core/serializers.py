from rest_framework import serializers
from .models import Lesson, Student, Attendance, Subject, Group
from .models import Branch, SubscriptionPlan, SubscriptionPrice


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ['id', 'name', 'address', 'city', 'is_active']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'branch', 'is_active']


class SubscriptionPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPrice
        fields = ['id', 'lessons_per_month', 'price_per_lesson']


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    prices = SubscriptionPriceSerializer(many=True, read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'branch', 'plan_type', 'subjects', 'is_active', 'prices']


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'date_of_birth', 'phone', 'email',
            'address', 'parent_name', 'parent_phone', 'parent_email', 'parent_relationship',
            'branch', 'is_active', 'subscription_plan'
        ]

    def validate(self, data):
        branch = data.get('branch')
        subscription_plan = data.get('subscription_plan')
        if subscription_plan and branch and subscription_plan.branch_id != branch.id:
            raise serializers.ValidationError('Subscription plan must belong to the same branch as the student.')
        return data


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'branch', 'students', 'is_active']

    def validate(self, data):
        branch = data.get('branch') or getattr(self.instance, 'branch', None)
        students = data.get('students', [])
        if branch:
            for student in students:
                if student.branch_id != branch.id:
                    raise serializers.ValidationError('Students must belong to the same branch as the group.')
        return data


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ['id', 'lesson', 'student', 'date', 'is_present', 'comment']

    def validate(self, data):
        lesson = data.get('lesson')
        student = data.get('student')
        date = data.get('date')
        if lesson.status == 'CANCELLED':
            raise serializers.ValidationError('Cannot mark attendance for a cancelled lesson.')
        if date and date != lesson.date:
            raise serializers.ValidationError('Attendance date must match the lesson date.')
        if lesson.lesson_type == 'INDIVIDUAL' and lesson.student_id != student.id:
            raise serializers.ValidationError('Student is not participant of this individual lesson.')
        if lesson.lesson_type == 'GROUP' and student not in lesson.group.students.all():
            raise serializers.ValidationError('Student is not in the lesson group.')
        return data


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

    def validate(self, data):
        start = data.get('start_time')
        end = data.get('end_time')
        teacher = data.get('teacher')
        group = data.get('group')
        student = data.get('student')
        date = data.get('date')

        if start and end and start >= end:
            raise serializers.ValidationError("Час початку має бути раніше часу завершення!")

        qs = Lesson.objects.filter(date=date).exclude(status='CANCELLED')

        teacher_conflicts = qs.filter(teacher=teacher, start_time__lt=end, end_time__gt=start)

        student_conflicts = Lesson.objects.none()
        if student:
            student_conflicts = qs.filter(student=student, start_time__lt=end, end_time__gt=start)
        elif group:
            members = group.students.all()
            student_conflicts = qs.filter(group__students__in=members, start_time__lt=end, end_time__gt=start)

        conflicts = teacher_conflicts | student_conflicts
        if self.instance:
            conflicts = conflicts.exclude(id=self.instance.id)

        if conflicts.exists():
            raise serializers.ValidationError("Конфлікт у розкладі: вчитель або студент зайняті у цей час!")

        return data
