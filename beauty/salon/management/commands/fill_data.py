from django.core.management.base import BaseCommand
from django.core.files import File
from salon.models import Master, Service, Image, MasterService
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Заполняет базу данных мастерами и услугами'

    def handle(self, *args, **options):
        """Заполнение данных"""
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
        
        # Очистка существующих данных (опционально)
        self.stdout.write('Очистка старых данных...')
        MasterService.objects.all().delete()
        Master.objects.all().delete()
        Service.objects.all().delete()
        Image.objects.all().delete()
        
        # Создание изображений
        self.stdout.write('Создание изображений...')
        
        # Проверяем, есть ли уже изображения в media/images
        media_images_dir = BASE_DIR / 'media' / 'images'
        georgiy_media = media_images_dir / 'georgiy.png'
        maria_media = media_images_dir / 'maria.png'
        
        # Также проверяем исходные файлы (если они еще есть)
        georgiy_source = BASE_DIR / 'img' / 'георгий.png'
        maria_source = BASE_DIR / 'img' / 'мария.png'
        
        image_georgiy = None
        image_maria = None
        
        # Загружаем georgiy.png
        if georgiy_media.exists():
            img = Image()
            with open(georgiy_media, 'rb') as f:
                img.file_path.save('georgiy.png', File(f), save=True)
            image_georgiy = img
            self.stdout.write(self.style.SUCCESS('✓ Изображение georgiy.png загружено из media/images'))
        elif georgiy_source.exists():
            img = Image()
            with open(georgiy_source, 'rb') as f:
                img.file_path.save('georgiy.png', File(f), save=True)
            image_georgiy = img
            self.stdout.write(self.style.SUCCESS('✓ Изображение георгий.png загружено из img'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Файл georgiy.png не найден'))
        
        # Загружаем maria.png
        if maria_media.exists():
            img = Image()
            with open(maria_media, 'rb') as f:
                img.file_path.save('maria.png', File(f), save=True)
            image_maria = img
            self.stdout.write(self.style.SUCCESS('✓ Изображение maria.png загружено из media/images'))
        elif maria_source.exists():
            img = Image()
            with open(maria_source, 'rb') as f:
                img.file_path.save('maria.png', File(f), save=True)
            image_maria = img
            self.stdout.write(self.style.SUCCESS('✓ Изображение мария.png загружено из img'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Файл maria.png не найден'))
        
        # Создание услуг
        self.stdout.write('Создание услуг...')
        services_data = [
            {'title': 'Стрижка женская', 'description': 'Профессиональная стрижка волос для женщин с укладкой', 'price': 2500},
            {'title': 'Стрижка мужская', 'description': 'Классическая и современная стрижка для мужчин', 'price': 1200},
            {'title': 'Окрашивание волос', 'description': 'Полное окрашивание волос с использованием профессиональных красок', 'price': 4500},
            {'title': 'Мелирование', 'description': 'Мелирование волос с использованием техники балаяж', 'price': 5500},
            {'title': 'Омбре', 'description': 'Создание эффекта омбре на волосах', 'price': 6000},
            {'title': 'Укладка волос', 'description': 'Профессиональная укладка волос на любой случай', 'price': 1800},
            {'title': 'Химическая завивка', 'description': 'Долговременная химическая завивка волос', 'price': 5000},
            {'title': 'Ламинирование волос', 'description': 'Ламинирование для блеска и гладкости волос', 'price': 3500},
            {'title': 'Кератиновое выпрямление', 'description': 'Выпрямление и восстановление волос кератином', 'price': 7000},
            {'title': 'Мужская борода', 'description': 'Стрижка и укладка бороды', 'price': 1500},
            {'title': 'Бритье головы', 'description': 'Профессиональное бритье головы', 'price': 1000},
            {'title': 'Детская стрижка', 'description': 'Стрижка для детей с игровой атмосферой', 'price': 1000},
            {'title': 'Свадебная прическа', 'description': 'Эксклюзивная прическа для свадьбы', 'price': 8000},
            {'title': 'Вечерняя прическа', 'description': 'Элегантная прическа для особого случая', 'price': 4000},
            {'title': 'Тонирование волос', 'description': 'Тонирование для обновления цвета', 'price': 2000},
        ]
        
        services = []
        for service_data in services_data:
            service = Service.objects.create(**service_data)
            services.append(service)
            self.stdout.write(self.style.SUCCESS(f'✓ Создана услуга: {service.title}'))
        
        # Создание мастеров
        self.stdout.write('Создание мастеров...')
        masters_data = [
            # Мужские имена
            {'full_name': 'Георгий Петров', 'specialization': 'Мужские стрижки и бритье', 'experience_years': 8, 'image': image_georgiy, 'gender': 'male'},
            {'full_name': 'Александр Смирнов', 'specialization': 'Классические мужские стрижки', 'experience_years': 12, 'image': image_georgiy, 'gender': 'male'},
            {'full_name': 'Дмитрий Иванов', 'specialization': 'Современные мужские стрижки', 'experience_years': 6, 'image': image_georgiy, 'gender': 'male'},
            {'full_name': 'Максим Козлов', 'specialization': 'Борода и усы', 'experience_years': 5, 'image': image_georgiy, 'gender': 'male'},
            # Женские имена
            {'full_name': 'Мария Волкова', 'specialization': 'Женские стрижки и укладки', 'experience_years': 10, 'image': image_maria, 'gender': 'female'},
            {'full_name': 'Анна Соколова', 'specialization': 'Окрашивание и мелирование', 'experience_years': 15, 'image': image_maria, 'gender': 'female'},
            {'full_name': 'Елена Новикова', 'specialization': 'Свадебные и вечерние прически', 'experience_years': 9, 'image': image_maria, 'gender': 'female'},
            {'full_name': 'Ольга Морозова', 'specialization': 'Ламинирование и кератин', 'experience_years': 7, 'image': image_maria, 'gender': 'female'},
            {'full_name': 'Татьяна Лебедева', 'specialization': 'Омбре и балаяж', 'experience_years': 11, 'image': image_maria, 'gender': 'female'},
            {'full_name': 'Наталья Ковалева', 'specialization': 'Детские стрижки', 'experience_years': 6, 'image': image_maria, 'gender': 'female'},
        ]
        
        masters = []
        for master_data in masters_data:
            image = master_data.pop('image')
            gender = master_data.pop('gender')
            master = Master.objects.create(**master_data, image=image)
            masters.append(master)
            self.stdout.write(self.style.SUCCESS(f'✓ Создан мастер: {master.full_name}'))
        
        # Связывание мастеров с услугами
        self.stdout.write('Связывание мастеров с услугами...')
        
        # Мужские мастера - мужские услуги
        male_masters = [m for m in masters if 'Петров' in m.full_name or 'Смирнов' in m.full_name or 'Иванов' in m.full_name or 'Козлов' in m.full_name]
        male_services = [s for s in services if 'мужск' in s.title.lower() or 'борода' in s.title.lower() or 'бритье' in s.title.lower()]
        for master in male_masters:
            for service in male_services:
                MasterService.objects.get_or_create(master=master, service=service)
        
        # Женские мастера - женские услуги
        female_masters = [m for m in masters if 'Волкова' in m.full_name or 'Соколова' in m.full_name or 'Новикова' in m.full_name or 'Морозова' in m.full_name or 'Лебедева' in m.full_name or 'Ковалева' in m.full_name]
        female_services = [s for s in services if 'женск' in s.title.lower() or 'окрашивание' in s.title.lower() or 'мелирование' in s.title.lower() or 'омбре' in s.title.lower() or 'укладка' in s.title.lower() or 'завивка' in s.title.lower() or 'ламинирование' in s.title.lower() or 'кератин' in s.title.lower() or 'свадебн' in s.title.lower() or 'вечерн' in s.title.lower() or 'тонирование' in s.title.lower()]
        for master in female_masters:
            for service in female_services:
                MasterService.objects.get_or_create(master=master, service=service)
        
        # Универсальные услуги для всех
        universal_services = [s for s in services if 'детск' in s.title.lower()]
        for master in masters:
            for service in universal_services:
                MasterService.objects.get_or_create(master=master, service=service)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Создано связей мастер-услуга: {MasterService.objects.count()}'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Данные успешно заполнены!'))
        self.stdout.write(f'Создано мастеров: {len(masters)}')
        self.stdout.write(f'Создано услуг: {len(services)}')

