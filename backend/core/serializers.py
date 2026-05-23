from rest_framework import serializers
from .models import Lesson, Student, Attendance, Subject, Group
from .models import Branch, SubscriptionPlan, SubscriptionPrice, Subscription, LessonTemplate


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


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'student', 'subject', 'plan', 'start_date', 'is_active']

    def validate(self, data):
        plan = data.get('plan')
        subject = data.get('subject')
        if plan and subject and subject not in plan.subjects.all():
            raise serializers.ValidationError('Subject is not in the subscription plan.')
        return data


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id', 'first_name', 'last_name', 'date_of_birth', 'phone', 'email',
            'address', 'parent_name', 'parent_phone', 'parent_email', 'parent_relationship',
            'branch', 'is_active'
        ]


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
        fields = ['id', 'lesson', 'student', 'is_present', 'comment']

    def validate(self, data):
        lesson = data.get('lesson')
        student = data.get('student')
        if lesson.status == 'CANCELLED':
            raise serializers.ValidationError('Cannot mark attendance for a cancelled lesson.')
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
            raise serializers.ValidationError('Час початку має бути раніше часу завершення!')

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
            raise serializers.ValidationError('Конфлікт у розкладі: вчитель або студент зайняті у цей час!')

        return data


class LessonTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonTemplate
        fields = '__all__'

    def validate(self, data):
        if data.get('date_from') and data.get('date_to'):
            if data['date_from'] > data['date_to']:
                raise serializers.ValidationError('date_from must be before date_to.')
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError('start_time must be before end_time.')
        lesson_type = data.get('lesson_type')
        if lesson_type == 'INDIVIDUAL' and not data.get('student'):
            raise serializers.ValidationError('Individual template requires a student.')
        if lesson_type == 'GROUP' and not data.get('group'):
            raise serializers.ValidationError('Group template requires a group.')
        return data