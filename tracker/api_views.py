import requests
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
import os
import json
import google.generativeai as genai

from .models import FoodLog, WeightLog, WaterLog, FoodItem, FitnessGoal, AIRecommendation, UserProfile, DailyRoutine, DietMeal, DailyDietCheck
from .serializers import (
    FoodLogSerializer, WeightLogSerializer, WaterLogSerializer,
    FoodItemSerializer, FitnessGoalSerializer, AIRecommendationSerializer, DailyRoutineSerializer,
    DietMealSerializer, DailyDietCheckSerializer
)

class FoodLogViewSet(viewsets.ModelViewSet):
    serializer_class = FoodLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Allow filtering by date, default to today
        queryset = FoodLog.objects.filter(user=self.request.user)
        date_str = self.request.query_params.get('date', None)
        if date_str:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(logged_at__date=date)
            except ValueError:
                pass
        else:
            queryset = queryset.filter(logged_at__date=timezone.localdate())
        return queryset.order_by('logged_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WeightLogViewSet(viewsets.ModelViewSet):
    serializer_class = WeightLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WeightLog.objects.filter(user=self.request.user).order_by('-logged_at')

    def perform_create(self, serializer):
        # Update or create for a specific date
        logged_at = serializer.validated_data.get('logged_at', timezone.localdate())
        weight = serializer.validated_data.get('weight')
        
        weight_log, created = WeightLog.objects.update_or_create(
            user=self.request.user,
            logged_at=logged_at,
            defaults={'weight': weight}
        )
        
        # Also update current_weight in FitnessGoal
        goal, _ = FitnessGoal.objects.get_or_create(user=self.request.user)
        goal.current_weight = weight
        goal.save()


class WaterLogViewSet(viewsets.ModelViewSet):
    serializer_class = WaterLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WaterLog.objects.filter(user=self.request.user).order_by('-logged_at')

    def perform_create(self, serializer):
        logged_at = serializer.validated_data.get('logged_at', timezone.localdate())
        amount = serializer.validated_data.get('amount')
        
        water_log, created = WaterLog.objects.get_or_create(
            user=self.request.user,
            logged_at=logged_at,
            defaults={'amount': 0}
        )
        water_log.amount += amount
        water_log.save()

    @action(detail=False, methods=['POST'], url_path='quick-add')
    def quick_add(self, request):
        amount = request.data.get('amount', 250)
        try:
            amount = int(amount)
        except ValueError:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
            
        today = timezone.localdate()
        water_log, created = WaterLog.objects.get_or_create(
            user=self.request.user,
            logged_at=today,
            defaults={'amount': 0}
        )
        water_log.amount += amount
        water_log.save()
        
        return Response(WaterLogSerializer(water_log).data, status=status.HTTP_200_OK)


class DashboardDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        
        # Get fitness goals
        goal, created = FitnessGoal.objects.get_or_create(user=user)
        goal_data = FitnessGoalSerializer(goal, context={'request': request}).data
        
        # Today's logs
        food_logs = FoodLog.objects.filter(user=user, logged_at__date=today)
        water_log = WaterLog.objects.filter(user=user, logged_at=today).first()
        weight_log = WeightLog.objects.filter(user=user, logged_at=today).first()
        if not weight_log:
            # Fallback to the latest weight log
            weight_log = WeightLog.objects.filter(user=user).order_by('-logged_at').first()

        # Nutrition calculations
        totals = food_logs.aggregate(
            calories=Sum('calories'),
            protein=Sum('protein'),
            carbs=Sum('carbs'),
            fat=Sum('fat')
        )
        
        calories_consumed = float(totals['calories'] or 0)
        protein_consumed = float(totals['protein'] or 0)
        carbs_consumed = float(totals['carbs'] or 0)
        fat_consumed = float(totals['fat'] or 0)
        water_consumed = water_log.amount if water_log else 0
        current_weight = float(weight_log.weight) if weight_log else float(goal.current_weight)

        # Weekly/Monthly trends for charts
        # 1. Calorie & Macros history (last 7 days)
        calorie_history = []
        labels = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            labels.append(date.strftime('%a'))
            day_logs = FoodLog.objects.filter(user=user, logged_at__date=date)
            day_totals = day_logs.aggregate(calories=Sum('calories'))
            calorie_history.append(float(day_totals['calories'] or 0))

        # 2. Weight history (last 30 days)
        weight_history = []
        weight_labels = []
        thirty_days_ago = today - timedelta(days=30)
        weight_logs = WeightLog.objects.filter(user=user, logged_at__gte=thirty_days_ago).order_by('logged_at')
        for wl in weight_logs:
            weight_labels.append(wl.logged_at.strftime('%m/%d'))
            weight_history.append(float(wl.weight))

        # 3. Water history (last 7 days)
        water_history = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            wl = WaterLog.objects.filter(user=user, logged_at=date).first()
            water_history.append(wl.amount if wl else 0)

        response_data = {
            'summary': {
                'calories_consumed': calories_consumed,
                'protein_consumed': protein_consumed,
                'carbs_consumed': carbs_consumed,
                'fat_consumed': fat_consumed,
                'water_consumed': water_consumed,
                'current_weight': current_weight,
                'calories_goal': goal.daily_calorie_goal,
                'protein_goal': goal.daily_protein_goal,
                'carbs_goal': goal.daily_carbs_goal,
                'fat_goal': goal.daily_fats_goal,
                'water_goal': goal.daily_water_goal,
            },
            'goal': goal_data,
            'charts': {
                'calorie_history': calorie_history,
                'calorie_labels': labels,
                'weight_history': weight_history,
                'weight_labels': weight_labels,
                'water_history': water_history,
                'water_labels': labels,
            }
        }
        return Response(response_data)


class FoodSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'results': []})

        results = []

        # 1. Search local user custom food items first
        local_foods = FoodItem.objects.filter(
            Q(created_by=request.user) | Q(created_by__isnull=True),
            name__icontains=query
        )[:10]
        for food in local_foods:
            results.append({
                'id': food.id,
                'name': food.name,
                'calories': float(food.calories),
                'protein': float(food.protein),
                'carbs': float(food.carbs),
                'fat': float(food.fat),
                'serving_size': food.serving_size,
                'barcode': food.barcode,
                'source': 'local'
            })

        # 2. Search Open Food Facts API
        try:
            url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                'search_terms': query,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 10
            }
            headers = {
                'User-Agent': 'AIFitnessTracker - Windows - Version 1.0 - contact@aifitnesstracker.com'
            }
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                for prod in products:
                    name = prod.get('product_name')
                    if not name:
                        continue
                    
                    nutriments = prod.get('nutriments', {})
                    # Open Food Facts returns values per 100g
                    calories = nutriments.get('energy-kcal_100g', nutriments.get('energy-kcal', 0))
                    protein = nutriments.get('proteins_100g', 0)
                    carbs = nutriments.get('carbohydrates_100g', 0)
                    fat = nutriments.get('fat_100g', 0)
                    serving_size = prod.get('serving_size', '100g')
                    barcode = prod.get('code', '')

                    # Append to results if not already there
                    results.append({
                        'id': None,
                        'name': name,
                        'calories': float(calories),
                        'protein': float(protein),
                        'carbs': float(carbs),
                        'fat': float(fat),
                        'serving_size': serving_size,
                        'barcode': barcode,
                        'source': 'open_food_facts'
                    })
        except Exception as e:
            # Silently ignore search error to fallback gracefully
            pass

        return Response({'results': results})

class FoodSaveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Saves an Open Food Facts product locally so it can be selected as FoodItem
        data = request.data
        barcode = data.get('barcode')
        
        # Check if already exists
        food_item = None
        if barcode:
            food_item = FoodItem.objects.filter(barcode=barcode).first()
            
        if not food_item:
            serializer = FoodItemSerializer(data=data)
            if serializer.is_valid():
                food_item = serializer.save(created_by=request.user)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(FoodItemSerializer(food_item).data, status=status.HTTP_201_CREATED)


def generate_gemini_content(prompt):
    keys = []
    primary = os.getenv("GEMINI_API_KEY")
    if primary:
        keys.append(primary)
        
    extra_keys = []
    for env_name, env_val in os.environ.items():
        if env_name.startswith("GEMINI_API_KEY_") and env_val:
            extra_keys.append((env_name, env_val))
            
    # Sort logically so GEMINI_API_KEY_2 comes before GEMINI_API_KEY_10
    def get_sort_key(item):
        name = item[0]
        suffix = name[len("GEMINI_API_KEY_"):]
        if suffix.isdigit():
            return (0, int(suffix))
        return (1, name)
        
    extra_keys.sort(key=get_sort_key)
    
    for _, val in extra_keys:
        if val not in ordered_keys:
            ordered_keys.append(val)

    if not ordered_keys:
        raise ValueError("No Gemini API keys are configured in environment settings.")

    last_error = None
    for i, key in enumerate(ordered_keys):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(prompt)
            return response
        except Exception as e:
            last_error = e
            print(f"Gemini API key {i+1} failed: {str(e)}")
            continue
    raise last_error


