import django_filters
from .models import Booking, Master, Service, Review


class BookingFilter(django_filters.FilterSet):
    """Фильтр для модели Booking"""
    status = django_filters.ChoiceFilter(choices=Booking.STATUS_CHOICES)
    date_from = django_filters.DateTimeFilter(field_name='appointment_datetime', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='appointment_datetime', lookup_expr='lte')
    user = django_filters.NumberFilter(field_name='user__user_id')
    master = django_filters.NumberFilter(field_name='master__master_id')
    service = django_filters.NumberFilter(field_name='service__service_id')
    
    class Meta:
        model = Booking
        fields = ['status', 'user', 'master', 'service']


class MasterFilter(django_filters.FilterSet):
    """Фильтр для модели Master"""
    min_experience = django_filters.NumberFilter(field_name='experience_years', lookup_expr='gte')
    max_experience = django_filters.NumberFilter(field_name='experience_years', lookup_expr='lte')
    specialization = django_filters.CharFilter(field_name='specialization', lookup_expr='icontains')
    
    class Meta:
        model = Master
        fields = ['specialization', 'experience_years']


class ServiceFilter(django_filters.FilterSet):
    """Фильтр для модели Service"""
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    
    class Meta:
        model = Service
        fields = ['title', 'price']


class ReviewFilter(django_filters.FilterSet):
    """Фильтр для модели Review"""
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    master = django_filters.NumberFilter(field_name='master__master_id')
    
    class Meta:
        model = Review
        fields = ['rating', 'master']

