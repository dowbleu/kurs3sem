from django.contrib import admin
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.urls import reverse
from simple_history.admin import SimpleHistoryAdmin
from .models import User, Service, Master, Image, MasterService, Booking, Review, ChangeHistory


# Ресурсы для экспорта
class BookingResource(resources.ModelResource):
    """Кастомный ресурс для экспорта Booking с дополнительными методами"""
    
    # Кастомные поля для экспорта
    status_display = resources.Field(attribute='status', column_name='Статус (текст)')
    user_name = resources.Field(attribute='user__name', column_name='Имя клиента')
    master_name = resources.Field(attribute='master__full_name', column_name='Имя мастера')
    
    class Meta:
        model = Booking
        fields = ('booking_id', 'user__name', 'user__email', 'master__full_name', 
                 'service__title', 'appointment_datetime', 'status', 'created_at')
        export_order = ('booking_id', 'user__name', 'user__email', 'master__full_name',
                       'service__title', 'appointment_datetime', 'status', 'created_at')
    
    def get_export_queryset(self):
        """Кастомизация queryset для экспорта - исключаем отмененные записи"""
        queryset = super().get_export_queryset()
        # Можно добавить фильтрацию, например, только активные записи
        return queryset.exclude(status='cancelled')
    
    def dehydrate_status(self, booking):
        """Кастомизация поля status при экспорте - добавляем текстовое представление"""
        status_dict = {
            'pending': 'В ожидании',
            'confirmed': 'Подтверждена',
            'completed': 'Завершена',
            'cancelled': 'Отменена'
        }
        return status_dict.get(booking.status, booking.status)
    
    def dehydrate_appointment_datetime(self, booking):
        """Кастомизация поля appointment_datetime - форматируем дату"""
        if booking.appointment_datetime:
            return booking.appointment_datetime.strftime('%d.%m.%Y %H:%M')
        return ''
    
    def get_booking_id(self, booking):
        """Кастомный метод для получения booking_id с префиксом"""
        return f"BK-{booking.booking_id}"


class MasterResource(resources.ModelResource):
    """Ресурс для экспорта Master"""
    class Meta:
        model = Master
        fields = ('master_id', 'full_name', 'specialization', 'experience_years', 'created_at')
        export_order = ('master_id', 'full_name', 'specialization', 'experience_years', 'created_at')


class ServiceResource(resources.ModelResource):
    """Ресурс для экспорта Service"""
    class Meta:
        model = Service
        fields = ('service_id', 'title', 'description', 'price', 'created_at', 'updated_at')
        export_order = ('service_id', 'title', 'description', 'price', 'created_at', 'updated_at')
    
    def dehydrate_price(self, service):
        """Кастомизация поля price - добавляем валюту"""
        return f"{service.price} руб."


class UserResource(resources.ModelResource):
    """Ресурс для экспорта User"""
    class Meta:
        model = User
        fields = ('user_id', 'name', 'email', 'role', 'created_at')
        export_order = ('user_id', 'name', 'email', 'role', 'created_at')
    
    def dehydrate_role(self, user):
        """Кастомизация поля role - текстовое представление"""
        return user.get_role_display()


class ReviewResource(resources.ModelResource):
    """Ресурс для экспорта Review"""
    class Meta:
        model = Review
        fields = ('review_id', 'user__name', 'master__full_name', 'rating', 'comment', 'created_at')
        export_order = ('review_id', 'user__name', 'master__full_name', 'rating', 'comment', 'created_at')
    
    def dehydrate_rating(self, review):
        """Кастомизация поля rating - добавляем звездочки"""
        return f"{review.rating}/5"


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    """Административная панель для модели Image"""
    list_display = ('image_id', 'file_path', 'uploaded_at', 'get_file_info')
    list_display_links = ('image_id', 'file_path')
    list_filter = ('uploaded_at',)
    search_fields = ('file_path',)
    readonly_fields = ('image_id', 'uploaded_at')
    date_hierarchy = 'uploaded_at'
    
    @admin.display(description='Информация о файле')
    def get_file_info(self, obj):
        """Собственный метод для отображения в list_display"""
        if obj.file_path:
            filename = obj.file_path.name.split('/')[-1] if '/' in obj.file_path.name else obj.file_path.name
            url = obj.file_path.url if hasattr(obj.file_path, 'url') else f'/media/{obj.file_path.name}'
            return format_html(
                '<span style="color: green;">✓</span> <a href="{}" target="_blank">{}</a>',
                url,
                filename
            )
        return '-'
    get_file_info.short_description = 'Информация о файле'


class MasterServiceInline(admin.TabularInline):
    """Inline для связи мастер-услуга"""
    model = MasterService
    extra = 1
    raw_id_fields = ('master', 'service')


