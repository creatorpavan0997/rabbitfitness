from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal

from .models import UserProfile, FitnessGoal, FoodItem, FoodLog, WeightLog, WaterLog, DietMeal, DailyDietCheck

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


class DietPlanAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='diet_user', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_seeding_default_diet_plan(self):
        url = '/api/diet-meals/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        self.assertEqual(DietMeal.objects.filter(user=self.user).count(), 4)

        breakfast = DietMeal.objects.get(user=self.user, meal_type='breakfast')
        self.assertEqual(breakfast.calories, Decimal('939.00'))
        self.assertEqual(breakfast.protein, Decimal('35.00'))

    def test_update_diet_meal(self):
        self.client.get('/api/diet-meals/')
        meal = DietMeal.objects.get(user=self.user, meal_type='breakfast')

        url = f'/api/diet-meals/{meal.id}/'
        data = {
            'meal_type': 'breakfast',
            'items': '* Protein Shake - 1 serving',
            'calories': 150.00,
            'protein': 30.00,
            'carbs': 3.00,
            'fat': 2.00
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        meal.refresh_from_db()
        self.assertEqual(meal.calories, Decimal('150.00'))
        self.assertEqual(meal.protein, Decimal('30.00'))
        self.assertEqual(meal.items, '* Protein Shake - 1 serving')

    def test_toggle_diet_check_creates_and_deletes_food_log(self):
        url = '/api/diet-checks/toggle/'
        data = {
            'meal_type': 'lunch',
            'is_eaten': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_eaten'])

        food_logs = FoodLog.objects.filter(user=self.user, meal_type='lunch')
        self.assertEqual(food_logs.count(), 1)
        food_log = food_logs.first()
        self.assertEqual(food_log.food_name, "Diet Plan: Lunch")
        self.assertEqual(food_log.calories, Decimal('1345.00'))

        check = DailyDietCheck.objects.get(user=self.user, meal_type='lunch', logged_at=timezone.localdate())
        self.assertEqual(check.linked_log, food_log)

        data['is_eaten'] = False
        response2 = self.client.post(url, data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertFalse(response2.data['is_eaten'])

        self.assertEqual(FoodLog.objects.filter(user=self.user, meal_type='lunch').count(), 0)

        check.refresh_from_db()
        self.assertIsNone(check.linked_log)


class CarrotEstimateAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='carrot_user', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_carrot_estimate_valid_input(self):
        url = '/api/food/carrot-estimate/'
        data = {
            'text': "100g oats\n2 eggs\n1.5 tbsp ghee"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response structure
        self.assertIn('items', response.data)
        self.assertIn('calories', response.data)
        self.assertIn('protein', response.data)
        self.assertIn('carbs', response.data)
        self.assertIn('fat', response.data)
        
        # 100g oats -> calories: 389, protein: 16.9, carbs: 66.3, fat: 6.9
        # 2 eggs -> calories: 70 * 2 = 140, protein: 6.0 * 2 = 12.0, carbs: 0.6 * 2 = 1.2, fat: 5.0 * 2 = 10.0
        # 1.5 tbsp ghee -> default unit g, alt_units: tbsp = 15g. 1.5 tbsp = 22.5g.
        # multiplier = 22.5 / 100.0 = 0.225.
        # ghee 100g -> calories: 900, fat: 100.0
        # 1.5 tbsp ghee -> calories: 900 * 0.225 = 202.5, fat: 100 * 0.225 = 22.5
        # Total calories estimated: 389 + 140 + 202.5 = 731.5
        # Total protein: 16.9 + 12.0 = 28.9
        # Total carbs: 66.3 + 1.2 = 67.5
        # Total fat: 6.9 + 10.0 + 22.5 = 39.4
        
        self.assertEqual(response.data['calories'], 731.5)
        self.assertEqual(response.data['protein'], 28.9)
        self.assertEqual(response.data['carbs'], 67.5)
        self.assertEqual(response.data['fat'], 39.4)
        
        items = response.data['items']
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]['matched_name'], 'oats')
        self.assertEqual(items[1]['matched_name'], 'egg')
        self.assertEqual(items[2]['matched_name'], 'ghee')

    def test_carrot_estimate_empty_input(self):
        url = '/api/food/carrot-estimate/'
        response = self.client.post(url, {'text': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

