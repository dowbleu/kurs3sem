from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User as DjangoUser
from .models import Booking, User, Master, Service


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=150, required=True, label='Имя')
    
    class Meta:
        model = DjangoUser
        fields = ('username', 'first_name', 'email', 'password1', 'password2')
        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'email': 'Email',
        }
    
    def clean_email(self):
        """Валидация email: проверка уникальности"""
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    "Пользователь с таким email уже зарегистрирован. Используйте другой email или войдите в систему."
                )
                
            if DjangoUser.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    "Пользователь с таким email уже зарегистрирован. Используйте другой email или войдите в систему."
                )
        return email
    
    def clean_first_name(self):
        """Валидация имени: проверка на пустоту и минимальную длину"""
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = first_name.strip()
            if len(first_name) < 2:
                raise forms.ValidationError(
                    "Имя должно содержать минимум 2 символа."
                )
            if not first_name.replace(' ', '').replace('-', '').isalpha():
                raise forms.ValidationError(
                    "Имя может содержать только буквы, пробелы и дефисы."
                )
        return first_name
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        if commit:
            user.save()
            # Создаем запись в модели User
            User.objects.create(
                name=user.first_name,
                email=user.email,
                role='client'
            )
        return user


class BookingForm(forms.ModelForm):
    """Форма для создания и редактирования записи"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Если пользователь не админ, скрываем поле статуса
        if self.user and not self.user.is_staff:
            if 'status' in self.fields:
                del self.fields['status']
        
        # Если пользователь авторизован, автоматически выбираем его из модели User
        if self.user and self.user.is_authenticated:
            try:
                salon_user = User.objects.get(email=self.user.email)
                self.fields['user'].initial = salon_user
                # Делаем поле скрытым для обычных пользователей, видимым только для админов
                if not self.user.is_staff:
                    self.fields['user'].widget = forms.HiddenInput()
            except User.DoesNotExist:
                # Если пользователь не найден в модели User, скрываем поле для обычных пользователей
                if not self.user.is_staff:
                    self.fields['user'].widget = forms.HiddenInput()
    
    class Meta:
        model = Booking
        fields = ['user', 'master', 'service', 'appointment_datetime', 'status']
        widgets = {
            'appointment_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            'user': forms.Select(attrs={'class': 'form-control'}),
            'master': forms.Select(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'user': 'Пользователь',
            'master': 'Мастер',
            'service': 'Услуга',
            'appointment_datetime': 'Дата и время записи',
            'status': 'Статус',
        }
    
    def clean_appointment_datetime(self):
        """Валидация: дата записи должна быть в будущем"""
        from django.utils import timezone
        appointment_datetime = self.cleaned_data.get('appointment_datetime')
        
        if appointment_datetime:
            # Если datetime naive (без timezone), делаем его aware
            if timezone.is_naive(appointment_datetime):
                appointment_datetime = timezone.make_aware(appointment_datetime)
            
            now = timezone.now()
            # Сравниваем с учетом timezone
            if appointment_datetime <= now:
                raise forms.ValidationError(
                    "Дата и время записи должны быть в будущем. Выберите дату позже текущего момента."
                )
        return appointment_datetime


class BookingStatusUpdateForm(forms.ModelForm):
    """Форма для изменения статуса записи (только для админа)"""
    
    class Meta:
        model = Booking
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'status': 'Статус',
        }
