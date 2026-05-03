from django.db import models
from account.models import Station
from django.conf import settings
from datetime import date
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()

class FuelInventory(models.Model):

    FUEL_CHOICES = (
        ('Premium', 'Premium'),
        ('Diesel', 'Diesel'),
        ('ULG', 'Unleaded Gasoline'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)

    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES)

    # CM measurement from deepstick
    tank1_cm = models.IntegerField(default=0, blank=True, null=True)
    tank2_cm = models.IntegerField(default=0, blank=True, null=True)
    tank3_cm = models.IntegerField(default=0, blank=True, null=True)

    # Liters equivalent
    tank1_liters = models.IntegerField(default=0)
    tank2_liters = models.IntegerField(default=0)
    tank3_liters = models.IntegerField(default=0)

    dispatch_liters = models.FloatField(default=0)

    is_read = models.BooleanField(default=False)

    date = models.DateField(default=date.today)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.station} | {self.fuel_type} | {self.date}"

class StationDispatch(models.Model):
    station = models.ForeignKey('account.Station', on_delete=models.CASCADE)
    fuel_type = models.CharField(max_length=50)
    dispatch_liters = models.FloatField(default=0)
    dispatch_liters2 = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('station', 'fuel_type')

    def __str__(self):
        return f"{self.station} | {self.fuel_type} | {self.dispatch_liters}"

class Notification(models.Model):

    TYPE_CHOICES = (
        ('new_report', '📋 New Report Submitted'),
        ('report_read', '✅ Report Read by Admin'),
        ('report_deleted', '🗑️ Report Deleted'),
        ('assigned', '🏪 Station Assigned'),
        ('deactivated', '🔴 Account Deactivated'),
        ('activated', '🟢 Account Activated'),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notif_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} | {self.notif_type} | {self.created_at}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(default='default.jpg', upload_to='profile_pics')
    phone_number = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=50, blank=True)
    employee_id = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"

