from django.contrib import admin
from .models import UserProfile, FitnessGoal, FoodItem, FoodLog, WeightLog, WaterLog, AIRecommendation, DailyRoutine

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'height', 'created_at')
    search_fields = ('user__username', 'gender')

@admin.register(FitnessGoal)
class FitnessGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal_type', 'current_weight', 'target_weight', 'daily_calorie_goal')
    list_filter = ('goal_type',)
    search_fields = ('user__username',)

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'calories', 'protein', 'carbs', 'fat', 'serving_size', 'created_by')
    search_fields = ('name', 'barcode')

@admin.register(FoodLog)
class FoodLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'food_name', 'meal_type', 'quantity', 'calories', 'logged_at')
    list_filter = ('meal_type', 'logged_at')
    search_fields = ('user__username', 'food_name')

@admin.register(WeightLog)
class WeightLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'weight', 'logged_at')
    list_filter = ('logged_at',)
    search_fields = ('user__username',)

@admin.register(WaterLog)
class WaterLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'logged_at')
    list_filter = ('logged_at',)
    search_fields = ('user__username',)

@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'input_query', 'created_at')
    search_fields = ('user__username', 'input_query')

@admin.register(DailyRoutine)
class DailyRoutineAdmin(admin.ModelAdmin):
    list_display = ('user', 'task_name', 'is_completed', 'logged_at')
    list_filter = ('is_completed', 'logged_at')
    search_fields = ('user__username', 'task_name')

