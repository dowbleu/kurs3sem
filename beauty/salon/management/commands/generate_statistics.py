from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from salon.models import Booking, Master, Service, User


class Command(BaseCommand):
    help = 'Генерирует статистику по салону красоты'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='console',
            choices=['console', 'json'],
            help='Формат вывода статистики',
        )

    def handle(self, *args, **options):
        """Выполнение команды"""
        output_format = options['format']
        
        stats = self.collect_statistics()
        
        if output_format == 'json':
            self.stdout.write(self.style.SUCCESS('Статистика в формате JSON:'))
            import json
            self.stdout.write(json.dumps(stats, indent=2, ensure_ascii=False, default=str))
        else:
            self.print_console_statistics(stats)

    def collect_statistics(self):
        """Сбор статистики"""
        stats = {}
        
        # Статистика по записям
        stats['bookings'] = {
            'total': Booking.objects.count(),
            'by_status': dict(Booking.objects.values('status').annotate(count=Count('status')).values_list('status', 'count')),
            'pending': Booking.objects.filter(status='pending').count(),
            'confirmed': Booking.objects.filter(status='confirmed').count(),
            'completed': Booking.objects.filter(status='completed').count(),
            'cancelled': Booking.objects.filter(status='cancelled').count(),
        }
        
        # Статистика по мастерам
        stats['masters'] = {
            'total': Master.objects.count(),
            'with_bookings': Master.objects.annotate(booking_count=Count('bookings')).filter(booking_count__gt=0).count(),
            'average_experience': Master.objects.aggregate(avg=Avg('experience_years'))['avg'] or 0,
            'experienced_masters': Master.objects.filter(experience_years__gte=5).count(),
        }
        
        # Статистика по услугам
        stats['services'] = {
            'total': Service.objects.count(),
            'average_price': float(Service.objects.aggregate(avg=Avg('price'))['avg'] or 0),
            'most_popular': list(Service.objects.annotate(booking_count=Count('bookings'))
                                .order_by('-booking_count')[:5]
                                .values('title', 'booking_count')),
        }
        
        # Статистика по пользователям
        stats['users'] = {
            'total': User.objects.count(),
            'clients': User.objects.filter(role='client').count(),
            'admins': User.objects.filter(role='admin').count(),
            'with_bookings': User.objects.annotate(booking_count=Count('bookings')).filter(booking_count__gt=0).count(),
        }
        
        # Статистика за последние 30 дней
        thirty_days_ago = timezone.now() - timedelta(days=30)
        stats['last_30_days'] = {
            'new_bookings': Booking.objects.filter(created_at__gte=thirty_days_ago).count(),
            'new_users': User.objects.filter(created_at__gte=thirty_days_ago).count(),
        }
        
        # Сложный Q-запрос: записи в ближайшие 7 дней
        future_date = timezone.now() + timedelta(days=7)
        stats['upcoming'] = {
            'next_7_days': Booking.objects.filter(
                Q(appointment_datetime__gte=timezone.now()) &
                Q(appointment_datetime__lte=future_date) &
                Q(status__in=['pending', 'confirmed'])
            ).count(),
        }
        
        return stats

    def print_console_statistics(self, stats):
        """Вывод статистики в консоль"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('СТАТИСТИКА САЛОНА КРАСОТЫ'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        # Записи
        self.stdout.write(self.style.WARNING('ЗАПИСИ:'))
        self.stdout.write(f"  Всего записей: {stats['bookings']['total']}")
        self.stdout.write(f"  Ожидают подтверждения: {stats['bookings']['pending']}")
        self.stdout.write(f"  Подтверждены: {stats['bookings']['confirmed']}")
        self.stdout.write(f"  Завершены: {stats['bookings']['completed']}")
        self.stdout.write(f"  Отменены: {stats['bookings']['cancelled']}")
        
        # Мастера
        self.stdout.write(self.style.WARNING('\nМАСТЕРА:'))
        self.stdout.write(f"  Всего мастеров: {stats['masters']['total']}")
        self.stdout.write(f"  С записями: {stats['masters']['with_bookings']}")
        self.stdout.write(f"  Средний опыт: {stats['masters']['average_experience']:.1f} лет")
        self.stdout.write(f"  Опытные (5+ лет): {stats['masters']['experienced_masters']}")
        
        # Услуги
        self.stdout.write(self.style.WARNING('\nУСЛУГИ:'))
        self.stdout.write(f"  Всего услуг: {stats['services']['total']}")
        self.stdout.write(f"  Средняя цена: {stats['services']['average_price']:.2f} руб.")
        self.stdout.write("  Самые популярные услуги:")
        for service in stats['services']['most_popular']:
            self.stdout.write(f"    - {service['title']}: {service['booking_count']} записей")
        
        # Пользователи
        self.stdout.write(self.style.WARNING('\nПОЛЬЗОВАТЕЛИ:'))
        self.stdout.write(f"  Всего пользователей: {stats['users']['total']}")
        self.stdout.write(f"  Клиентов: {stats['users']['clients']}")
        self.stdout.write(f"  Администраторов: {stats['users']['admins']}")
        self.stdout.write(f"  С записями: {stats['users']['with_bookings']}")
        
        # Последние 30 дней
        self.stdout.write(self.style.WARNING('\nПОСЛЕДНИЕ 30 ДНЕЙ:'))
        self.stdout.write(f"  Новых записей: {stats['last_30_days']['new_bookings']}")
        self.stdout.write(f"  Новых пользователей: {stats['last_30_days']['new_users']}")
        
        # Ближайшие записи
        self.stdout.write(self.style.WARNING('\nБЛИЖАЙШИЕ ЗАПИСИ:'))
        self.stdout.write(f"  Записей на ближайшие 7 дней: {stats['upcoming']['next_7_days']}")
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60 + '\n'))

