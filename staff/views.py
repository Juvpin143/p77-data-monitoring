from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FuelInventory, Notification
from account.models import CustomUser

@login_required
def staff_dashboard(request):
    stations = request.user.station.all()
    sales = FuelInventory.objects.filter(station__in=stations)
    recent_reports = sales.order_by("-created_at")[:5]

    # 🔥 Get latest liters per fuel (NOT SUM)
    def get_latest_liters(fuel):
        latest = FuelInventory.objects.filter(
            station__in=stations,
            fuel_type=fuel
        ).order_by("-created_at").first()

        if not latest:
            return 0

        # Check which tank has value
        if latest.tank1_liters:
            return latest.tank1_liters
        elif latest.tank2_liters:
            return latest.tank2_liters
        elif latest.tank3_liters:
            return latest.tank3_liters

        return 0

    diesel_total = get_latest_liters("Diesel")
    premium_total = get_latest_liters("Premium")
    regular_total = get_latest_liters("ULG")

    context = {
        "recent_reports": recent_reports,
        "diesel_total": diesel_total,
        "premium_total": premium_total,
        "regular_total": regular_total,
    }

    return render(request, "dashboard/staff_dashboard.html", context)

@login_required
def submit_inventory(request):

    if request.method == "POST":

        stations = request.user.station.all().order_by("name")
        user = request.user
        has_data = False

        station_map = {}

        for s in stations:
            name = s.name.strip().upper()
            if name.endswith("T1"):
                station_map["T1"] = s
            elif name.endswith("T2"):
                station_map["T2"] = s
            elif name.endswith("T3"):
                station_map["T3"] = s

        # 🔥 FIX: Kung isa lang ang station at walang T1/T2/T3 sa name,
        # i-assign siya bilang T1 by default
        if not station_map and stations.count() == 1:
            station_map["T1"] = stations.first()

        def save_fuel(fuel_name, prefix):
            nonlocal has_data

            for tank in ["T1", "T2", "T3"]:
                cm = request.POST.get(f"{prefix}_{tank.lower()}_cm")
                liters = request.POST.get(f"{prefix}_{tank.lower()}_liters")

                if liters is not None and liters.strip() != "":
                    station = station_map.get(tank)

                    if station:
                        FuelInventory.objects.create(
                            user=user,
                            station=station,
                            fuel_type=fuel_name,
                            tank1_cm=int(cm or 0) if tank == "T1" else 0,
                            tank2_cm=int(cm or 0) if tank == "T2" else 0,
                            tank3_cm=int(cm or 0) if tank == "T3" else 0,
                            tank1_liters=int(liters or 0) if tank == "T1" else 0,
                            tank2_liters=int(liters or 0) if tank == "T2" else 0,
                            tank3_liters=int(liters or 0) if tank == "T3" else 0,
                        )
                        has_data = True

        save_fuel("Premium", "premium")
        save_fuel("Diesel", "diesel")
        save_fuel("ULG", "regular")

        if not has_data:
            messages.error(request, "Please enter at least one inventory value!")
            return redirect("submit_inventory")

        stations_names = ", ".join([s.name for s in stations])
        admins = CustomUser.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                notif_type='new_report',
                message=f"📋 {user.username} submitted a new fuel inventory report for {stations_names}."
            )

        messages.success(request, "Fuel inventory submitted successfully!")
        return redirect("my_reports")

    # GET request
    stations = request.user.station.all()

    allowed_tanks = set()
    has_premium = False
    has_regular = False
    has_diesel = False

    # 🔥 Per-tank capacity check
    premium_tanks = set()
    regular_tanks = set()
    diesel_tanks = set()

    for s in stations:
        name = s.name.strip()

        # Determine which tank this station is
        if name.endswith("T1"):
            tank_key = "T1"
            allowed_tanks.add("T1")
        elif name.endswith("T2"):
            tank_key = "T2"
            allowed_tanks.add("T2")
        elif name.endswith("T3"):
            tank_key = "T3"
            allowed_tanks.add("T3")
        else:
            tank_key = "T1"
            allowed_tanks.add("T1")

        # Check if fuel have capacity per tank
        if s.premium_capacity:
            has_premium = True
            premium_tanks.add(tank_key)
        if s.regular_capacity:
            has_regular = True
            regular_tanks.add(tank_key)
        if s.diesel_capacity:
            has_diesel = True
            diesel_tanks.add(tank_key)

    if not allowed_tanks:
        allowed_tanks = {"T1"}

    # 🔥 Default: ipakita lahat kung walang capacity data
    if not any([has_premium, has_regular, has_diesel]):
        has_premium = has_regular = has_diesel = True
        premium_tanks = regular_tanks = diesel_tanks = allowed_tanks

    context = {
        "allowed_tanks": allowed_tanks,
        "has_premium": has_premium,
        "has_regular": has_regular,
        "has_diesel": has_diesel,
        "premium_tanks": premium_tanks,
        "regular_tanks": regular_tanks,
        "diesel_tanks": diesel_tanks,
    }

    return render(request, "staff/submit_inventory.html", context)

