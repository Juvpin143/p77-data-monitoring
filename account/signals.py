from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Station

@receiver(post_save, sender=CustomUser)
def create_user_station(sender, instance, created, **kwargs):
    if created and not instance.station:
        station = Station.objects.create(
            name=f"Station {instance.username}"
        )
        instance.station = station
        instance.save()