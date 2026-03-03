from datetime import date, datetime
from django.db.models import Avg
from datetime import timedelta
import json
from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm, FoodRecordForm, FoodCategoryForm, FoodForm
from .models import FoodCategory, Food, FoodRecord


def get_dietary_suggestions(total_calories, meal_subtotals):
    """Provide dietary advice based on calorie intake"""
    suggestions = []
    if total_calories == 0:
        return suggestions

    if total_calories < 1200:
        suggestions.append(("warning", "Today's intake is relatively low; a balanced diet is recommended."))
    elif 1200 <= total_calories <= 2000:
        suggestions.append(("success", "Great! Your intake is within a healthy range."))
    else:
        suggestions.append(("danger", "You have exceeded the recommended intake, it is advisable to choose lighter foods."))

    meal_labels = {'breakfast': 'Breakfast', 'lunch': 'Lunch', 'dinner': 'Dinner', 'snack': 'snack'}
    for meal_type, subtotal in meal_subtotals.items():
        if subtotal > 800:
            label = meal_labels.get(meal_type, meal_type)
            suggestions.append(("info", f"Your {label} The intake is relatively high, it is recommended to balance each meal."))

    return suggestions


def register_view(request):
    """User Registration View"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """User Login View"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    # Set Chinese label suffix
    form.label_suffix = ''
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """User Logout View"""
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
        """Enhanced Dashboard View with Statistics & Charts"""

        user = request.user
        today = date.today()

        # All user records
        all_records = FoodRecord.objects.filter(user=user)

        # Today's records
        today_records = all_records.filter(record_date=today)

        # ========= STAT CARDS DATA =========

        # Total calories today
        total_today = today_records.aggregate(
            total=Sum(F('quantity') * F('food__calories_per_100g') / 100)
        )['total'] or 0

        # Total records count
        records_count = all_records.count()

        # Average calories per record
        avg_calories = all_records.aggregate(
            avg=Avg(F('quantity') * F('food__calories_per_100g') / 100)
        )['avg'] or 0

        # Last entry
        last_entry = all_records.order_by('-record_date', '-id').first()
        last_entry_time = last_entry.record_date if last_entry else None

        # ========= LAST 7 DAYS TREND =========

        weekly_labels = []
        weekly_calories = []

        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            weekly_labels.append(day.strftime('%m-%d'))

            daily_total = all_records.filter(record_date=day).aggregate(
                total=Sum(F('quantity') * F('food__calories_per_100g') / 100)
            )['total'] or 0

            weekly_calories.append(round(float(daily_total), 1))

        # ========= MEAL DISTRIBUTION =========

        meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
        meal_distribution = []

        for meal in meal_types:
            meal_total = all_records.filter(meal_type=meal).aggregate(
                total=Sum(F('quantity') * F('food__calories_per_100g') / 100)
            )['total'] or 0
            meal_distribution.append(round(float(meal_total), 1))

        context = {
            # Stats cards
            'total_today': round(total_today, 1),
            'records_count': records_count,
            'avg_calories': round(avg_calories, 1),
            'last_entry': last_entry_time,

            # Charts
            'weekly_labels': json.dumps(weekly_labels),
            'weekly_calories': json.dumps(weekly_calories),
            'meal_distribution': json.dumps(meal_distribution),
        }

        return render(request, 'dashboard.html', context)


