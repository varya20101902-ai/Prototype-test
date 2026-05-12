"""
Маршруты проекта Quizsite.
"""
from django.contrib import admin
from django.urls import path

from Quiz import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('create-test/', views.create_test_view, name='create_test'),
    path('Quiz1/', views.Quiz1, name='Quiz1'),
    path('submit-quiz/', views.submit_quiz_view, name='submit_quiz'),
]
