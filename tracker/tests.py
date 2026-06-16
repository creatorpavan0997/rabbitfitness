from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from .models import UserProfile, FitnessGoal, FoodItem, FoodLog, WeightLog, WaterLog

class SignalTests(TestCase):
    def test_user_creation_creates_profile_and_goal(self):
        # Test that user creation triggers post_save signals for UserProfile and FitnessGoal
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        
        self.assertTrue(hasattr(user, 'profile'))
        self.assertTrue(hasattr(user, 'goal'))
        self.assertEqual(user.profile.user, user)
        self.assertEqual(user.goal.user, user)
        self.assertEqual(user.goal.daily_calorie_goal, 2000)


class FoodLogAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='api_user', password='password123')
        self.client.force_authenticate(user=self.user)
        
        self.food_item = FoodItem.objects.create(
            name='Chicken Breast',
            calories=165.00,
            protein=31.00,
            carbs=0.00,
            fat=3.60,
            serving_size='100g'
        )

    def test_log_food_item(self):
        url = '/api/food-log/'
        data = {
            'food_item': self.food_item.id,
            'meal_type': 'lunch',
            'quantity': 2.00 # 200g
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        log = FoodLog.objects.get(id=response.data['id'])
        self.assertEqual(log.food_name, 'Chicken Breast')
        self.assertEqual(log.calories, Decimal('330.00')) # 165 * 2
        self.assertEqual(log.protein, Decimal('62.00')) # 31 * 2


class WeightLogAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='weight_user', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_log_weight_updates_fitness_goal(self):
        url = '/api/weight-log/'
        data = {
            'weight': 74.50,
            'logged_at': str(timezone.localdate())
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify WeightLog exists
        self.assertEqual(WeightLog.objects.filter(user=self.user).count(), 1)
        
        # Verify FitnessGoal current_weight is updated
        goal = FitnessGoal.objects.get(user=self.user)
        self.assertEqual(goal.current_weight, Decimal('74.50'))


class WaterLogAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='water_user', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_quick_add_water(self):
        url = '/api/water-log/quick-add/'
        data = {'amount': 500}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify log entry
        log = WaterLog.objects.get(user=self.user, logged_at=timezone.localdate())
        self.assertEqual(log.amount, 500)

        # Quick add another 250ml
        response2 = self.client.post(url, {'amount': 250}, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        log.refresh_from_db()
        self.assertEqual(log.amount, 750)
