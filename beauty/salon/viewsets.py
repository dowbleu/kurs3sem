from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Booking, Master, Service
from .serializers import BookingSerializer, MasterSerializer, ServiceSerializer
from .filters import BookingFilter, MasterFilter, ServiceFilter


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet для модели Booking с Q-запросами, фильтрацией и пагинацией"""
    queryset = Booking.objects.select_related('user', 'master', 'service').all()
    serializer_class = BookingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookingFilter
    search_fields = ['user__name', 'user__email', 'master__full_name', 'service__title']
    ordering_fields = ['appointment_datetime', 'created_at', 'status']
    ordering = ['-appointment_datetime']
    
    def get_queryset(self):
        """
        Переопределяем queryset с использованием Q-объектов для сложных запросов
        """
        queryset = Booking.objects.select_related('user', 'master', 'service').all()
        
        # Фильтрация для текущего аутентифицированного пользователя
        if self.request.user.is_authenticated:
            user_filter = self.request.query_params.get('my_bookings', None)
            if user_filter == 'true':
                # Используем Q-запрос для поиска пользователя по email
                try:
                    from .models import User
                    salon_user = User.objects.get(email=self.request.user.email)
                    queryset = queryset.filter(Q(user=salon_user))
                except User.DoesNotExist:
                    queryset = queryset.none()
        
        # Фильтрация по статусу
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Фильтрация по дате записи (Q-запрос)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if date_from or date_to:
            q_objects = Q()
            if date_from:
                q_objects &= Q(appointment_datetime__gte=date_from)
            if date_to:
                q_objects &= Q(appointment_datetime__lte=date_to)
            queryset = queryset.filter(q_objects)
        
        # Сложный Q-запрос: записи с высоким приоритетом (подтвержденные и в ближайшие 7 дней)
        priority = self.request.query_params.get('priority', None)
        if priority == 'high':
            future_date = timezone.now() + timedelta(days=7)
            queryset = queryset.filter(
                Q(status='confirmed') & 
                Q(appointment_datetime__gte=timezone.now()) &
                Q(appointment_datetime__lte=future_date)
            )
        
        # Сложный Q-запрос с OR, AND, NOT: активные записи (не отмененные) и (подтвержденные или в ожидании)
        active_only = self.request.query_params.get('active_only', None)
        if active_only == 'true':
            queryset = queryset.filter(
                ~Q(status='cancelled') & 
                (Q(status='confirmed') | Q(status='pending'))
            )
        
        # Сложный Q-запрос с OR, AND, NOT: будущие записи, не завершенные, не отмененные
        upcoming_active = self.request.query_params.get('upcoming_active', None)
        if upcoming_active == 'true':
            queryset = queryset.filter(
                Q(appointment_datetime__gte=timezone.now()) &
                ~Q(status='completed') &
                ~Q(status='cancelled')
            )
        
        # Q-запрос: записи определенного мастера с определенным статусом
        master_id = self.request.query_params.get('master_id', None)
        if master_id and status_filter:
            queryset = queryset.filter(
                Q(master_id=master_id) & Q(status=status_filter)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Кастомный action для получения статистики по записям
        """
        total_bookings = Booking.objects.count()
        pending = Booking.objects.filter(status='pending').count()
        confirmed = Booking.objects.filter(status='confirmed').count()
        completed = Booking.objects.filter(status='completed').count()
        cancelled = Booking.objects.filter(status='cancelled').count()
        
        # Q-запрос для записей в ближайшие 30 дней
        future_date = timezone.now() + timedelta(days=30)
        upcoming = Booking.objects.filter(
            Q(appointment_datetime__gte=timezone.now()) &
            Q(appointment_datetime__lte=future_date) &
            Q(status__in=['pending', 'confirmed'])
        ).count()
        
        return Response({
            'total_bookings': total_bookings,
            'pending': pending,
            'confirmed': confirmed,
            'completed': completed,
            'cancelled': cancelled,
            'upcoming_30_days': upcoming,
        })


class MasterViewSet(viewsets.ModelViewSet):
    """ViewSet для модели Master с Q-запросами и фильтрацией"""
    queryset = Master.objects.select_related('image').prefetch_related('services').all()
    serializer_class = MasterSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MasterFilter
    search_fields = ['full_name', 'specialization']
    ordering_fields = ['full_name', 'experience_years', 'created_at']
    ordering = ['full_name']
    
    def get_queryset(self):
        """
        Переопределяем queryset с использованием Q-объектов
        """
        queryset = Master.objects.select_related('image').prefetch_related('services').all()
        
        # Фильтрация по опыту работы (Q-запрос)
        min_experience = self.request.query_params.get('min_experience', None)
        max_experience = self.request.query_params.get('max_experience', None)
        
        if min_experience or max_experience:
            q_objects = Q()
            if min_experience:
                q_objects &= Q(experience_years__gte=min_experience)
            if max_experience:
                q_objects &= Q(experience_years__lte=max_experience)
            queryset = queryset.filter(q_objects)
        
        # Q-запрос: мастера с определенной специализацией и опытом
        specialization = self.request.query_params.get('specialization', None)
        if specialization:
            queryset = queryset.filter(
                Q(specialization__icontains=specialization)
            )
        
        # Сложный Q-запрос: опытные мастера (более 5 лет) или с определенной специализацией
        experienced = self.request.query_params.get('experienced', None)
        if experienced == 'true':
            queryset = queryset.filter(
                Q(experience_years__gte=5) | Q(specialization__icontains='стрижк')
            )
        
        # Сложный Q-запрос с OR, AND, NOT: опытные мастера (опыт >= 5 лет ИЛИ специализация содержит "стрижк" или "окрашивание"), 
        # но не новички (опыт >= 1 год)
        senior_not_junior = self.request.query_params.get('senior_not_junior', None)
        if senior_not_junior == 'true':
            queryset = queryset.filter(
                (Q(experience_years__gte=5) | Q(specialization__icontains='стрижк') | Q(specialization__icontains='окрашивание')) &
                ~Q(experience_years__lt=1)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])  # noqa: метод используется через DRF router
    def add_service(self, request, pk=None):
        """
        Кастомный action для добавления услуги мастеру
        """
        master = self.get_object()
        service_id = request.data.get('service_id')
        
        if not service_id:
            return Response(
                {'error': 'service_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = Service.objects.get(pk=service_id)
        except Service.DoesNotExist:
            return Response(
                {'error': 'Service not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Добавляем услугу мастеру
        master.services.add(service)
        return Response({
            'message': f'Услуга "{service.title}" добавлена мастеру "{master.full_name}"'
        }, status=status.HTTP_200_OK)


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для модели Service (только чтение)"""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ServiceFilter
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'price', 'created_at']
    ordering = ['title']
    
    def get_queryset(self):
        """
        Переопределяем queryset с использованием Q-объектов
        """
        queryset = Service.objects.all()
        
        # Фильтрация по цене (Q-запрос)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        
        if min_price or max_price:
            q_objects = Q()
            if min_price:
                q_objects &= Q(price__gte=min_price)
            if max_price:
                q_objects &= Q(price__lte=max_price)
            queryset = queryset.filter(q_objects)
        
        # Q-запрос: услуги с определенным словом в названии или описании
        search_term = self.request.query_params.get('search', None)
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) | Q(description__icontains=search_term)
            )
        
        return queryset

