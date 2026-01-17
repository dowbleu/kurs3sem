from django.core.management.base import BaseCommand
from django.core.files import File
from salon.models import Image, Master
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Исправляет пути к изображениям в базе данных'

    def handle(self, *args, **options):
        """Исправление путей"""
        # BASE_DIR указывает на beauty/ (где manage.py)
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        media_dir = BASE_DIR / 'media' / 'images'
        
        georgiy_path = media_dir / 'georgiy.png'
        maria_path = media_dir / 'maria.png'
        
        self.stdout.write('Исправление путей к изображениям...')
        
        # Удаляем все старые изображения
        Image.objects.all().delete()
        self.stdout.write('✓ Удалены старые изображения из базы данных')
        
        # Создаем новые изображения с правильными путями
        georgiy_img = None
        maria_img = None
        
        if georgiy_path.exists():
            georgiy_img = Image()
            with open(georgiy_path, 'rb') as f:
                georgiy_img.file_path.save('georgiy.png', File(f), save=True)
            self.stdout.write(self.style.SUCCESS(f'✓ Создано изображение georgiy.png'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Файл {georgiy_path} не найден'))
        
        if maria_path.exists():
            maria_img = Image()
            with open(maria_path, 'rb') as f:
                maria_img.file_path.save('maria.png', File(f), save=True)
            self.stdout.write(self.style.SUCCESS(f'✓ Создано изображение maria.png'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Файл {maria_path} не найден'))
        
        # Удаляем дубликаты изображений
        all_images = Image.objects.all()
        georgiy_img = Image.objects.filter(file_path__icontains='georgiy').first()
        maria_img = Image.objects.filter(file_path__icontains='maria').first()
        
        if georgiy_img and maria_img:
            # Удаляем все изображения кроме нужных
            images_to_delete = Image.objects.exclude(pk__in=[georgiy_img.pk, maria_img.pk])
            count = images_to_delete.count()
            images_to_delete.delete()
            if count > 0:
                self.stdout.write(self.style.SUCCESS(f'✓ Удалено {count} дубликатов изображений'))
        
        # Обновляем мастера, чтобы они использовали правильные изображения
        if georgiy_img:
            male_masters = Master.objects.filter(full_name__in=['Георгий Петров', 'Александр Смирнов', 'Дмитрий Иванов', 'Максим Козлов'])
            updated = male_masters.update(image=georgiy_img)
            if updated > 0:
                self.stdout.write(self.style.SUCCESS(f'✓ Обновлено {updated} мужских мастеров'))
        
        if maria_img:
            female_masters = Master.objects.filter(full_name__in=['Мария Волкова', 'Анна Соколова', 'Елена Новикова', 'Ольга Морозова', 'Татьяна Лебедева', 'Наталья Ковалева'])
            updated = female_masters.update(image=maria_img)
            if updated > 0:
                self.stdout.write(self.style.SUCCESS(f'✓ Обновлено {updated} женских мастеров'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Пути к изображениям исправлены!'))
        self.stdout.write(f'Все изображения находятся в: media/images/')
        self.stdout.write(f'URL для доступа: /media/images/')

