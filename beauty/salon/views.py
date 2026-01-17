from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from .models import Booking, User, Master
from .forms import BookingForm, CustomUserCreationForm, BookingStatusUpdateForm


def is_admin(user):
    """Проверка, является ли пользователь админом"""
    return user.is_authenticated and user.is_staff


def home(request):
    """Главная страница"""
    return render(request, 'salon/home.html')


def register_view(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            django_user = form.save()
            login(request, django_user)
            messages.success(request, 'Регистрация успешна! Добро пожаловать!')
            return redirect('salon:booking_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'salon/register.html', {'form': form})


def login_view(request):
    """Вход пользователя"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name or user.username}!')
            return redirect('salon:booking_list')
    else:
        form = AuthenticationForm()
    return render(request, 'salon/login.html', {'form': form})


def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('salon:booking_list')


class BookingListView(ListView):
    """Просмотр списка всех записей"""
    model = Booking
    template_name = 'salon/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Booking.objects.select_related('user', 'master', 'service').order_by('-appointment_datetime')
        # Обычные пользователи видят только свои записи
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            try:
                salon_user = User.objects.get(email=self.request.user.email)
                queryset = queryset.filter(user=salon_user)
            except User.DoesNotExist:
                queryset = Booking.objects.none()
        # Неавторизованные пользователи видят все записи (или можно вернуть пустой queryset)
        return queryset


class BookingDetailView(DetailView):
    """Просмотр детальной информации о записи"""
    model = Booking
    template_name = 'salon/booking_detail.html'
    context_object_name = 'booking'
    
    def get_queryset(self):
        queryset = Booking.objects.select_related('user', 'master', 'service')
        # Обычные пользователи могут видеть только свои записи
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            try:
                salon_user = User.objects.get(email=self.request.user.email)
                queryset = queryset.filter(user=salon_user)
            except User.DoesNotExist:
                queryset = Booking.objects.none()
        return queryset


class BookingCreateView(LoginRequiredMixin, CreateView):
    """Добавление новой записи (требуется авторизация)"""
    model = Booking
    form_class = BookingForm
    template_name = 'salon/booking_form.html'
    success_url = reverse_lazy('salon:booking_list')
    login_url = reverse_lazy('salon:login')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Для обычных пользователей автоматически устанавливаем пользователя из модели User
        if not self.request.user.is_staff:
            try:
                salon_user = User.objects.get(email=self.request.user.email)
                form.instance.user = salon_user
            except User.DoesNotExist:
                messages.error(self.request, 'Ошибка: пользователь не найден в системе')
                return redirect('salon:booking_create')
            # Устанавливаем статус по умолчанию для обычных пользователей
            form.instance.status = 'pending'
        else:
            # Для админов используем выбранного пользователя или устанавливаем из формы
            if not form.cleaned_data.get('user'):
                try:
                    salon_user = User.objects.get(email=self.request.user.email)
                    form.instance.user = salon_user
                except User.DoesNotExist:
                    pass
        
        messages.success(self.request, 'Запись успешно создана! Ожидайте подтверждения администратора.')
        return super().form_valid(form)


class BookingUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование существующей записи"""
    model = Booking
    form_class = BookingForm
    template_name = 'salon/booking_form.html'
    success_url = reverse_lazy('salon:booking_list')
    login_url = reverse_lazy('salon:login')
    
    def get_queryset(self):
        queryset = Booking.objects.select_related('user', 'master', 'service')
        # Обычные пользователи могут редактировать только свои записи
        if not self.request.user.is_staff:
            try:
                salon_user = User.objects.get(email=self.request.user.email)
                queryset = queryset.filter(user=salon_user)
            except User.DoesNotExist:
                queryset = Booking.objects.none()
        return queryset
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Обычные пользователи не могут менять статус
        if not self.request.user.is_staff:
            form.instance.status = self.get_object().status
        messages.success(self.request, 'Запись успешно обновлена!')
        return super().form_valid(form)


class BookingDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление записи"""
    model = Booking
    template_name = 'salon/booking_confirm_delete.html'
    success_url = reverse_lazy('salon:booking_list')
    context_object_name = 'booking'
    login_url = reverse_lazy('salon:login')
    
    def get_queryset(self):
        queryset = Booking.objects.select_related('user', 'master', 'service')
        # Обычные пользователи могут удалять только свои записи
        if not self.request.user.is_staff:
            try:
                salon_user = User.objects.get(email=self.request.user.email)
                queryset = queryset.filter(user=salon_user)
            except User.DoesNotExist:
                queryset = Booking.objects.none()
        return queryset
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Запись успешно удалена!')
        return super().delete(request, *args, **kwargs)


class AdminPendingBookingsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Просмотр и управление записями в статусе "pending" для администраторов"""
    model = Booking
    template_name = 'salon/admin_pending_bookings.html'
    context_object_name = 'pending_bookings'
    paginate_by = 10
    login_url = reverse_lazy('salon:login')
    
    def test_func(self):
        """Проверка, что пользователь является администратором"""
        return self.request.user.is_staff
    
    def get_queryset(self):
        """Получаем только записи со статусом 'pending'"""
        queryset = Booking.objects.filter(status='pending').select_related(
            'user', 'master', 'service'
        ).order_by('created_at')
        
        # Фильтрация по мастеру (если указан)
        master_filter = self.request.GET.get('master')
        if master_filter:
            queryset = queryset.filter(master_id=master_filter)
        
        # Поиск по имени клиента
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(user__name__icontains=search)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Добавляем дополнительный контекст"""
        context = super().get_context_data(**kwargs)
        context['masters'] = Master.objects.all().order_by('full_name')
        context['total_pending'] = Booking.objects.filter(status='pending').count()
        return context
    
    def post(self, request, *args, **kwargs):
        """Обработка изменения статуса записи"""
        booking_id = request.POST.get('booking_id')
        new_status = request.POST.get('status')
        
        if booking_id and new_status:
            booking = get_object_or_404(Booking, pk=booking_id)
            old_status = booking.get_status_display()
            booking.status = new_status
            booking.save()
            messages.success(
                request, 
                f'Статус записи #{booking.booking_id} изменен с "{old_status}" на "{booking.get_status_display()}".'
            )
        else:
            messages.error(request, 'Ошибка: не указан ID записи или статус.')
        
        return redirect('salon:admin_pending_bookings')
