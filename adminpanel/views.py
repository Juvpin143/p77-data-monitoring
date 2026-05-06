from django.contrib.messages.context_processors import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from account.forms import ClusterForm, StationForm, AssignForm, StationEditForm
from django.db.models import Case, When, IntegerField, Value
from staff.models import FuelInventory, Notification, StationDispatch
from account.models import CustomUser, Station
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from account.models import Cluster
from django.contrib import messages
from django.db.models import Q
from functools import wraps
from django.urls import reverse
from django.db.models import Value
from django.db.models.functions import Concat
from django.http import JsonResponse

User = get_user_model()

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (
            request.user.is_superuser or request.user.role in ['admin', 'viewer']
        ):
            return view_func(request, *args, **kwargs)
        return redirect(reverse('account:login'))
    return _wrapped_view

def full_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == 'admin'
        ):
            return view_func(request, *args, **kwargs)
        messages.error(request, "You don't have permission to do this.")
        return redirect(reverse('adminpanel:admin_dashboard'))
    return _wrapped_view

@admin_required
def admin_dashboard(request):
    clusters = Cluster.objects.prefetch_related('stations').order_by('code')

    all_stations = []
    area_totals = {}
    area_dispatch_totals = {}

    for cluster in clusters:

        area_dispatch_totals[cluster.name] = {
            'premium_total': 0,
            'regular_total': 0,
            'diesel_total': 0
        }

        area_totals[cluster.name] = 0  #  initialize even no station

        stations = cluster.stations.order_by('id')

        if not stations.exists():
            # Display Cluster even no station yet
            all_stations.append({
                'id': None,
                'area': cluster.name,
                'cluster_code': cluster.code,
                'name': '— No stations yet —',
                'premium': 0, 'premium_vacancy': 0, 'premium_dispatch': 0, 'premium_dispatch2': 0, 'premium_capacity': 0,
                'regular': 0, 'regular_vacancy': 0, 'regular_dispatch': 0, 'regular_dispatch2': 0, 'regular_capacity': 0,
                'diesel': 0, 'diesel_vacancy': 0, 'diesel_dispatch': 0, 'diesel_dispatch2': 0, 'diesel_capacity': 0,
                'created_at': None
            })
            continue

        for station in stations:

            premium_capacity = station.premium_capacity or 0
            regular_capacity = station.regular_capacity or 0
            diesel_capacity = station.diesel_capacity or 0

            def get_latest(fuel, capacity):
                latest = FuelInventory.objects.filter(
                    station=station,
                    fuel_type=fuel
                ).order_by('-created_at').first()

                dispatch_obj = StationDispatch.objects.filter(
                    station=station,
                    fuel_type=fuel
                ).first()

                dispatch = int(dispatch_obj.dispatch_liters) if dispatch_obj else 0
                dispatch2 = int(dispatch_obj.dispatch_liters2) if dispatch_obj else 0

                if not latest:
                    return 0, capacity, dispatch, dispatch2, None, 'secondary'

                t1 = latest.tank1_liters or 0
                t2 = latest.tank2_liters or 0
                t3 = latest.tank3_liters or 0

                liters = t1 + t2 + t3
                vacancy = capacity - liters
                latest_time = latest.created_at

                percent = (liters / capacity * 100) if capacity > 0 else 0

                if liters == 0:
                    color = 'secondary'
                elif percent <= 25:
                    color = 'danger'
                elif percent <= 40:
                    color = 'light-danger'
                elif percent <= 60:
                    color = 'orange'
                elif percent <= 80:
                    color = 'light-success'
                else:
                    color = 'success'

                return liters, vacancy, dispatch, dispatch2, latest_time, color

            premium_liters, premium_vac, premium_disp, premium_disp2, premium_time, premium_color = get_latest(
                'Premium', premium_capacity)
            regular_liters, regular_vac, regular_disp, regular_disp2, regular_time, regular_color = get_latest('ULG',
                                                                                                               regular_capacity)
            diesel_liters, diesel_vac, diesel_disp, diesel_disp2, diesel_time, diesel_color = get_latest('Diesel',
                                                                                                         diesel_capacity)

            # totals — disp1 + disp2 combined
            area_dispatch_totals[cluster.name]['premium_total'] += premium_disp + premium_disp2
            area_dispatch_totals[cluster.name]['regular_total'] += regular_disp + regular_disp2
            area_dispatch_totals[cluster.name]['diesel_total'] += diesel_disp + diesel_disp2

            all_stations.append({
                'id': station.id,
                'area': cluster.name,
                'cluster_code': cluster.code,
                'name': station.name,
                'premium': premium_liters,
                'premium_vacancy': premium_vac,
                'premium_dispatch': premium_disp,
                'premium_dispatch2': premium_disp2,
                'premium_capacity': premium_capacity,
                'regular': regular_liters,
                'regular_vacancy': regular_vac,
                'regular_dispatch': regular_disp,
                'regular_dispatch2': regular_disp2,
                'regular_capacity': regular_capacity,
                'diesel': diesel_liters,
                'diesel_vacancy': diesel_vac,
                'diesel_dispatch': diesel_disp,
                'diesel_dispatch2': diesel_disp2,
                'diesel_capacity': diesel_capacity,
                'premium_color': premium_color,
                'regular_color': regular_color,
                'diesel_color': diesel_color,
                'created_at': premium_time or regular_time or diesel_time
            })

    all_stations = sorted(all_stations, key=lambda x: (x['cluster_code'], x['area']))

    return render(request, 'dashboard/admin_dashboard.html', {
        'stations': all_stations,
        'area_totals': area_totals,
        'area_dispatch_totals': area_dispatch_totals
    })

