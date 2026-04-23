from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Cluster, Station


class RegisterForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2'
        ]

class ClusterForm(forms.ModelForm):
    class Meta:
        model = Cluster
        fields = ['name', 'code']

class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['cluster', 'name', 'premium_capacity', 'regular_capacity', 'diesel_capacity']

class AssignForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='staff').order_by('username'),
        empty_label='— Select User —',
        label='Select User'
    )
    station = forms.ModelMultipleChoiceField(
        queryset=Station.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        label='Select Stations'
    )

class StationEditForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role='staff').order_by('username'),
        empty_label='— Select User —',
        label='Select User',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Station
        fields = ['cluster', 'name', 'premium_capacity', 'regular_capacity', 'diesel_capacity']
        widgets = {
            'cluster': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'premium_capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'regular_capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'diesel_capacity': forms.NumberInput(attrs={'class': 'form-control'}),
        }