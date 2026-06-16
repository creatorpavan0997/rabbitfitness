from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, FitnessGoal

class UserRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['age', 'gender', 'height']
        widgets = {
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 28'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 175.5', 'step': '0.1'}),
        }


class FitnessGoalForm(forms.ModelForm):
    class Meta:
        model = FitnessGoal
        fields = [
            'goal_type', 'current_weight', 'target_weight',
            'daily_calorie_goal', 'daily_protein_goal', 'daily_carbs_goal',
            'daily_fats_goal', 'daily_water_goal'
        ]
        widgets = {
            'goal_type': forms.Select(attrs={'class': 'form-select'}),
            'current_weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 75.0', 'step': '0.1'}),
            'target_weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 70.0', 'step': '0.1'}),
            'daily_calorie_goal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2000'}),
            'daily_protein_goal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 140'}),
            'daily_carbs_goal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 240'}),
            'daily_fats_goal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 65'}),
            'daily_water_goal': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2500'}),
        }