def get_active_tank(obj):
    if not obj:
        return "-", 0

    if obj.tank1_liters:
        return "T1", obj.tank1_liters
    elif obj.tank2_liters:
        return "T2", obj.tank2_liters
    elif obj.tank3_liters:
        return "T3", obj.tank3_liters

    return "-", 0

@login_required
def my_reports(request):

    reports = FuelInventory.objects.filter(user=request.user).order_by("-created_at")

    return render(request, "staff/my_report.html", {"reports": reports})

@login_required
def view_report(request, id):

    report = FuelInventory.objects.get(id=id)

    return render(request, "staff/view_report.html", {"report": report})

@login_required
def edit_report(request, id):

    report = FuelInventory.objects.get(id=id, user=request.user)

    if request.method == "POST":

        has_data = False

        def get_values(prefix):
            t1_cm = request.POST.get(f"{prefix}_t1_cm")
            t2_cm = request.POST.get(f"{prefix}_t2_cm")
            t3_cm = request.POST.get(f"{prefix}_t3_cm")

            t1_l = request.POST.get(f"{prefix}_t1_liters")
            t2_l = request.POST.get(f"{prefix}_t2_liters")
            t3_l = request.POST.get(f"{prefix}_t3_liters")

            return t1_cm, t2_cm, t3_cm, t1_l, t2_l, t3_l

        if report.fuel_type == "Premium":
            values = get_values("premium")
        elif report.fuel_type == "Diesel":
            values = get_values("diesel")
        elif report.fuel_type == "ULG":
            values = get_values("regular")

        t1_cm, t2_cm, t3_cm, t1_l, t2_l, t3_l = values

        t1_cm = int(t1_cm or 0)
        t2_cm = int(t2_cm or 0)
        t3_cm = int(t3_cm or 0)

        t1_l = int(t1_l or 0)
        t2_l = int(t2_l or 0)
        t3_l = int(t3_l or 0)

        if not any([t1_cm, t2_cm, t3_cm, t1_l, t2_l, t3_l]):
            messages.error(request, "Please enter at least one value!")
            return redirect("edit_report", id=report.id)

        if (
            report.tank1_cm == t1_cm and
            report.tank2_cm == t2_cm and
            report.tank3_cm == t3_cm and
            report.tank1_liters == t1_l and
            report.tank2_liters == t2_l and
            report.tank3_liters == t3_l
        ):
            messages.warning(request, "No changes detected!")
            return redirect("edit_report", id=report.id)

        report.tank1_cm = t1_cm
        report.tank2_cm = t2_cm
        report.tank3_cm = t3_cm

        report.tank1_liters = t1_l
        report.tank2_liters = t2_l
        report.tank3_liters = t3_l

        report.save()

        messages.success(request, "Updated successfully!")
        return redirect("my_reports")

    # 🔥 FIX: GET request - gamitin ang parehong logic sa submit_inventory
    stations = request.user.station.all()

    allowed_tanks = set()
    has_premium = False
    has_regular = False
    has_diesel = False

    premium_tank = set()
    regular_tank = set()
    diesel_tank = set()

    for s in stations:
        name = s.name.strip()
        if name.endswith("T1"):
            tank_key = "T1"
            allowed_tanks.add("T1")
        elif name.endswith("T2"):
            tank_key = "T2"
            allowed_tanks.add("T2")
        elif name.endswith("T3"):
            tank_key = "T3"
            allowed_tanks.add("T3")
        else:
            tank_key = "T1"
            allowed_tanks.add("T1")

        if s.premium_capacity:
            has_premium = True
            premium_tank.add(tank_key)
        if s.regular_capacity:
            has_regular = True
            regular_tank.add(tank_key)
        if s.diesel_capacity:
            has_diesel = True
            diesel_tank.add(tank_key)

    if not allowed_tanks:
        allowed_tanks = {"T1"}

    if not any([has_premium, has_regular, has_diesel]):
        has_premium = has_regular = has_diesel = True
        premium_tank = regular_tank = diesel_tank = allowed_tanks

    context = {
        "allowed_tanks": allowed_tanks,
        "premium_tank": premium_tank,
        "regular_tank": regular_tank,
        "diesel_tank": diesel_tank,
        "has_premium": has_premium,
        "has_regular": has_regular,
        "has_diesel": has_diesel,

    }


    return render(request, "staff/edit_report.html", context)

@login_required
def delete_report(request, id):
    report = FuelInventory.objects.get(id=id)
    report.delete()
    messages.success(request, "Report deleted successfully!")
    return redirect("my_reports")
