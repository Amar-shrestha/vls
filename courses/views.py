from django.shortcuts import render
from rest_framework import viewsets,status
from .models import Category, Lesson, Enroll, Question, Notifications
from .serializers import CategorySerializer, LessonSerializer, LessonReadSerializer, EnrollSerializer, QuestionSerializer, QuestionReadOnlySerializer, NotificationsSerializer
from rest_framework.decorators import action
from django.core.mail import send_mail, EmailMultiAlternatives
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from accounts.serializers import UserSerializer
from django.contrib.auth import get_user_model
User = get_user_model()

class CategoryView(viewsets.ModelViewSet):
	queryset = Category.objects.all()
	serializer_class = CategorySerializer

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user)


class LessonView(viewsets.ModelViewSet):
	queryset = Lesson.objects.all()
	filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
	filterset_fields = ['title', 'description','category__title']
	search_fields = ['title', 'description','category__title']
	ordering_fields = ['title', 'description','category__title']

	def get_serializer_class(self):

		if self.request.method == 'LIST':
			return LessonReadSerializer

		if self.request.method == 'retrieve': 
			return LessonReadSerializer

		if self.request.method == 'POST':
			return LessonSerializer

		if self.request.method == 'PUT':
			return LessonSerializer

		return LessonReadSerializer

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user)

	@action(methods=['get'], detail=False)
	def trainerlessons(self, request, *args, **kwargs):
		queryset=Lesson.objects.filter(created_by=self.request.user)
		page=self.paginate_queryset(queryset)
		serializers=LessonReadSerializer(page, many=True)
		return self.get_paginated_response(serializers.data)

class NotificationsView(viewsets.ModelViewSet):
	queryset = Notifications.objects.all()
	serializer_class = NotificationsSerializer
	filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
	filterset_fields = ['title', 'description','course','course__id']
	search_fields = ['title', 'description','course','course__id']
	ordering_fields = ['title', 'description','course','course__id']


class EnrollView(viewsets.ModelViewSet):
	queryset = Enroll.objects.all()
	serializer_class = EnrollSerializer
	permission_classes=(IsAuthenticated, )


	def perform_create(self, serializer):
		user = self.request.user
		serializer.save(user=user)
		user_email=serializer.data.get('user')

		subject, from_email, to = 'Course Enrollment Confirmation', 'no-reply@vls.com', user_email
		email_body = 'Hi - ' + user_email
		email_content = 'Thanks for choosing our course'
		html_content = f'<p>{email_body}</p>\n{email_content}'
		msg = EmailMultiAlternatives(subject, email_body, from_email, [to])
		msg.attach_alternative(html_content, "text/html")
		msg.send()

		response_data = {
		    "detail": "sucess"
		}
		return Response(response_data, status=status.HTTP_201_CREATED)


	@action(methods=['get'], detail=False)
	def enrolllessons(self, request, *args, **kwargs):
		queryset=Enroll.objects.filter(user=self.request.user).values_list('lesson',flat=True)
		lessons=Lesson.objects.filter(id__in=queryset)
		page=self.paginate_queryset(lessons)
		serializers=LessonReadSerializer(page, many=True)
		return self.get_paginated_response(serializers.data)

	@action(methods=['get'], detail=False)
	def enrollusers(self, request, *args, **kwargs):
		queryset=Enroll.objects.filter(lesson__created_by=self.request.user).values_list('user',flat=True)
		users=User.objects.filter(email__in=queryset)
		page=self.paginate_queryset(users)
		serializers=UserSerializer(page, many=True)
		return self.get_paginated_response(serializers.data)


class QuestionView(viewsets.ModelViewSet):
	queryset = Question.objects.all()
	filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
	filterset_fields = ['answer','lesson__id']
	search_fields = ['answer','lesson__id']
	ordering_fields = ['answer','lesson__id']

	def get_serializer_class(self):

		if self.request.method == 'LIST':
			return QuestionReadOnlySerializer

		if self.request.method == 'retrieve': 
			return QuestionReadOnlySerializer

		if self.request.method == 'POST':
			return QuestionSerializer

		if self.request.method == 'PUT':
			return QuestionSerializer

		return QuestionReadOnlySerializer

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user)

	@action(methods=['get'], detail=True)
	def enrolllessonquestions(self, request, pk):
		queryset=Lesson.objects.filter(id=pk)
		questions=Question.objects.filter(lesson__in=queryset)
		page=self.paginate_queryset(questions)
		serializers=QuestionSerializer(page, many=True)
		return self.get_paginated_response(serializers.data)


	@action(methods=['get'], detail=False)
	def trainerlessonquestions(self, request):
		queryset=Question.objects.filter(created_by=self.request.user)
		page=self.paginate_queryset(queryset)
		serializers=QuestionReadOnlySerializer(page, many=True)
		return self.get_paginated_response(serializers.data)