@require_POST
@full_admin_required
def update_dispatch(request):
    station_id = request.POST.get('station_id')
    fuel_type = request.POST.get('fuel_type')
    dispatch_value = request.POST.get('dispatch')
    dispatch_value2 = request.POST.get('dispatch2')

    if not station_id:
        return JsonResponse({'status': 'error'}, status=400)

    updates = {}
    if dispatch_value is not None:
        try:
            updates['dispatch_liters'] = float(dispatch_value)
        except ValueError:
            return JsonResponse({'status': 'error'}, status=400)

    if dispatch_value2 is not None:
        try:
            updates['dispatch_liters2'] = float(dispatch_value2)
        except ValueError:
            return JsonResponse({'status': 'error'}, status=400)

    if updates:
        StationDispatch.objects.update_or_create(
            station_id=station_id,
            fuel_type=fuel_type,
            defaults=updates
        )

    return JsonResponse({'status': 'ok'})

@login_required
@full_admin_required
def add_cluster(request):
    if request.method == 'POST':
        form = ClusterForm(request.POST)
        if form.is_valid():
            cluster = form.save()
            messages.success(request, f"'{cluster.name}' added successfully!")
            return redirect(reverse('adminpanel:admin_dashboard'))
    else:
        form = ClusterForm()

    return render(request, 'admin/add_cluster.html', {"form": form})

@full_admin_required
def add_station(request):
    if request.method == 'POST':
        form = StationForm(request.POST)
        if form.is_valid():
            station = form.save()
            messages.success(request, f"'{station.name}' added successfully!")
            return redirect(reverse('adminpanel:add_station'))
    else:
        form = StationForm()
    return render(request, 'admin/add_station.html', {"form": form})


@full_admin_required
def assign_user(request):
    if request.method == 'POST':
        form = AssignForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            stations = form.cleaned_data['station']
            user.station.set(stations)

            station_names = ", ".join([s.name for s in stations])

            messages.success(request, f"'{user.username}' assigned to '{station_names}' successfully!")
            return redirect(reverse('adminpanel:user_list'))
    else:
        form = AssignForm()

    return render(request, 'account/assign_user.html', {'form': form})

@admin_required
def user_list(request):
    query = request.GET.get('q', '').strip()
    role = request.GET.get('role')

    users = CustomUser.objects.prefetch_related("station").filter(
        Q(is_activated=True) | Q(is_superuser=True)
    ).order_by(
        Case(
            When(is_superuser=True, then=Value(0)),
            When(role='admin', then=Value(1)),
            default=Value(2),
            output_field=IntegerField()
        )
    )

    if query:
        users = users.annotate(
            full_name_db=Concat('first_name', Value(' '), 'last_name')
        ).filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(full_name_db__icontains=query)
        )

    if role == 'admin':
        users = users.filter(role='admin')
    elif role == 'staff':
        users = users.filter(role='staff')
    elif role == 'viewer':
        users = users.filter(role='viewer')

    return render(request, 'admin/user_list.html', {"users": users, "role": role})

