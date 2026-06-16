from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, FitnessGoal, FoodItem, FoodLog, WeightLog, WaterLog, AIRecommendation, DailyRoutine, DietMeal, DailyDietCheck

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'age', 'gender', 'height', 'created_at', 'updated_at']

class FitnessGoalSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    class Meta:
        model = FitnessGoal
        fields = [
            'id', 'user', 'goal_type', 'current_weight', 'target_weight',
            'daily_calorie_goal', 'daily_protein_goal', 'daily_carbs_goal',
            'daily_fats_goal', 'daily_water_goal', 'updated_at'
        ]

class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = ['id', 'name', 'calories', 'protein', 'carbs', 'fat', 'serving_size', 'barcode']
        read_only_fields = ['id']

class FoodLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    food_item_detail = FoodItemSerializer(source='food_item', read_only=True)
    food_name = serializers.CharField(required=False, allow_blank=True, default="")

    calories = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    protein = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    carbs = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    fat = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)

    class Meta:
        model = FoodLog
        fields = [
            'id', 'user', 'food_item', 'food_item_detail', 'food_name',
            'meal_type', 'quantity', 'calories', 'protein', 'carbs', 'fat', 'logged_at'
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        # Calculate macros based on quantity if food_item is selected
        food_item = validated_data.get('food_item')
        quantity = validated_data.get('quantity', 1.00)
        
        if food_item:
            # Multiplier calculation (quantity represents number of servings/multipliers)
            validated_data['calories'] = food_item.calories * quantity
            validated_data['protein'] = food_item.protein * quantity
            validated_data['carbs'] = food_item.carbs * quantity
            validated_data['fat'] = food_item.fat * quantity
            if not validated_data.get('food_name'):
                validated_data['food_name'] = food_item.name
        else:
            # If logged manually, values must be supplied or defaulted to 0
            validated_data['calories'] = validated_data.get('calories', 0.00)
            validated_data['protein'] = validated_data.get('protein', 0.00)
            validated_data['carbs'] = validated_data.get('carbs', 0.00)
            validated_data['fat'] = validated_data.get('fat', 0.00)
            
        return super().create(validated_data)

class WeightLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = WeightLog
        fields = ['id', 'user', 'weight', 'logged_at']
        read_only_fields = ['id']

    def validate_weight(self, value):
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0.")
        return value

class WaterLogSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = WaterLog
        fields = ['id', 'user', 'amount', 'logged_at']
        read_only_fields = ['id']

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Water amount cannot be negative.")
        return value

class AIRecommendationSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = AIRecommendation
        fields = ['id', 'user', 'input_query', 'recommendation_text', 'created_at']
        read_only_fields = ['id', 'created_at']


class DailyRoutineSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DailyRoutine
        fields = ['id', 'user', 'task_name', 'is_completed', 'logged_at']
        read_only_fields = ['id']


class DietMealSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DietMeal
        fields = ['id', 'user', 'meal_type', 'items', 'calories', 'protein', 'carbs', 'fat']
        read_only_fields = ['id']


class DailyDietCheckSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = DailyDietCheck
        fields = ['id', 'user', 'meal_type', 'logged_at', 'is_eaten', 'linked_log']
        read_only_fields = ['id', 'linked_log']
