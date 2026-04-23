from django import forms
from .models import FuelInventory, Profile


class FuelInventoryForm(forms.ModelForm):

    class Meta:
        model = FuelInventory
        fields = [
            "fuel_type",
            "tank1_cm",
            "tank2_cm",
            "tank3_cm",
            "tank1_liters",
            "tank2_liters",
            "tank3_liters",
            "date",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_pic', 'phone_number', 'position']