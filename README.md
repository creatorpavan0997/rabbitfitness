# Rabbit Fitness

A modern, responsive production-ready Fitness and Nutrition web application built with **Python Django 5**, **Django REST Framework (DRF)**, **Bootstrap 5**, **Chart.js**, **Open Food Facts API**, and the **Gemini API** for personalized AI coaching feedback.

---

## ⚡ Key Features

1. **User Authentication & Profiles**:
   - Secure registration, login, logout, password resets, and user physical profile tracking.
2. **Interactive Dashboard**:
   - Dynamic SVG calorie rings, macro targets progress bars, and Chart.js visualizations (weekly trends, daily macro distributions, monthly weight progress).
3. **Smart Food Tracker**:
   - Log foods manually or query the Open Food Facts API directly. Save favorite food choices.
4. **Hydration (Water) Logger**:
   - Visual cup fill animation showing hydration percentage with quick add shortcuts (+250ml, +500ml, +750ml).
5. **Progressive Weight Tracker**:
   - Log daily weight and visualize progress against target weight dynamically on a Chart.js line graph.
6. **Personal AI Coach**:
   - Integrates with the **Gemini API** (`gemini-1.5-flash`) to generate contextual feedback based on daily logs, answer general training questions, suggest recipes, and recommend protein sources.

---

## 📂 Project Structure

```
ai_fitness_tracker/
├── manage.py                   # Django CLI executable
├── requirements.txt            # Python dependencies list
├── .env.example                # Config blueprint for environment variables
├── .env                        # Local configurations (ignored by git)
├── static/                     # Global static directory
│   ├── css/
│   │   └── style.css           # Premium HSL dark-mode styling and animations
│   └── js/
│       └── app.js              # Client-side theme controller & API fetch utility
├── fitness_tracker/
│   ├── __init__.py
│   ├── settings.py             # Project configurations (CORS, REST, dot-env)
│   ├── urls.py                 # Main URL routing (serves static/media)
│   └── wsgi.py
└── tracker/                    # Main application app
    ├── admin.py                # Admin portal configurations
    ├── apps.py
    ├── models.py               # UserProfile, FitnessGoal, FoodLog, WeightLog, WaterLog, etc.
    ├── forms.py                # Form classes for profile updates and registration
    ├── serializers.py          # DRF Serializers for API validation
    ├── api_views.py            # DRF ViewSets & custom endpoint classes
    ├── urls.py                 # App level template & API url mappings
    ├── tests.py                # Unit test suites (signals, logging validation)
    └── templates/              # HTML Templates
        └── tracker/
            ├── base.html       # Base HTML skeleton & theme toggle
            ├── dashboard.html  # Main analytics display & Chart.js instances
            ├── food_log.html   # Food logs & debounced search engine
            ├── water_tracker.html # Wave-animated cup water logging
            ├── weight_tracker.html # Weight logging & progression chart
            ├── ai_coach.html   # Live chat and daily analyzer
            └── auth/           # Login, registration, profile forms & password reset
```

---

## 🛠️ Installation & Setup Guide

### 1. Prerequisites
- **Python 3.12+**
- **pip**

### 2. Clone and Initialize Workspace
Create a folder structure and download dependencies:
```bash
git clone <repository-url>
cd ai_fitness_tracker
```

### 3. Install Package Dependencies
Install the requirements globally or inside a virtual environment:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file from the example blueprint:
```bash
cp .env.example .env
```
Open the `.env` file and input your keys:
```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
GEMINI_API_KEY=your-gemini-api-key-here
```

*Note: If no `GEMINI_API_KEY` is supplied, the coach will fall back gracefully to a message informing you that the coach is currently offline.*

### 5. Setup Database & Migrations
Create the SQLite database and run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)
Create an admin user to browse model databases at `http://127.0.0.1:8000/admin/`:
```bash
python manage.py createsuperuser
```

### 7. Run Server
Launch the development server:
```bash
python manage.py runserver
```
Visit the application at: **`http://127.0.0.1:8000/`**

---

## 🧪 Running Unit Tests

Run the backend test cases using:
```bash
python manage.py test
```

---

## 📡 REST API Documentation

All API endpoints are protected and require a logged-in session cookie (standard SessionAuthentication).

| Endpoint | Method | Description | Request Body Example |
| :--- | :--- | :--- | :--- |
| `/api/food-log/` | `GET` | List today's food logs (use `?date=YYYY-MM-DD` query param to filter). | |
| `/api/food-log/` | `POST` | Create a new food log. Automatically computes macros if `food_item` is set. | `{"food_item": 1, "meal_type": "lunch", "quantity": 1.5}` |
| `/api/food-log/<id>/` | `DELETE` | Delete a food log entry. | |
| `/api/water-log/` | `GET` | List historical water logs. | |
| `/api/water-log/` | `POST` | Add/Increment water logged. | `{"amount": 250}` |
| `/api/water-log/quick-add/` | `POST` | Fast action to increment today's water. Defaults to `250` ml. | `{"amount": 500}` |
| `/api/weight-log/` | `GET` | List historical weights. | |
| `/api/weight-log/` | `POST` | Log or update weight for a date. Updates current weight on Profile. | `{"weight": 70.5, "logged_at": "2026-06-13"}` |
| `/api/dashboard-data/` | `GET` | Retrieve today's nutrition sums, goal targets, and historical chart arrays. | |
| `/api/food/search/` | `GET` | Search custom foods and matches on the Open Food Facts API (use `?q=banana`). | |
| `/api/food/save-food/` | `POST` | Cache an Open Food Facts product entry into local `FoodItem` table. | `{"name": "Banana", "calories": 89, "protein": 1.1, "carbs": 22.8, "fat": 0.3, "serving_size": "100g", "barcode": "12345"}` |
| `/api/ai-coach/` | `GET` | List last 10 recommendation advices generated. | |
| `/api/ai-coach/` | `POST` | Trigger AI Coach response (either query `chat` or today's logs `analyze`). | `{"action": "chat", "message": "Give me 3 high protein breakfast ideas"}` |

---

## 🚀 Production Deployment Instructions

1. **Change Security Configurations** (`fitness_tracker/settings.py`):
   - Set `DEBUG=False` in your environment variables.
   - Configure a secure random `SECRET_KEY`.
   - Update `ALLOWED_HOSTS` with your domain names (e.g. `ALLOWED_HOSTS=my-fitness-app.com`).
2. **Database Configuration**:
   - Provision a PostgreSQL cluster.
   - Set the `DATABASE_URL` environment variable. The app automatically connects when configured.
3. **Static File Collection**:
   - Collect static resources to serve via Nginx/WhiteNoise:
     ```bash
     python manage.py collectstatic --noinput
     ```
4. **Deploy Server**:
   - Use a WSGI server like **Gunicorn**:
     ```bash
     gunicorn fitness_tracker.wsgi:application --bind 0.0.0.0:8000
     ```
# rabbi
# rabbi
