from rest_framework import serializers
from .models import Booking, Master, Service, User, Review
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели User"""
    
    class Meta:
        model = User
        fields = ['user_id', 'name', 'email', 'role', 'created_at']
        read_only_fields = ['user_id', 'created_at']


class ServiceSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Service"""
    
    class Meta:
        model = Service
        fields = ['service_id', 'title', 'description', 'price', 'created_at', 'updated_at']
        read_only_fields = ['service_id', 'created_at', 'updated_at']


class MasterSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Master"""
    specialization_display = serializers.CharField(source='get_specialization_display', read_only=True)
    
    class Meta:
        model = Master
        fields = [
            'master_id', 'full_name', 'specialization', 'specialization_display',
            'experience_years', 'image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['master_id', 'created_at', 'updated_at']


class BookingSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Booking с валидацией"""
    user_detail = UserSerializer(source='user', read_only=True)
    master_detail = MasterSerializer(source='master', read_only=True)
    service_detail = ServiceSerializer(source='service', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'booking_id', 'user', 'user_detail', 'master', 'master_detail',
            'service', 'service_detail', 'appointment_datetime', 'status',
            'status_display', 'created_at'
        ]
        read_only_fields = ['booking_id', 'created_at']
    
    def validate_appointment_datetime(self, value):
        """Валидация: дата записи должна быть в будущем"""
        now = timezone.now()
        # Сравниваем с учетом timezone
        if value <= now:
            raise serializers.ValidationError(
                "Дата и время записи должны быть в будущем. Выберите дату позже текущего момента."
            )
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Review (без валидации, так как не используется на сайте)"""
    user_detail = UserSerializer(source='user', read_only=True)
    master_detail = MasterSerializer(source='master', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'review_id', 'user', 'user_detail', 'master', 'master_detail',
            'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['review_id', 'created_at']
