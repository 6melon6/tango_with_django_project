from datetime import date, datetime

from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm, FoodRecordForm, FoodCategoryForm, FoodForm
from .models import FoodCategory, Food, FoodRecord


def get_dietary_suggestions(total_calories, meal_subtotals):
    """根据摄入热量提供饮食建议"""
    suggestions = []
    if total_calories == 0:
        return suggestions

    if total_calories < 1200:
        suggestions.append(("warning", "今天的摄入量偏低，建议均衡饮食。"))
    elif 1200 <= total_calories <= 2000:
        suggestions.append(("success", "很好！您的摄入量在健康范围内。"))
    else:
        suggestions.append(("danger", "您已超过推荐摄入量，建议选择更清淡的食物。"))

    meal_labels = {'breakfast': '早餐', 'lunch': '午餐', 'dinner': '晚餐', 'snack': '零食'}
    for meal_type, subtotal in meal_subtotals.items():
        if subtotal > 800:
            label = meal_labels.get(meal_type, meal_type)
            suggestions.append(("info", f"您的{label}摄入量较高，建议平衡各餐。"))

    return suggestions


def register_view(request):
    """用户注册视图"""
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
    """用户登录视图"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    # 设置中文标签后缀
    form.label_suffix = ''
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """用户登出视图"""
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    """仪表盘视图 - 显示当日饮食汇总"""
    today = date.today()

    # 获取记录
    entries = FoodRecord.objects.filter(user=request.user, record_date=today).select_related('food', 'food__category')

    # 计算总热量 - 直接在 aggregate 中计算，避免 MySQL annotate 冲突
    total_calories = entries.aggregate(
        total=Sum(F('quantity') * F('food__calories_per_100g') / 100)
    )['total'] or 0

    # 按餐次分类的小计 - 使用表达式
    meal_subtotals = entries.values('meal_type').annotate(
        subtotal=Sum(F('quantity') * F('food__calories_per_100g') / 100)
    )
    meal_data = {item['meal_type']: item['subtotal'] for item in meal_subtotals}

    # 准备 Chart.js 饼图数据
    meal_labels = {'breakfast': '早餐', 'lunch': '午餐', 'dinner': '晚餐', 'snack': '零食'}
    chart_labels = [meal_labels.get(k, k) for k in meal_data.keys()]
    chart_data = [round(v, 1) for v in meal_data.values()]

    # 按餐次分组记录（带热量注解）
    grouped_entries = {}
    for meal_type, label in FoodRecord.MEAL_CHOICES:
        grouped_entries[label] = entries.filter(meal_type=meal_type).annotate(
            calculated_total=F('quantity') * F('food__calories_per_100g') / 100
        )

    # 获取最近 5 条饮食记录（不限日期）
    recent_records = FoodRecord.objects.filter(user=request.user).select_related('food', 'food__category').annotate(
        calculated_total=F('quantity') * F('food__calories_per_100g') / 100
    ).order_by('-record_date', '-id')[:5]

    # 饮食建议
    suggestions = get_dietary_suggestions(total_calories, meal_data)

    context = {
        'total_calories': round(total_calories, 1),
        'meal_data': meal_data,
        'grouped_entries': grouped_entries,
        'suggestions': suggestions,
        'today': today,
        'recent_records': recent_records,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'dashboard.html', context)


@login_required
def history_view(request):
    """历史记录视图 - 支持日期查询、日期范围查询、餐次筛选"""
    today_str = date.today().strftime('%Y-%m-%d')
    entries = None
    chart_data = []
    query_date = request.GET.get('date', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    meal_type = request.GET.get('meal_type', '')

    # 默认显示今天
    if not query_date and not start_date and not end_date:
        query_date = today_str

    # 基础查询
    base_qs = FoodRecord.objects.filter(user=request.user)

    # 餐次筛选
    if meal_type:
        base_qs = base_qs.filter(meal_type=meal_type)

    if query_date:
        try:
            parsed_date = datetime.strptime(query_date, '%Y-%m-%d').date()
            # entries 使用 annotate 添加热量字段
            entries = base_qs.select_related('food', 'food__category').annotate(
                calculated_total=F('quantity') * F('food__calories_per_100g') / 100
            ).filter(record_date=parsed_date).order_by('-record_date', '-id')
            # chart_data 使用 aggregate 直接计算
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

    # 转换日期为字符串以便 JSON 序列化
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
    """记录列表视图 - 按日期显示"""
    # 获取查询日期，默认今天
    query_date = request.GET.get('date', '')
    if not query_date:
        query_date = date.today().strftime('%Y-%m-%d')

    # 解析日期
    selected_date = None
    entries = []
    total_calories = 0

    try:
        selected_date = datetime.strptime(query_date, '%Y-%m-%d').date()
        # 获取该日期的记录 - 先排序获取 entries
        qs = FoodRecord.objects.filter(user=request.user, record_date=selected_date)
        entries = qs.select_related('food', 'food__category').order_by('-id')
        # 单独计算总热量（避免 MySQL annotate/aggregate 冲突）
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
    """添加饮食记录视图"""
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
    """编辑饮食记录视图"""
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
    """删除饮食记录视图"""
    record = get_object_or_404(FoodRecord, id=id, user=request.user)
    if request.method == 'POST':
        record.delete()
        return redirect('record_list')
    return render(request, 'record/delete.html', {'entry': record})


# ========== 食物分类管理视图 ==========

@login_required
def category_list_view(request):
    """分类列表视图"""
    categories = FoodCategory.objects.all().order_by('category_name')
    return render(request, 'category/category_list.html', {'categories': categories})


@login_required
def category_add_view(request):
    """添加分类视图"""
    if request.method == 'POST':
        form = FoodCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = FoodCategoryForm()
    return render(request, 'category/category_form.html', {'form': form, 'action': '添加'})


@login_required
def category_edit_view(request, id):
    """编辑分类视图"""
    category = get_object_or_404(FoodCategory, id=id)
    if request.method == 'POST':
        form = FoodCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = FoodCategoryForm(instance=category)
    return render(request, 'category/category_form.html', {'form': form, 'action': '编辑', 'category': category})


@login_required
def category_delete_view(request, id):
    """删除分类视图"""
    category = get_object_or_404(FoodCategory, id=id)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'category/category_delete.html', {'category': category})


# ========== 食物库管理视图 ==========

@login_required
def food_list_view(request):
    """食物库列表视图 - 支持搜索"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')

    foods = Food.objects.all().select_related('category').order_by('category__category_name', 'food_name')

    # 搜索过滤
    if search_query:
        foods = foods.filter(food_name__icontains=search_query)

    # 分类过滤
    if category_filter:
        foods = foods.filter(category_id=category_filter)

    # 获取所有分类用于过滤下拉框
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
    """添加食物到食物库视图"""
    if request.method == 'POST':
        form = FoodForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('food_list')
    else:
        form = FoodForm()
    return render(request, 'food_library/food_form.html', {'form': form, 'action': '添加'})


@login_required
def food_library_edit_view(request, id):
    """编辑食物库中的食物视图"""
    food = get_object_or_404(Food, id=id)
    if request.method == 'POST':
        form = FoodForm(request.POST, instance=food)
        if form.is_valid():
            form.save()
            return redirect('food_list')
    else:
        form = FoodForm(instance=food)
    return render(request, 'food_library/food_form.html', {'form': form, 'action': '编辑', 'food': food})


@login_required
def food_library_delete_view(request, id):
    """删除食物库中的食物视图"""
    food = get_object_or_404(Food, id=id)
    if request.method == 'POST':
        food.delete()
        return redirect('food_list')
    return render(request, 'food_library/food_delete.html', {'food': food})
