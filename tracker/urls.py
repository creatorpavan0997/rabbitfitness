from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

from . import views
from . import api_views

# REST API Router
router = DefaultRouter()
router.register(r'food-log', api_views.FoodLogViewSet, basename='food-log')
router.register(r'weight-log', api_views.WeightLogViewSet, basename='weight-log')
router.register(r'water-log', api_views.WaterLogViewSet, basename='water-log')
router.register(r'routines', api_views.DailyRoutineViewSet, basename='routines')
router.register(r'diet-meals', api_views.DietMealViewSet, basename='diet-meals')
router.register(r'diet-checks', api_views.DailyDietCheckViewSet, basename='diet-checks')


urlpatterns = [
    # Template Web Views
    path('', views.dashboard_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='tracker/auth/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    path('food/', views.food_log_view, name='food_log'),
    path('weight/', views.weight_tracker_view, name='weight_tracker'),
    path('water/', views.water_tracker_view, name='water_tracker'),
    path('ai-coach/', views.ai_coach_view, name='ai_coach'),
    path('diet-plan/', views.diet_plan_view, name='diet_plan'),
    path('cooking-timer/', views.cooking_timer_view, name='cooking_timer'),
    
    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='tracker/auth/password_reset.html',
        email_template_name='tracker/auth/password_reset_email.html',
        subject_template_name='tracker/auth/password_reset_subject.txt'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='tracker/auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='tracker/auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='tracker/auth/password_reset_complete.html'
    ), name='password_reset_complete'),

    # REST API View endpoints
    path('api/', include(router.urls)),
    path('api/dashboard-data/', api_views.DashboardDataView.as_view(), name='api_dashboard_data'),
    path('api/food/search/', api_views.FoodSearchView.as_view(), name='api_food_search'),
    path('api/food/save-food/', api_views.FoodSaveView.as_view(), name='api_food_save'),
    path('api/food/ai-estimate/', api_views.AIFoodEstimateView.as_view(), name='api_food_ai_estimate'),
    path('api/food/favorite/', api_views.FavoriteFoodView.as_view(), name='api_food_favorite'),
    path('api/ai-coach/', api_views.AICoachView.as_view(), name='api_ai_coach'),
]