@login_required
def history_view(request):
    """History View - Supports Date Query, Date Range Query, and Meal Filtering"""
    today_str = date.today().strftime('%Y-%m-%d')
    entries = None
    chart_data = []
    query_date = request.GET.get('date', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    meal_type = request.GET.get('meal_type', '')

    # Default to show today
    if not query_date and not start_date and not end_date:
        query_date = today_str

    # Basic Query
    base_qs = FoodRecord.objects.filter(user=request.user)

    # Meal Selection
    if meal_type:
        base_qs = base_qs.filter(meal_type=meal_type)

    if query_date:
        try:
            parsed_date = datetime.strptime(query_date, '%Y-%m-%d').date()
            # Use annotate on entries to add a calorie field
            entries = base_qs.select_related('food', 'food__category').annotate(
                calculated_total=F('quantity') * F('food__calories_per_100g') / 100
            ).filter(record_date=parsed_date).order_by('-record_date', '-id')
            # chart_data calculates directly using aggregate
            chart_data = list(
                base_qs.filter(record_date=parsed_date)
                .values('record_date')
                .annotate(total=Sum(F('quantity') * F('food__calories_per_100g') / 100))
                .order_by('record_date')
            )
        except ValueError:
            entries = base_qs.none()
    elif start_date and end_date:
        try:
            parsed_start = datetime.strptime(start_date, '%Y-%m-%d').date()
            parsed_end = datetime.strptime(end_date, '%Y-%m-%d').date()
            entries = base_qs.select_related('food', 'food__category').annotate(
                calculated_total=F('quantity') * F('food__calories_per_100g') / 100
            ).filter(record_date__gte=parsed_start, record_date__lte=parsed_end).order_by('-record_date', '-id')
            chart_data = list(
                base_qs.filter(record_date__gte=parsed_start, record_date__lte=parsed_end)
                .values('record_date')
                .annotate(total=Sum(F('quantity') * F('food__calories_per_100g') / 100))
                .order_by('record_date')
            )
        except ValueError:
            entries = base_qs.none()

    # Convert the date to a string for JSON serialization
    for item in chart_data:
        item['record_date'] = item['record_date'].strftime('%Y-%m-%d')

    context = {
        'entries': entries,
        'chart_data': chart_data,
        'query_date': query_date,
        'start_date': start_date,
        'end_date': end_date,
        'meal_type': meal_type,
        'has_results': entries is not None,
        'meal_choices': FoodRecord.MEAL_CHOICES,
    }
    return render(request, 'history/history.html', context)


@login_required
def record_list_view(request):
    # Record List View - Display by Date
    # Get the query date, default is today
    query_date = request.GET.get('date', '')
    if not query_date:
        query_date = date.today().strftime('%Y-%m-%d')

    # Parsing Date
    selected_date = None
    entries = []
    total_calories = 0

    try:
        selected_date = datetime.strptime(query_date, '%Y-%m-%d').date()
        # Get the records for this date - first sort to get entries
        qs = FoodRecord.objects.filter(user=request.user, record_date=selected_date)
        entries = qs.select_related('food', 'food__category').order_by('-id')
        # Calculate the total calories separately (to avoid MySQL annotate/aggregate conflicts)
        total_calories = qs.aggregate(
            total=Sum(F('quantity') * F('food__calories_per_100g') / 100)
        )['total'] or 0
    except ValueError:
        pass

    context = {
        'entries': entries,
        'selected_date': selected_date,
        'query_date': query_date,
        'total_calories': round(total_calories, 1),
    }
    return render(request, 'record/record_list.html', context)


@login_required
def add_food_view(request):
    """Add Diet Record View"""
    if request.method == 'POST':
        form = FoodRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.user = request.user
            record.save()
            return redirect('record_list')
    else:
        form = FoodRecordForm()
    return render(request, 'record/add.html', {'form': form, 'today': date.today()})


@login_required
def edit_food_view(request, id):
    """Edit Diet Record View"""
    record = get_object_or_404(FoodRecord, id=id, user=request.user)
    if request.method == 'POST':
        form = FoodRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('record_list')
    else:
        form = FoodRecordForm(instance=record)
    return render(request, 'record/edit.html', {'form': form, 'entry': record})


@login_required
def delete_food_view(request, id):
    """Delete Diet Record View"""
    record = get_object_or_404(FoodRecord, id=id, user=request.user)
    if request.method == 'POST':
        record.delete()
        return redirect('record_list')
    return render(request, 'record/delete.html', {'entry': record})


# ========== Food Classification Management View ==========

@login_required
def category_list_view(request):
    # Category List View
    categories = FoodCategory.objects.all().order_by('category_name')
    return render(request, 'category/category_list.html', {'categories': categories})


@login_required
def category_add_view(request):
    # Add category view
    if request.method == 'POST':
        form = FoodCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = FoodCategoryForm()
    return render(request, 'category/category_form.html', {'form': form, 'action': 'Add'})


@login_required
def category_edit_view(request, id):
    # Edit Category View
    category = get_object_or_404(FoodCategory, id=id)
    if request.method == 'POST':
        form = FoodCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = FoodCategoryForm(instance=category)
    return render(request, 'category/category_form.html', {'form': form, 'action': 'Edit', 'category': category})


@login_required
def category_delete_view(request, id):
    # Delete category view
    category = get_object_or_404(FoodCategory, id=id)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'category/category_delete.html', {'category': category})


# ========== Food Inventory Management View ==========

@login_required
def food_list_view(request):
   # Food Library List View - Supports Search
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    foods = Food.objects.all().select_related('category').order_by('category__category_name', 'food_name')

    # Search Filter
    if search_query:
        foods = foods.filter(food_name__icontains=search_query)

    # Category Filtering
    if category_filter:
        foods = foods.filter(category_id=category_filter)

    # Get all categories for filtering dropdown
    categories = FoodCategory.objects.all().order_by('category_name')

    context = {
        'foods': foods,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    return render(request, 'food_library/food_list.html', context)


@login_required
def food_library_add_view(request):
    # Add food to the food library view
    if request.method == 'POST':
        form = FoodForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('food_list')
    else:
        form = FoodForm()
    return render(request, 'food_library/food_form.html', {'form': form, 'action': 'Add'})


@login_required
def food_library_edit_view(request, id):
    # Edit the food view in the food library
    food = get_object_or_404(Food, id=id)
    if request.method == 'POST':
        form = FoodForm(request.POST, instance=food)
        if form.is_valid():
            form.save()
            return redirect('food_list')
    else:
        form = FoodForm(instance=food)
    return render(request, 'food_library/food_form.html', {'form': form, 'action': 'action', 'food': food})


@login_required
def food_library_delete_view(request, id):
    # Delete the food view in the food library
    food = get_object_or_404(Food, id=id)
    if request.method == 'POST':
        food.delete()
        return redirect('food_list')
    return render(request, 'food_library/food_delete.html', {'food': food})