class AICoachView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        recs = AIRecommendation.objects.filter(user=request.user).order_by('-created_at')[:10]
        return Response(AIRecommendationSerializer(recs, many=True).data)

    def post(self, request):
        user = request.user
        action_type = request.data.get('action') # 'analyze' or 'chat'
        
        # Get user settings
        profile, _ = UserProfile.objects.get_or_create(user=user)
        goal, _ = FitnessGoal.objects.get_or_create(user=user)

        # Collect today's data to provide full context to the AI Coach
        today = timezone.localdate()
        food_logs = FoodLog.objects.filter(user=user, logged_at__date=today)
        water_log = WaterLog.objects.filter(user=user, logged_at=today).first()
        
        totals = food_logs.aggregate(
            c=Sum('calories'), p=Sum('protein'), ch=Sum('carbs'), f=Sum('fat')
        )
        
        cal_in = float(totals['c'] or 0)
        prot_in = float(totals['p'] or 0)
        carb_in = float(totals['ch'] or 0)
        fat_in = float(totals['f'] or 0)
        water_in = water_log.amount if water_log else 0

        meal_list = []
        for fl in food_logs:
            meal_list.append(f"- {fl.food_name} ({fl.quantity}x {fl.meal_type}): {fl.calories} kcal, {fl.protein}g P, {fl.carbs}g C, {fl.fat}g F")
        meals_consumed = "\n".join(meal_list) if meal_list else "None logged yet."

        system_instruction = (
            f"You are a premium Rabbit Fitness & Nutrition Coach. The user is a {profile.gender or 'person'} "
            f"who is {profile.age or 25} years old, {profile.height or 175}cm tall, weighing {goal.current_weight or 70}kg. "
            f"Their goal is {goal.get_goal_type_display()} (target weight: {goal.target_weight}kg).\n\n"
            f"User's Daily Targets:\n"
            f"- Calories: {goal.daily_calorie_goal} kcal\n"
            f"- Protein: {goal.daily_protein_goal}g\n"
            f"- Carbs: {goal.daily_carbs_goal}g\n"
            f"- Fats: {goal.daily_fats_goal}g\n"
            f"- Water: {goal.daily_water_goal}ml\n\n"
            f"User's Actual Intake Today ({today.strftime('%Y-%m-%d')}):\n"
            f"- Calories Consumed: {cal_in} kcal\n"
            f"- Protein Consumed: {prot_in}g\n"
            f"- Carbs Consumed: {carb_in}g\n"
            f"- Fats Consumed: {fat_in}g\n"
            f"- Water Consumed: {water_in}ml\n"
            f"Meals Logged Today:\n{meals_consumed}\n\n"
            f"INSTRUCTIONS:\n"
            f"- Be a supportive, expert, and conversational coach.\n"
            f"- Always use the user's actual intake and targets to provide personalized advice.\n"
            f"- Explain details fully, clarify user doubts, and discuss their logs naturally. Avoid empty pleasantries and fluff.\n"
            f"- Keep responses structured, concise, and highly informative, using bold figures and formatting for readability. Do not cut responses off too short."
        )

        if action_type == 'analyze':
            prompt = (
                f"{system_instruction}\n\n"
                f"Please analyze my nutrition logs for today and provide a structured, complete feedback summary on my intake, including what targets I met/missed, meal suggestions if needed, and one key advice tip."
            )
            
            try:
                response = generate_gemini_content(prompt)
                text = response.text
                
                # Save recommendation
                AIRecommendation.objects.create(
                    user=user,
                    input_query=f"Daily Analysis for {today}",
                    recommendation_text=text
                )
                return Response({'recommendation': text})
            except ValueError as ve:
                return Response({
                    'recommendation': "The AI Coach is currently offline (no Gemini API keys are configured in environment settings). Please configure GEMINI_API_KEY to activate it."
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        elif action_type == 'chat':
            user_message = request.data.get('message', '').strip()
            if not user_message:
                return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
            
            prompt = (
                f"{system_instruction}\n\n"
                f"The user says: '{user_message}'\n\n"
                f"Discuss and respond to this message. Clarify doubts, give details from their logs if relevant, and chat normally to assist them."
            )
            
            try:
                response = generate_gemini_content(prompt)
                text = response.text
                
                AIRecommendation.objects.create(
                    user=user,
                    input_query=user_message,
                    recommendation_text=text
                )
                return Response({'recommendation': text})
            except ValueError as ve:
                return Response({
                    'recommendation': "The AI Coach is currently offline (no Gemini API keys are configured in environment settings). Please configure GEMINI_API_KEY to activate it."
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

class AIFoodEstimateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'error': 'Food description cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        prompt = (
            "You are a professional nutritionist. Estimate the nutritional values of the food description provided. "
            "Respond ONLY with a valid raw JSON object. Do not include markdown code block formatting (such as ```json ... ```) or any explanation. "
            "If the description contains multiple items, sum up their values. "
            "Ensure the keys and values match the following format exactly: "
            '{"name": "Food Name", "calories": 0.00, "protein": 0.00, "carbs": 0.00, "fat": 0.00} '
            "All values should be floats representing the nutritional count for the entire described amount.\n\n"
            f"Description: {text}"
        )

        try:
            response = generate_gemini_content(prompt)
            resp_text = response.text.strip()
            
            # Clean markdown code block wraps if model generates them anyway
            if resp_text.startswith("```"):
                lines = resp_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                resp_text = "\n".join(lines).strip()
            
            # Parse the JSON response
            data = json.loads(resp_text)
            
            # Ensure required keys exist
            required_keys = ['name', 'calories', 'protein', 'carbs', 'fat']
            for key in required_keys:
                if key not in data:
                    raise KeyError(f"Missing key: {key}")
            
            return Response(data)
        except ValueError as ve:
            return Response({
                'error': 'No Gemini API keys are configured in environment settings.'
            }, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError:
            response_text = ""
            try:
                response_text = response.text[:200]
            except Exception:
                pass
            return Response({
                'error': f"Failed to parse AI response as JSON: {response_text}"
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FavoriteFoodView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        foods = FoodItem.objects.filter(favorite_by=request.user)
        return Response(FoodItemSerializer(foods, many=True).data)

    def post(self, request):
        food_id = request.data.get('food_item_id')
        if food_id:
            food = get_object_or_404(FoodItem, id=food_id)
            food.favorite_by.add(request.user)
            return Response(FoodItemSerializer(food).data, status=status.HTTP_200_OK)
        else:
            # Create a new FoodItem and favorite it
            serializer = FoodItemSerializer(data=request.data)
            if serializer.is_valid():
                food = serializer.save(created_by=request.user)
                food.favorite_by.add(request.user)
                return Response(FoodItemSerializer(food).data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        food_id = request.query_params.get('food_item_id')
        if not food_id:
            return Response({'error': 'food_item_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        food = get_object_or_404(FoodItem, id=food_id)
        food.favorite_by.remove(request.user)
        return Response({'status': 'removed from favorites'}, status=status.HTTP_200_OK)


class DailyRoutineViewSet(viewsets.ModelViewSet):
    serializer_class = DailyRoutineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        today = timezone.localdate()
        
        # Allow filtering by date
        date_str = self.request.query_params.get('date', None)
        if date_str:
            try:
                today = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        queryset = DailyRoutine.objects.filter(user=user, logged_at=today)
        
        # Auto-populate default habits if none exist for today
        if not queryset.exists() and today == timezone.localdate():
            default_tasks = [
                "Drink target water intake",
                "Log all daily meals",
                "Record body weight",
                "Complete 30-minute workout"
            ]
            for task in default_tasks:
                DailyRoutine.objects.get_or_create(
                    user=user,
                    task_name=task,
                    logged_at=today,
                    defaults={'is_completed': False}
                )
            queryset = DailyRoutine.objects.filter(user=user, logged_at=today)
            
        # Dynamically update default routines based on today's progress
        if today == timezone.localdate():
            # 1. Drink target water intake
            water_log = WaterLog.objects.filter(user=user, logged_at=today).first()
            goal, _ = FitnessGoal.objects.get_or_create(user=user)
            if water_log and water_log.amount >= goal.daily_water_goal:
                DailyRoutine.objects.filter(user=user, task_name="Drink target water intake", logged_at=today).update(is_completed=True)
            else:
                DailyRoutine.objects.filter(user=user, task_name="Drink target water intake", logged_at=today).update(is_completed=False)

            # 2. Log all daily meals (Breakfast + Lunch + Dinner)
            logged_meals = FoodLog.objects.filter(user=user, logged_at__date=today).values_list('meal_type', flat=True).distinct()
            if 'breakfast' in logged_meals and 'lunch' in logged_meals and 'dinner' in logged_meals:
                DailyRoutine.objects.filter(user=user, task_name="Log all daily meals", logged_at=today).update(is_completed=True)
            else:
                DailyRoutine.objects.filter(user=user, task_name="Log all daily meals", logged_at=today).update(is_completed=False)

            # 3. Record body weight
            weight_exists = WeightLog.objects.filter(user=user, logged_at=today).exists()
            if weight_exists:
                DailyRoutine.objects.filter(user=user, task_name="Record body weight", logged_at=today).update(is_completed=True)
            else:
                DailyRoutine.objects.filter(user=user, task_name="Record body weight", logged_at=today).update(is_completed=False)
            
        return queryset.order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


DEFAULT_DIET_PLAN = [
    {
        'meal_type': 'breakfast',
        'items': "* Oats – 100g\n* Milk – 250ml\n* Peanut Butter – 2 tbsp\n* Banana – 2",
        'calories': 939.00,
        'protein': 35.00,
        'carbs': 138.00,
        'fat': 32.00,
    },
    {
        'meal_type': 'lunch',
        'items': "* Cooked Rice – 650g\n* Dal – 1.5 cups\n* Curd – 100g\n* Boiled Eggs – 2",
        'calories': 1345.00,
        'protein': 49.50,
        'carbs': 231.00,
        'fat': 21.00,
    },
    {
        'meal_type': 'snack',
        'items': "* Egg Whites – 6\n* Boiled Chana – 100g\n* Sprouts – 50g\n* Sweet Corn – 50g",
        'calories': 329.00,
        'protein': 35.00,
        'carbs': 41.00,
        'fat': 4.00,
    },
    {
        'meal_type': 'dinner',
        'items': "* Roti – 4\n* Ghee – 1 tbsp\n* Soya Chunks (dry weight) – 50g\n* Cooked Rice – 225g\n* Curd – 100g",
        'calories': 966.00,
        'protein': 46.50,
        'carbs': 148.00,
        'fat': 22.50,
    },
]


class DietMealViewSet(viewsets.ModelViewSet):
    serializer_class = DietMealSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = DietMeal.objects.filter(user=user)
        if not queryset.exists():
            # Seed the default plan
            for meal in DEFAULT_DIET_PLAN:
                DietMeal.objects.create(
                    user=user,
                    meal_type=meal['meal_type'],
                    items=meal['items'],
                    calories=meal['calories'],
                    protein=meal['protein'],
                    carbs=meal['carbs'],
                    fat=meal['fat']
                )
            queryset = DietMeal.objects.filter(user=user)
        return queryset.order_by('id')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DailyDietCheckViewSet(viewsets.ModelViewSet):
    serializer_class = DailyDietCheckSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        today = timezone.localdate()
        date_str = self.request.query_params.get('date', None)
        if date_str:
            try:
                today = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        queryset = DailyDietCheck.objects.filter(user=user, logged_at=today)
        return queryset.order_by('id')

    @action(detail=False, methods=['POST'], url_path='toggle')
    def toggle(self, request):
        user = request.user
        meal_type = request.data.get('meal_type')
        is_eaten = request.data.get('is_eaten')
        date_str = request.data.get('date', None)
        
        if not meal_type:
            return Response({'error': 'meal_type is required'}, status=status.HTTP_400_BAD_REQUEST)
        if is_eaten is None:
            return Response({'error': 'is_eaten is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        today = timezone.localdate()
        if date_str:
            try:
                today = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
                
        # Get the corresponding DietMeal to retrieve macros
        diet_meal = DietMeal.objects.filter(user=user, meal_type=meal_type).first()
        if not diet_meal:
            for meal in DEFAULT_DIET_PLAN:
                DietMeal.objects.get_or_create(
                    user=user,
                    meal_type=meal['meal_type'],
                    defaults={
                        'items': meal['items'],
                        'calories': meal['calories'],
                        'protein': meal['protein'],
                        'carbs': meal['carbs'],
                        'fat': meal['fat']
                    }
                )
            diet_meal = DietMeal.objects.filter(user=user, meal_type=meal_type).first()

        # Find or create check log
        check, created = DailyDietCheck.objects.get_or_create(
            user=user,
            meal_type=meal_type,
            logged_at=today,
            defaults={'is_eaten': False}
        )

        if is_eaten:
            check.is_eaten = True
            if not check.linked_log:
                meal_display = dict(DietMeal.MEAL_CHOICES).get(meal_type, meal_type.capitalize())
                food_name = f"Diet Plan: {meal_display}"
                
                # Make local timezone aware datetime
                current_time = timezone.localtime(timezone.now()).time()
                naive_datetime = timezone.datetime.combine(today, current_time)
                logged_datetime = timezone.make_aware(naive_datetime)
                
                food_log = FoodLog.objects.create(
                    user=user,
                    food_name=food_name,
                    meal_type=meal_type,
                    quantity=1.00,
                    calories=diet_meal.calories,
                    protein=diet_meal.protein,
                    carbs=diet_meal.carbs,
                    fat=diet_meal.fat,
                    logged_at=logged_datetime
                )
                check.linked_log = food_log
            check.save()
        else:
            check.is_eaten = False
            if check.linked_log:
                food_log = check.linked_log
                check.linked_log = None
                check.save()
                food_log.delete()
            else:
                check.save()
                
        return Response(DailyDietCheckSerializer(check).data, status=status.HTTP_200_OK)