@full_admin_required
def activate(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if user.is_superuser:
        messages.error(request, "Admin cannot be deactivated!")
        return redirect(request.GET.get("next") or reverse('adminpanel:user_list'))
    user.is_active = True
    user.save()
    messages.success(request, f"{user.username} has been activated!")
    return redirect(request.GET.get("next") or reverse('adminpanel:user_list'))

@full_admin_required
def deactivate(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if user.is_superuser:
        messages.error(request, "Admin cannot be deactivated!")
        return redirect(request.GET.get("next") or reverse('adminpanel:user_list'))
    user.is_active = False
    user.save()
    messages.warning(request, f"{user.username} has been deactivated!")
    return redirect(request.GET.get("next") or reverse('adminpanel:user_list'))

@full_admin_required
def delete_user(request, user_id):
    staff = get_object_or_404(CustomUser, id=user_id)
    if staff.is_superuser or staff.role == 'admin':
        messages.error(request, "Admin accounts cannot be deleted!")
        return redirect(request.GET.get("next") or reverse('adminpanel:user_list'))
    username = staff.username
    staff.delete()
    messages.success(request, f"'{username}' has been deleted!")
    return redirect(request.GET.get("next") or reverse('adminpanel:user_list'))

@admin_required
def all_reports(request):
    reports = FuelInventory.objects.select_related("user", "station").order_by("-created_at")

    query = request.GET.get('q', '').strip()
    fuel = request.GET.get('fuel')
    status = request.GET.get('status')

    if query:
        reports = reports.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(station__name__icontains=query)
        )

    if fuel:
        reports = reports.filter(fuel_type=fuel)

    if status == 'read':
        reports = reports.filter(is_read=True)
    elif status == 'unread':
        reports = reports.filter(is_read=False)

    return render(request, "admin/all_reports.html", {"reports": reports})

@admin_required
def toggle_read(request, id):
    report = get_object_or_404(FuelInventory, id=id)
    report.is_read = not report.is_read
    report.save()
    messages.success(request, f"{report.station} read successfully!")
    return redirect(request.GET.get('next') or reverse('adminpanel:all_reports'))

@full_admin_required
def delete_report(request, id):
    report = get_object_or_404(FuelInventory, id=id)
    fuel_type = report.fuel_type
    report.delete()
    messages.success(request, f"'{fuel_type}' report has been deleted!")
    return redirect(reverse('adminpanel:all_reports'))

@admin_required
def notification(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by("-created_at")

    unread_count = notifications.filter(is_read=False).count()

    return render(request, "admin/notification.html", {
        "notifications": notifications,
        "unread_count": unread_count
    })

@admin_required
def mark_as_read(request, notif_id):
    if request.method == "POST":
        notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
        notif.is_read = True
        notif.save()
    return redirect(reverse('adminpanel:notifications'))

@admin_required
def mark_all_as_read(request):
    if request.method == "POST":
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
    return redirect(reverse('adminpanel:notifications'))

@full_admin_required
def read_toggle(request, id):
    report = get_object_or_404(FuelInventory, id=id)
    report.is_read = not report.is_read
    report.save()
    messages.success(request, '')

    # ✅ Notify staff kapag na-read ni Admin
    if report.is_read:
        Notification.objects.create(
            recipient=report.user,
            notif_type='report_read',
            message=f"✅ Admin has read your {report.fuel_type} inventory report for {report.station.name}."
        )

    return redirect(request.GET.get('next') or reverse('adminpanel:all_reports'))

@admin_required
def station_list(request):
    query = request.GET.get('q', '').strip()
    cluster_filter = request.GET.get('cluster', '').strip()

    stations = Station.objects.select_related('cluster').prefetch_related(
        'assigned_users'
    ).order_by('cluster__code', 'name')

    if query:
        stations = stations.filter(
            Q(cluster__name__icontains=query) |
            Q(name__icontains=query)
        )

    if cluster_filter:
        stations = stations.filter(cluster__name__icontains=cluster_filter)

    return render(request, 'admin/station_list.html', {'stations': stations})

@full_admin_required
def delete_station(request, id):
    station = get_object_or_404(Station, id=id)
    name = station.name
    station.delete()
    messages.info(request, f"'{name}' has been deleted!")
    return redirect(reverse('adminpanel:station_list'))

@full_admin_required
def edit_station(request, id):
    station = get_object_or_404(Station, id=id)

    current_user = station.assigned_users.first()

    if request.method == "POST":
        form = StationEditForm(request.POST, instance=station)
        if form.is_valid():
            form.save()

            selected_user = form.cleaned_data.get('user')

            station.assigned_users.clear()

            if selected_user:
                selected_user.station.add(station)

            messages.success(request, f"'{station.name}' has been updated successfully!")
            return redirect(reverse('adminpanel:station_list'))
    else:
        form = StationEditForm(instance=station, initial={'user': current_user})

    return render(request, 'admin/edit_station.html', {
        'station': station,
        'form': form
    })