from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # in cm
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class FitnessGoal(models.Model):
    GOAL_CHOICES = [
        ('loss', 'Weight Loss'),
        ('gain', 'Muscle Gain'),
        ('maintenance', 'Maintenance'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='goal')
    goal_type = models.CharField(max_length=15, choices=GOAL_CHOICES, default='maintenance')
    current_weight = models.DecimalField(max_digits=5, decimal_places=2, default=70.00) # in kg
    target_weight = models.DecimalField(max_digits=5, decimal_places=2, default=70.00) # in kg
    daily_calorie_goal = models.PositiveIntegerField(default=2000)
    daily_protein_goal = models.PositiveIntegerField(default=120) # in grams
    daily_carbs_goal = models.PositiveIntegerField(default=230) # in grams
    daily_fats_goal = models.PositiveIntegerField(default=65) # in grams
    daily_water_goal = models.PositiveIntegerField(default=2500) # in ml
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Fitness Goal"

class FoodItem(models.Model):
    name = models.CharField(max_length=200)
    calories = models.DecimalField(max_digits=6, decimal_places=2) # per serving/100g
    protein = models.DecimalField(max_digits=6, decimal_places=2) # in grams
    carbs = models.DecimalField(max_digits=6, decimal_places=2) # in grams
    fat = models.DecimalField(max_digits=6, decimal_places=2) # in grams
    serving_size = models.CharField(max_length=100, default='100g')
    barcode = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='custom_foods')
    favorite_by = models.ManyToManyField(User, related_name='favorite_foods', blank=True)

    def __str__(self):
        return self.name

class FoodLog(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_logs')
    food_item = models.ForeignKey(FoodItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    food_name = models.CharField(max_length=200)
    meal_type = models.CharField(max_length=15, choices=MEAL_CHOICES)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, default=1.00) # multiplier
    calories = models.DecimalField(max_digits=6, decimal_places=2)
    protein = models.DecimalField(max_digits=6, decimal_places=2)
    carbs = models.DecimalField(max_digits=6, decimal_places=2)
    fat = models.DecimalField(max_digits=6, decimal_places=2)
    logged_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} logged {self.food_name} for {self.meal_type}"

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_logs')
    weight = models.DecimalField(max_digits=5, decimal_places=2) # in kg
    logged_at = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ['-logged_at']
        unique_together = ('user', 'logged_at')

    def __str__(self):
        return f"{self.user.username} - {self.weight}kg on {self.logged_at}"

class WaterLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_logs')
    amount = models.PositiveIntegerField() # in ml
    logged_at = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ['-logged_at']
        unique_together = ('user', 'logged_at')

    def __str__(self):
        return f"{self.user.username} - {self.amount}ml on {self.logged_at}"

class AIRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_recommendations')
    input_query = models.TextField()
    recommendation_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AI Rec for {self.user.username} on {self.created_at.strftime('%Y-%m-%d')}"


class DailyRoutine(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routines')
    task_name = models.CharField(max_length=150)
    is_completed = models.BooleanField(default=False)
    logged_at = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ['logged_at', 'id']
        unique_together = ('user', 'task_name', 'logged_at')

    def __str__(self):
        return f"{self.user.username} - {self.task_name} on {self.logged_at} (Completed: {self.is_completed})"

class DietMeal(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('snack', 'Snack'),
        ('dinner', 'Dinner'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_meals')
    meal_type = models.CharField(max_length=15, choices=MEAL_CHOICES)
    items = models.TextField(help_text="Checklist items text list")
    calories = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    carbs = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    fat = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('user', 'meal_type')

    def __str__(self):
        return f"{self.user.username}'s {self.get_meal_type_display()} Plan"


class DailyDietCheck(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('snack', 'Snack'),
        ('dinner', 'Dinner'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_checks')
    meal_type = models.CharField(max_length=15, choices=MEAL_CHOICES)
    logged_at = models.DateField(default=timezone.localdate)
    is_eaten = models.BooleanField(default=False)
    linked_log = models.ForeignKey(FoodLog, on_delete=models.SET_NULL, null=True, blank=True, related_name='diet_checks')

    class Meta:
        ordering = ['logged_at', 'meal_type']
        unique_together = ('user', 'meal_type', 'logged_at')

    def __str__(self):
        return f"{self.user.username} - {self.get_meal_type_display()} on {self.logged_at} (Eaten: {self.is_eaten})"


# Signals to auto-create user profile and default fitness goal on registration
@receiver(post_save, sender=User)
def create_user_profile_and_goal(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        FitnessGoal.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile_and_goal(sender, instance, **kwargs):
    # Ensure profile and goal exist even if users were created without signals initially
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()

    if not hasattr(instance, 'goal'):
        FitnessGoal.objects.create(user=instance)
    else:
        instance.goal.save()
