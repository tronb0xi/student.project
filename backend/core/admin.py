from django.contrib import admin
from .models import Branch, Subject, SubscriptionPlan, SubscriptionPrice, Student, Group, Lesson, Attendance

admin.site.register(Branch)
admin.site.register(Subject)
admin.site.register(SubscriptionPlan)
admin.site.register(SubscriptionPrice)
admin.site.register(Student)
admin.site.register(Group)
admin.site.register(Lesson)
admin.site.register(Attendance)
