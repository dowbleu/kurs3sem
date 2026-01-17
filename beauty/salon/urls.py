from django.urls import path
from . import views

app_name = 'salon'

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),
    
    # Авторизация
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Просмотр списка записей
    path('bookings/', views.BookingListView.as_view(), name='booking_list'),
    
    # Просмотр детальной информации о записи
    path('bookings/<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    
    # Добавление новой записи (требуется авторизация)
    path('bookings/create/', views.BookingCreateView.as_view(), name='booking_create'),
    
    # Редактирование записи (требуется авторизация)
    path('bookings/<int:pk>/update/', views.BookingUpdateView.as_view(), name='booking_update'),
    
    # Удаление записи (требуется авторизация)
    path('bookings/<int:pk>/delete/', views.BookingDeleteView.as_view(), name='booking_delete'),
    
    # Админ-панель: управление статусами записей
    path('manage/pending-bookings/', views.AdminPendingBookingsView.as_view(), name='admin_pending_bookings'),
]