@admin.register(Service)
class ServiceAdmin(ImportExportModelAdmin):
    """Административная панель для модели Service"""
    resource_class = ServiceResource
    list_display = ('service_id', 'title', 'price', 'created_at', 'updated_at', 'get_price_display', 'get_master_link')
    list_display_links = ('service_id', 'title')
    list_filter = ('created_at', 'updated_at', 'price')
    search_fields = ('title', 'description')
    readonly_fields = ('service_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    filter_horizontal = ('related_services',)
    inlines = [MasterServiceInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'price')
        }),
        ('Связанные услуги', {
            'fields': ('related_services',),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('service_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Цена с валютой', ordering='price')
    def get_price_display(self, obj):
        """Собственный метод для отображения цены"""
        return f"{obj.price} руб."
    get_price_display.short_description = 'Цена'
    
    @admin.display(description='Мастера')
    def get_master_link(self, obj):
        """Гиперссылка на мастеров, предоставляющих эту услугу"""
        masters = obj.masters.all()[:3]
        if masters:
            links = []
            for master in masters:
                url = reverse('admin:salon_master_change', args=[master.pk])
                links.append(f'<a href="{url}">{master.full_name}</a>')
            return format_html(', '.join(links))
        return '-'
    get_master_link.short_description = 'Мастера'


@admin.register(Master)
class MasterAdmin(ImportExportModelAdmin):
    """Административная панель для модели Master"""
    resource_class = MasterResource
    list_display = (
        'master_id',
        'full_name',
        'specialization',
        'experience_years',
        'get_image_link',
        'created_at',
        'get_experience_info',
        'get_bookings_count'
    )
    list_display_links = ('master_id', 'full_name')
    list_filter = ('specialization', 'experience_years', 'created_at', 'updated_at')
    search_fields = ('full_name', 'specialization')
    readonly_fields = ('master_id', 'created_at', 'updated_at')
    raw_id_fields = ('image',)
    date_hierarchy = 'created_at'
    inlines = [MasterServiceInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('full_name', 'specialization', 'experience_years', 'image')
        }),
        ('Системная информация', {
            'fields': ('master_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Изображение')
    def get_image_link(self, obj):
        """Гиперссылка на изображение"""
        if obj.image and obj.image.file_path:
            admin_url = reverse('admin:salon_image_change', args=[obj.image.pk])
            image_url = obj.image.file_path.url if hasattr(obj.image.file_path, 'url') else f'/media/{obj.image.file_path.name}'
            return format_html(
                '<a href="{}">Изображение #{}</a><br><a href="{}" target="_blank" style="font-size: 0.85rem; color: #6c757d;">Просмотр</a>',
                admin_url,
                obj.image.image_id,
                image_url
            )
        return '-'
    get_image_link.short_description = 'Изображение'
    
    @admin.display(description='Количество записей')
    def get_bookings_count(self, obj):
        """Количество записей к мастеру"""
        count = obj.bookings.count()
        if count > 0:
            url = reverse('admin:salon_booking_changelist') + f'?master__id__exact={obj.pk}'
            return format_html('<a href="{}">{} записей</a>', url, count)
        return '0'
    get_bookings_count.short_description = 'Записи'
    
    @admin.display(description='Опыт работы')
    def get_experience_info(self, obj):
        """Собственный метод для отображения опыта работы"""
        if obj.experience_years >= 5:
            color = 'green'
            icon = '⭐'
        elif obj.experience_years >= 3:
            color = 'orange'
            icon = '✓'
        else:
            color = 'blue'
            icon = '•'
        return format_html(
            '<span style="color: {};">{} {} лет</span>',
            color,
            icon,
            obj.experience_years
        )
    get_experience_info.short_description = 'Опыт работы'


@admin.register(MasterService)
class MasterServiceAdmin(admin.ModelAdmin):
    """Административная панель для модели MasterService"""
    list_display = ('master_service_id', 'master', 'service', 'get_master_specialization')
    list_display_links = ('master_service_id',)
    list_filter = ('master', 'service')
    search_fields = ('master__full_name', 'service__title')
    raw_id_fields = ('master', 'service')
    
    @admin.display(description='Специализация мастера')
    def get_master_specialization(self, obj):
        """Собственный метод для отображения специализации"""
        return obj.master.specialization
    get_master_specialization.short_description = 'Специализация'


@admin.register(User)
class UserAdmin(ImportExportModelAdmin):
    """Административная панель для модели User"""
    resource_class = UserResource
    list_display = ('user_id', 'name', 'email', 'role', 'created_at', 'get_role_display_custom')
    list_display_links = ('user_id', 'name')
    list_filter = ('role', 'created_at')
    search_fields = ('name', 'email')
    readonly_fields = ('user_id', 'created_at')
    date_hierarchy = 'created_at'
    
    @admin.display(description='Роль (отформатированная)')
    def get_role_display_custom(self, obj):
        """Собственный метод для отображения роли"""
        if obj.role == 'admin':
            return format_html('<span style="color: red; font-weight: bold;">👑 {}</span>', obj.get_role_display())
        return format_html('<span style="color: blue;">👤 {}</span>', obj.get_role_display())
    get_role_display_custom.short_description = 'Роль'


@admin.register(Booking)
class BookingAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    """Административная панель для модели Booking"""
    resource_class = BookingResource
    list_display = (
        'booking_id',
        'get_user_link',
        'get_master_link',
        'get_service_link',
        'appointment_datetime',
        'status',
        'created_at',
        'get_status_display_custom'
    )
    list_display_links = ('booking_id',)
    list_filter = ('status', 'appointment_datetime', 'created_at', 'master', 'service')
    search_fields = ('user__name', 'user__email', 'master__full_name', 'service__title')
    readonly_fields = ('booking_id', 'created_at')
    raw_id_fields = ('user', 'master', 'service')
    date_hierarchy = 'appointment_datetime'
    fieldsets = (
        ('Информация о записи', {
            'fields': ('user', 'master', 'service', 'appointment_datetime', 'status')
        }),
        ('Системная информация', {
            'fields': ('booking_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Пользователь')
    def get_user_link(self, obj):
        """Гиперссылка на пользователя"""
        url = reverse('admin:salon_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.name)
    get_user_link.short_description = 'Пользователь'
    
    @admin.display(description='Мастер')
    def get_master_link(self, obj):
        """Гиперссылка на мастера"""
        url = reverse('admin:salon_master_change', args=[obj.master.pk])
        return format_html('<a href="{}">{}</a>', url, obj.master.full_name)
    get_master_link.short_description = 'Мастер'
    
    @admin.display(description='Услуга')
    def get_service_link(self, obj):
        """Гиперссылка на услугу"""
        url = reverse('admin:salon_service_change', args=[obj.service.pk])
        return format_html('<a href="{}">{}</a>', url, obj.service.title)
    get_service_link.short_description = 'Услуга'
    
    @admin.display(description='Статус (цветной)')
    def get_status_display_custom(self, obj):
        """Собственный метод для отображения статуса с цветом"""
        colors = {
            'pending': 'orange',
            'confirmed': 'green',
            'completed': 'blue',
            'cancelled': 'red',
        }
        icons = {
            'pending': '⏳',
            'confirmed': '✓',
            'completed': '✅',
            'cancelled': '❌',
        }
        color = colors.get(obj.status, 'black')
        icon = icons.get(obj.status, '•')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    get_status_display_custom.short_description = 'Статус'


@admin.register(Review)
class ReviewAdmin(ImportExportModelAdmin):
    """Административная панель для модели Review"""
    resource_class = ReviewResource
    list_display = (
        'review_id',
        'user',
        'master',
        'rating',
        'created_at',
        'get_rating_stars',
        'get_comment_preview'
    )
    list_display_links = ('review_id', 'user')
    list_filter = ('rating', 'created_at', 'master')
    search_fields = ('user__name', 'user__email', 'master__full_name', 'comment')
    readonly_fields = ('review_id', 'created_at')
    raw_id_fields = ('user', 'master')
    date_hierarchy = 'created_at'
    
    @admin.display(description='Рейтинг (звезды)')
    def get_rating_stars(self, obj):
        """Собственный метод для отображения рейтинга звездами"""
        stars = '⭐' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color: gold; font-size: 14px;">{}</span> <strong>({}/5)</strong>',
            stars,
            obj.rating
        )
    get_rating_stars.short_description = 'Рейтинг'
    
    @admin.display(description='Превью комментария')
    def get_comment_preview(self, obj):
        """Собственный метод для отображения превью комментария"""
        if obj.comment:
            preview = obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
            return format_html('<span title="{}">{}</span>', obj.comment, preview)
        return '-'
    get_comment_preview.short_description = 'Комментарий'


@admin.register(ChangeHistory)
class ChangeHistoryAdmin(admin.ModelAdmin):
    """Административная панель для истории изменений"""
    list_display = ('id', 'content_type', 'object_id', 'action', 'changed_by', 'timestamp', 'get_object_link')
    list_filter = ('action', 'timestamp', 'content_type')
    search_fields = ('changed_by',)
    readonly_fields = ('content_type', 'object_id', 'action', 'changed_by', 'changes', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def get_object_link(self, obj):
        """Гиперссылка на объект"""
        try:
            model = obj.content_type.model_class()
            admin_url = reverse(f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change', args=[obj.object_id])
            return format_html('<a href="{}">{}</a>', admin_url, str(obj.content_object))
        except:
            return str(obj.content_object)
    get_object_link.short_description = 'Объект'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
