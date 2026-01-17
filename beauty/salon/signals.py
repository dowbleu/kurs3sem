from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import Booking, Master, ChangeHistory


def save_change_history(instance, action, changed_by='', old_values=None):
    """Функция для сохранения истории изменений"""
    content_type = ContentType.objects.get_for_model(instance)
    changes = {}
    
    if old_values:
        for field, old_value in old_values.items():
            new_value = getattr(instance, field, None)
            if old_value != new_value:
                changes[field] = {
                    'old': str(old_value),
                    'new': str(new_value)
                }
    
    ChangeHistory.objects.create(
        content_type=content_type,
        object_id=instance.pk,
        action=action,
        changed_by=changed_by,
        changes=changes
    )


@receiver(pre_save, sender=Booking)
def booking_pre_save(sender, instance, **kwargs):
    """Сохраняем старые значения перед обновлением"""
    if instance.pk:
        try:
            old_instance = Booking.objects.get(pk=instance.pk)
            instance._old_values = {
                'status': old_instance.status,
                'appointment_datetime': old_instance.appointment_datetime,
                'master_id': old_instance.master_id,
                'service_id': old_instance.service_id,
            }
        except Booking.DoesNotExist:
            instance._old_values = {}


@receiver(post_save, sender=Booking)
def booking_post_save(sender, instance, created, **kwargs):
    """Сохраняем историю изменений после сохранения записи"""
    action = 'created' if created else 'updated'
    old_values = getattr(instance, '_old_values', None)
    save_change_history(instance, action, old_values=old_values)


@receiver(post_delete, sender=Booking)
def booking_post_delete(sender, instance, **kwargs):
    """Сохраняем историю изменений после удаления записи"""
    save_change_history(instance, 'deleted')


@receiver(pre_save, sender=Master)
def master_pre_save(sender, instance, **kwargs):
    """Сохраняем старые значения перед обновлением"""
    if instance.pk:
        try:
            old_instance = Master.objects.get(pk=instance.pk)
            instance._old_values = {
                'full_name': old_instance.full_name,
                'specialization': old_instance.specialization,
                'experience_years': old_instance.experience_years,
            }
        except Master.DoesNotExist:
            instance._old_values = {}


@receiver(post_save, sender=Master)
def master_post_save(sender, instance, created, **kwargs):
    """Сохраняем историю изменений после сохранения мастера"""
    action = 'created' if created else 'updated'
    old_values = getattr(instance, '_old_values', None)
    save_change_history(instance, action, old_values=old_values)

