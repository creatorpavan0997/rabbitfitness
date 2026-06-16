from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from .forms import UserRegisterForm, UserProfileForm, FitnessGoalForm
from .models import UserProfile, FitnessGoal, FoodLog, WeightLog, WaterLog

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Authenticate and login the new user
            login(request, user)
            messages.success(request, f"Welcome to Rabbit Fitness, {user.username}!")
            return redirect('profile')
    else:
        form = UserRegisterForm()
        
    return render(request, 'tracker/auth/register.html', {'form': form})

@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    goal, _ = FitnessGoal.objects.get_or_create(user=user)

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=profile)
        goal_form = FitnessGoalForm(request.POST, instance=goal)
        
        if profile_form.is_valid() and goal_form.is_valid():
            profile_form.save()
            goal_form.save()
            messages.success(request, "Your profile and fitness goals have been updated!")
            return redirect('dashboard')
    else:
        profile_form = UserProfileForm(instance=profile)
        goal_form = FitnessGoalForm(instance=goal)

    context = {
        'profile_form': profile_form,
        'goal_form': goal_form,
    }
    return render(request, 'tracker/auth/profile.html', context)

@login_required
def dashboard_view(request):
    return render(request, 'tracker/dashboard.html')

@login_required
def food_log_view(request):
    return render(request, 'tracker/food_log.html')

@login_required
def weight_tracker_view(request):
    return render(request, 'tracker/weight_tracker.html')

@login_required
def water_tracker_view(request):
    return render(request, 'tracker/water_tracker.html')

@login_required
def ai_coach_view(request):
    return render(request, 'tracker/ai_coach.html')

@login_required
def diet_plan_view(request):
    return render(request, 'tracker/diet_plan.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')
