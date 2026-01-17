from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from simple_history.models import HistoricalRecords


class ChangeHistory(models.Model):
    """Модель для сохранения истории изменений объектов"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    action = models.CharField(max_length=20, choices=[
        ('created', 'Создан'),
        ('updated', 'Обновлен'),
        ('deleted', 'Удален'),
    ], verbose_name='Действие')
    changed_by = models.CharField(max_length=255, blank=True, verbose_name='Изменено пользователем')
    changes = models.JSONField(default=dict, verbose_name='Изменения')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время изменения')
    
    class Meta:
        verbose_name = 'История изменений'
        verbose_name_plural = 'История изменений'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.content_object} ({self.timestamp})"


class User(models.Model):
    """Модель пользователя"""
    ROLE_CHOICES = [
        ('client', 'Клиент'),
        ('admin', 'Администратор'),
    ]
    
    user_id = models.AutoField(primary_key=True, verbose_name='ID пользователя')
    name = models.CharField(max_length=255, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client', verbose_name='Роль')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.email})"


class Image(models.Model):
    """Модель изображения"""
    image_id = models.AutoField(primary_key=True, verbose_name='ID изображения')
    file_path = models.ImageField(upload_to='images/', verbose_name='Изображение')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    
    class Meta:
        verbose_name = 'Изображение'
        verbose_name_plural = 'Изображения'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Изображение {self.image_id}"


class Service(models.Model):
    """Модель услуги"""
    service_id = models.AutoField(primary_key=True, verbose_name='ID услуги')
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    # Дополнительное поле для демонстрации filter_horizontal
    related_services = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True,
        verbose_name='Связанные услуги'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['title']
    
    def __str__(self):
        return f"{self.title} - {self.price} руб."


class Master(models.Model):
    """Модель мастера"""
    master_id = models.AutoField(primary_key=True, verbose_name='ID мастера')
    full_name = models.CharField(max_length=255, verbose_name='Полное имя')
    specialization = models.CharField(max_length=255, verbose_name='Специализация')
    experience_years = models.PositiveIntegerField(verbose_name='Опыт работы (лет)')
    image = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='masters',
        verbose_name='Изображение'
    )
    services = models.ManyToManyField(
        Service,
        through='MasterService',
        related_name='masters',
        verbose_name='Услуги'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Мастер'
        verbose_name_plural = 'Мастера'
        ordering = ['full_name']
    
    def __str__(self):
        return f"{self.full_name} - {self.specialization}"


class MasterService(models.Model):
    """Модель связи многие-ко-многим между мастерами и услугами"""
    master_service_id = models.AutoField(primary_key=True, verbose_name='ID связи')
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name='master_services',
        verbose_name='Мастер'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='master_services',
        verbose_name='Услуга'
    )
    
    class Meta:
        verbose_name = 'Связь мастер-услуга'
        verbose_name_plural = 'Связи мастер-услуга'
        unique_together = ['master', 'service']
        ordering = ['master', 'service']
    
    def __str__(self):
        return f"{self.master.full_name} - {self.service.title}"


class Booking(models.Model):
    """Модель записи клиента"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждена'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]
    
    booking_id = models.AutoField(primary_key=True, verbose_name='ID записи')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Пользователь'
    )
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Мастер'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Услуга'
    )
    appointment_datetime = models.DateTimeField(verbose_name='Дата и время записи')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    # История изменений через django-simple-history
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['-appointment_datetime']
    
    def __str__(self):
        return f"Запись {self.user.name} к {self.master.full_name} на {self.appointment_datetime}"


class Review(models.Model):
    """Модель отзыва"""
    review_id = models.AutoField(primary_key=True, verbose_name='ID отзыва')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Пользователь'
    )
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Мастер'
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        verbose_name='Рейтинг'
    )
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Отзыв от {self.user.name} на {self.master.full_name} ({self.rating}/5)"
