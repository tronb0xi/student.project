from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer, LoginSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model

from backend.core.models import Lesson

User = get_user_model()

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                phone_number=serializer.validated_data['phone_number'],
                password=serializer.validated_data['password']
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data,
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def login_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        user = authenticate(
            request,
            phone_number=phone,
            password=password
        )

        if user is not None:
            login(request, user)

            if user.role == 'ADMIN' or user.is_staff:
                return redirect('admin_panel')

            if user.role == 'TEACHER':
                return redirect('teacher_dashboard')

            return redirect('login')

        else:
            messages.error(request, "Невірні дані")

    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def teacher_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'TEACHER':
        return redirect('login')

    lessons = Lesson.objects.filter(teacher=request.user).select_related('group', 'subject')
    
    return render(request, 'core/teacher_dashboard.html', {
        'lessons': lessons
    })

def mark_attendance(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, teacher=request.user)

    students = lesson.group.students.all() if lesson.group else []
    
    if request.method == 'POST':
        messages.success(request, "Відвідуваність збережена!")
        return redirect('teacher_dashboard')

    return render(request, 'users/mark_attendance.html', {
        'lesson': lesson,
        'students': students
    })

class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)