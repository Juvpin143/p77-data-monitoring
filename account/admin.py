from django.contrib import admin
from .models import CustomUser, Station, Cluster

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'get_stations', 'role')
    list_filter = ('role',)
    search_fields = ('username',)

    def get_stations(self, obj):
        return ", ".join([s.name for s in obj.station.all()])

    get_stations.short_description = "Stations"

@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "cluster", "address")
    list_filter = ("cluster",)