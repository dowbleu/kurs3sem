from rest_framework import serializers
from .models import Booking, Master, Service, User, Review


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
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Дата записи должна быть в будущем.")
        return value
    
    def validate(self, data):
        """Валидация на уровне всего объекта"""
        appointment_datetime = data.get('appointment_datetime')
        status = data.get('status', self.instance.status if self.instance else 'pending')
        
        # Проверка: нельзя создавать запись с завершенным статусом
        if status == 'completed' and not self.instance:
            raise serializers.ValidationError({
                'status': 'Нельзя создавать запись сразу с статусом "Завершена".'
            })
        
        return data


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Review с валидацией"""
    user_detail = UserSerializer(source='user', read_only=True)
    master_detail = MasterSerializer(source='master', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'review_id', 'user', 'user_detail', 'master', 'master_detail',
            'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['review_id', 'created_at']
    
    def validate_rating(self, value):
        """Валидация рейтинга: должен быть от 1 до 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Рейтинг должен быть от 1 до 5.")
        return value
    
    def validate_comment(self, value):
        """Валидация комментария: минимальная длина"""
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("Комментарий должен содержать минимум 10 символов.")
        return value

