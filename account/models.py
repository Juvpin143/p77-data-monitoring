from django.contrib.auth.models import AbstractUser
from django.db import models

class Cluster(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Station(models.Model):
    cluster = models.ForeignKey(
        Cluster,
        on_delete=models.CASCADE,
        related_name='stations',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    tank_capacity = models.IntegerField(default=0, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    premium_capacity = models.IntegerField(default=0, null=True, blank=True)
    regular_capacity = models.IntegerField(default=0, null=True, blank=True)
    diesel_capacity = models.IntegerField(default=0, null=True, blank=True)

    allowed_tanks = models.CharField(
        max_length=10,
        default="T1,T2,T3"
    )

    class Meta:
        unique_together = ('cluster', 'name')

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('staff','Staff'),
        ('admin','Admin'),
        ('viewer', 'Viewer'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    activation_sent_at = models.DateTimeField(null=True, blank=True)
    is_activated = models.BooleanField(default=False)

    station = models.ManyToManyField(
        Station,
        blank=True,
        related_name='assigned_users'
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def is_staff_user(self):
        return self.role == 'staff'

    def is_admin_user(self):
        return self.role == 'admin'

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"