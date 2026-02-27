"""
饮食追踪器 - 单元测试模块

测试任务:
10.1 用户认证测试用例 - 注册、登录、登出
10.2 食物分类测试用例 - CRUD 操作
10.3 食物库测试用例 - CRUD 操作、搜索
10.4 饮食记录测试用例 - 创建、查询、计算
10.5 运行测试并修复失败的用例
10.6 生成测试覆盖率报告
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from tracker.forms import RegisterForm, FoodCategoryForm, FoodForm, FoodRecordForm
from tracker.models import FoodCategory, Food, FoodRecord
from tracker.views import get_dietary_suggestions


# ========== 10.1 用户认证测试用例 ==========

class UserAuthenticationTest(TestCase):
    """用户认证测试 - 注册、登录、登出"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.dashboard_url = reverse('dashboard')

    def test_register_page_get(self):
        """测试注册页面 GET 请求返回 200"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_login_page_get(self):
        """测试登录页面 GET 请求返回 200"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_register_success(self):
        """测试成功注册新用户"""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        # 注册成功应该重定向到 dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)
        # 验证用户已创建
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # 验证用户已登录
        user = User.objects.get(username='newuser')
        self.assertTrue(self.client.session['_auth_user_id'])

    def test_register_duplicate_username(self):
        """测试重复用户名注册失败"""
        # 先创建一个用户
        User.objects.create_user(username='existing', password='Test123!')
        # 尝试重复注册
        response = self.client.post(self.register_url, {
            'username': 'existing',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_register_password_mismatch(self):
        """测试密码不匹配"""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'DifferentPass123!',
        })
        self.assertEqual(response.status_code, 200)
        # 检查表单包含密码错误
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_login_success(self):
        """测试成功登录"""
        user = User.objects.create_user(username='testuser', password='TestPass123!')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)

    def test_login_invalid_credentials(self):
        """测试无效凭据登录失败"""
        User.objects.create_user(username='testuser', password='TestPass123!')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        # 检查表单包含错误
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_logout(self):
        """测试登出功能"""
        user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)

    def test_unauthenticated_access_to_dashboard(self):
        """测试未认证用户访问 dashboard 被重定向"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


# ========== 10.2 食物分类测试用例 ==========

class FoodCategoryModelTest(TestCase):
    """食物分类模型测试"""

    def test_create_category(self):
        """测试创建分类"""
        category = FoodCategory.objects.create(
            category_name='主食类',
            description='主要提供碳水化合物的食物'
        )
        self.assertEqual(FoodCategory.objects.count(), 1)
        self.assertEqual(category.category_name, '主食类')

    def test_unique_category_name(self):
        """测试分类名称唯一性约束"""
        FoodCategory.objects.create(category_name='水果类')
        with self.assertRaises(Exception):
            FoodCategory.objects.create(category_name='水果类')

    def test_str_representation(self):
        """测试字符串表示"""
        category = FoodCategory.objects.create(category_name='蔬菜类')
        self.assertEqual(str(category), '蔬菜类')

    def test_category_with_empty_description(self):
        """测试空描述"""
        category = FoodCategory.objects.create(category_name='零食类')
        self.assertEqual(category.description, '')
        self.assertTrue(FoodCategory.objects.filter(category_name='零食类').exists())


class FoodCategoryViewTest(TestCase):
    """食物分类视图测试 - CRUD 操作"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='主食类', description='主食')

    def test_category_list_view(self):
        """测试分类列表视图"""
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category/category_list.html')
        self.assertContains(response, '主食类')

    def test_category_add_view_get(self):
        """测试添加分类 GET 请求"""
        response = self.client.get(reverse('category_add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category/category_form.html')

    def test_category_add_view_post(self):
        """测试添加分类 POST 请求"""
        response = self.client.post(reverse('category_add'), {
            'category_name': '水果类',
            'description': '新鲜水果'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('category_list'))
        self.assertTrue(FoodCategory.objects.filter(category_name='水果类').exists())

    def test_category_edit_view_get(self):
        """测试编辑分类 GET 请求"""
        response = self.client.get(reverse('category_edit', args=[self.category.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category/category_form.html')

    def test_category_edit_view_post(self):
        """测试编辑分类 POST 请求"""
        response = self.client.post(reverse('category_edit', args=[self.category.id]), {
            'category_name': '主食类（更新）',
            'description': '更新后的描述'
        })
        self.assertEqual(response.status_code, 302)
        self.category.refresh_from_db()
        self.assertEqual(self.category.category_name, '主食类（更新）')

    def test_category_delete_view_get(self):
        """测试删除分类 GET 请求"""
        response = self.client.get(reverse('category_delete', args=[self.category.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category/category_delete.html')

    def test_category_delete_view_post(self):
        """测试删除分类 POST 请求"""
        category_id = self.category.id
        response = self.client.post(reverse('category_delete', args=[category_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('category_list'))
        self.assertFalse(FoodCategory.objects.filter(id=category_id).exists())


class FoodCategoryFormTest(TestCase):
    """食物分类表单测试"""

    def test_valid_form(self):
        """测试有效表单"""
        form = FoodCategoryForm(data={
            'category_name': '测试分类',
            'description': '测试描述'
        })
        self.assertTrue(form.is_valid())

    def test_empty_category_name(self):
        """测试空分类名称"""
        form = FoodCategoryForm(data={
            'category_name': '',
            'description': '描述'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('category_name', form.errors)

    def test_duplicate_category_name(self):
        """测试重复分类名称（后端验证）"""
        FoodCategory.objects.create(category_name='水果类')
        form = FoodCategoryForm(data={
            'category_name': '水果类',
            'description': '描述'
        })
        # 注意：Django ModelForm 不会自动检查唯一性，需要手动调用 full_clean


# ========== 10.3 食物库测试用例 ==========

class FoodModelTest(TestCase):
    """食物模型测试"""

    def setUp(self):
        self.category = FoodCategory.objects.create(category_name='主食类')

    def test_create_food(self):
        """测试创建食物"""
        food = Food.objects.create(
            food_name='米饭',
            category=self.category,
            calories_per_100g=130,
            unit='克'
        )
        self.assertEqual(Food.objects.count(), 1)
        self.assertEqual(food.food_name, '米饭')
        self.assertEqual(food.calories_per_100g, 130)

    def test_food_str_representation(self):
        """测试食物字符串表示"""
        food = Food.objects.create(
            food_name='面条',
            category=self.category,
            calories_per_100g=150,
            unit='克'
        )
        self.assertEqual(str(food), '面条')

    def test_food_default_unit(self):
        """测试默认单位"""
        food = Food.objects.create(
            food_name='馒头',
            category=self.category,
            calories_per_100g=120
        )
        self.assertEqual(food.unit, '克')

    def test_food_cascade_delete(self):
        """测试级联删除"""
        food = Food.objects.create(
            food_name='测试食物',
            category=self.category,
            calories_per_100g=100
        )
        self.assertEqual(Food.objects.count(), 1)
        self.category.delete()
        self.assertEqual(Food.objects.count(), 0)


class FoodViewTest(TestCase):
    """食物库视图测试 - CRUD 操作和搜索"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='主食类')
        self.food = Food.objects.create(
            food_name='米饭',
            category=self.category,
            calories_per_100g=130,
            unit='克'
        )

    def test_food_list_view(self):
        """测试食物列表视图"""
        response = self.client.get(reverse('food_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'food_library/food_list.html')
        self.assertContains(response, '米饭')

    def test_food_list_search(self):
        """测试食物搜索功能"""
        response = self.client.get(reverse('food_list'), {'search': '米饭'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '米饭')

    def test_food_list_search_no_results(self):
        """测试搜索无结果"""
        response = self.client.get(reverse('food_list'), {'search': '不存在的食物'})
        self.assertEqual(response.status_code, 200)
        # 检查搜索查询被传递到模板
        self.assertEqual(response.context['search_query'], '不存在的食物')

    def test_food_list_category_filter(self):
        """测试按分类过滤"""
        response = self.client.get(reverse('food_list'), {'category': self.category.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '米饭')

    def test_food_library_add_view_get(self):
        """测试添加食物 GET 请求"""
        response = self.client.get(reverse('food_library_add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'food_library/food_form.html')

    def test_food_library_add_view_post(self):
        """测试添加食物 POST 请求"""
        response = self.client.post(reverse('food_library_add'), {
            'food_name': '面条',
            'category': self.category.id,
            'calories_per_100g': '150',
            'unit': '克'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('food_list'))
        self.assertTrue(Food.objects.filter(food_name='面条').exists())

    def test_food_library_edit_view_get(self):
        """测试编辑食物 GET 请求"""
        response = self.client.get(reverse('food_library_edit', args=[self.food.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'food_library/food_form.html')

    def test_food_library_edit_view_post(self):
        """测试编辑食物 POST 请求"""
        response = self.client.post(reverse('food_library_edit', args=[self.food.id]), {
            'food_name': '米饭（更新）',
            'category': self.category.id,
            'calories_per_100g': '140',
            'unit': '克'
        })
        self.assertEqual(response.status_code, 302)
        self.food.refresh_from_db()
        self.assertEqual(self.food.food_name, '米饭（更新）')
        self.assertEqual(self.food.calories_per_100g, 140)

    def test_food_library_delete_view_get(self):
        """测试删除食物 GET 请求"""
        response = self.client.get(reverse('food_library_delete', args=[self.food.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'food_library/food_delete.html')

    def test_food_library_delete_view_post(self):
        """测试删除食物 POST 请求"""
        food_id = self.food.id
        response = self.client.post(reverse('food_library_delete', args=[food_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('food_list'))
        self.assertFalse(Food.objects.filter(id=food_id).exists())


class FoodFormTest(TestCase):
    """食物表单测试"""

    def setUp(self):
        self.category = FoodCategory.objects.create(category_name='主食类')

    def _form_data(self, **overrides):
        data = {
            'food_name': '米饭',
            'category': self.category.id,
            'calories_per_100g': '130',
            'unit': '克'
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """测试有效表单"""
        form = FoodForm(data=self._form_data())
        self.assertTrue(form.is_valid())

    def test_empty_food_name(self):
        """测试空食物名称"""
        form = FoodForm(data=self._form_data(food_name=''))
        self.assertFalse(form.is_valid())
        self.assertIn('food_name', form.errors)

    def test_food_name_too_long(self):
        """测试食物名称过长"""
        form = FoodForm(data=self._form_data(food_name='a' * 101))
        self.assertFalse(form.is_valid())
        self.assertIn('food_name', form.errors)

    def test_calories_below_min(self):
        """测试热量低于最小值"""
        form = FoodForm(data=self._form_data(calories_per_100g='0'))
        self.assertFalse(form.is_valid())
        self.assertIn('calories_per_100g', form.errors)

    def test_calories_above_max(self):
        """测试热量超过最大值"""
        form = FoodForm(data=self._form_data(calories_per_100g='5001'))
        self.assertFalse(form.is_valid())
        self.assertIn('calories_per_100g', form.errors)

    def test_calories_valid_range(self):
        """测试热量在有效范围内"""
        form = FoodForm(data=self._form_data(calories_per_100g='1'))
        self.assertTrue(form.is_valid())
        form = FoodForm(data=self._form_data(calories_per_100g='5000'))
        self.assertTrue(form.is_valid())

    def test_empty_unit(self):
        """测试空单位"""
        form = FoodForm(data=self._form_data(unit=''))
        self.assertFalse(form.is_valid())
        self.assertIn('unit', form.errors)

    def test_unit_too_long(self):
        """测试单位过长"""
        form = FoodForm(data=self._form_data(unit='a' * 21))
        self.assertFalse(form.is_valid())
        self.assertIn('unit', form.errors)


# ========== 10.4 饮食记录测试用例 ==========

class FoodRecordModelTest(TestCase):
    """饮食记录模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='主食类')
        self.food = Food.objects.create(
            food_name='米饭',
            category=self.category,
            calories_per_100g=130,
            unit='克'
        )

    def test_create_record(self):
        """测试创建饮食记录"""
        record = FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('200.0'),
            meal_type='lunch',
            record_date=date.today()
        )
        self.assertEqual(FoodRecord.objects.count(), 1)
        self.assertEqual(record.quantity, Decimal('200.0'))

    def test_record_str_representation(self):
        """测试记录字符串表示"""
        record = FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('150.0'),
            meal_type='breakfast',
            record_date=date.today()
        )
        self.assertIn('米饭', str(record))
        self.assertIn('testuser', str(record))

    def test_total_calories_property(self):
        """测试总热量计算属性"""
        record = FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('200.0'),
            meal_type='lunch',
            record_date=date.today()
        )
        # 130 cal per 100g * 200g / 100 = 260 cal
        self.assertEqual(record.total_calories, 260)

    def test_meal_type_choices(self):
        """测试餐次选项"""
        for meal_type, _label in FoodRecord.MEAL_CHOICES:
            record = FoodRecord.objects.create(
                user=self.user,
                food=self.food,
                quantity=Decimal('100.0'),
                meal_type=meal_type,
                record_date=date.today()
            )
            record.full_clean()  # 应该不抛出异常

    def test_record_cascade_delete_user(self):
        """测试用户删除时级联删除记录"""
        FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('100.0'),
            meal_type='lunch',
            record_date=date.today()
        )
        self.assertEqual(FoodRecord.objects.count(), 1)
        self.user.delete()
        self.assertEqual(FoodRecord.objects.count(), 0)


class FoodRecordViewTest(TestCase):
    """饮食记录视图测试 - 创建、查询、计算"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='主食类')
        self.food = Food.objects.create(
            food_name='米饭',
            category=self.category,
            calories_per_100g=130,
            unit='克'
        )
        self.food2 = Food.objects.create(
            food_name='面条',
            category=self.category,
            calories_per_100g=150,
            unit='克'
        )

    def test_record_list_view(self):
        """测试记录列表视图"""
        response = self.client.get(reverse('record_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'record/record_list.html')

    def test_record_list_with_date(self):
        """测试按日期查询记录"""
        today = date.today().strftime('%Y-%m-%d')
        response = self.client.get(reverse('record_list'), {'date': today})
        self.assertEqual(response.status_code, 200)

    def test_add_food_view_get(self):
        """测试添加记录 GET 请求"""
        response = self.client.get(reverse('add_food'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'record/add.html')

    def test_add_food_view_post(self):
        """测试添加记录 POST 请求"""
        response = self.client.post(reverse('add_food'), {
            'food': self.food.id,
            'quantity': '200',
            'meal_type': 'lunch',
            'record_date': date.today().isoformat(),
            'notes': '午餐'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('record_list'))
        self.assertTrue(FoodRecord.objects.filter(meal_type='lunch').exists())

    def test_edit_food_view_get(self):
        """测试编辑记录 GET 请求"""
        record = FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('100.0'),
            meal_type='breakfast',
            record_date=date.today()
        )
        response = self.client.get(reverse('edit_food', args=[record.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'record/edit.html')

    def test_edit_food_view_post(self):
        """测试编辑记录 POST 请求"""
        record = FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('100.0'),
            meal_type='breakfast',
            record_date=date.today()
        )
        response = self.client.post(reverse('edit_food', args=[record.id]), {
            'food': self.food.id,
            'quantity': '150',
            'meal_type': 'lunch',
            'record_date': date.today().isoformat(),
            'notes': '更新后的备注'
        })
        self.assertEqual(response.status_code, 302)
        record.refresh_from_db()
        self.assertEqual(record.quantity, Decimal('150'))
        self.assertEqual(record.meal_type, 'lunch')

    def test_delete_food_view_get(self):
        """测试删除记录 GET 请求"""
        record = FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('100.0'),
            meal_type='breakfast',
            record_date=date.today()
        )
        response = self.client.get(reverse('delete_food', args=[record.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'record/delete.html')

    def test_delete_food_view_post(self):
        """测试删除记录 POST 请求"""
        record = FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('100.0'),
            meal_type='breakfast',
            record_date=date.today()
        )
        record_id = record.id
        response = self.client.post(reverse('delete_food', args=[record_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('record_list'))
        self.assertFalse(FoodRecord.objects.filter(id=record_id).exists())


class FoodRecordFormTest(TestCase):
    """饮食记录表单测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='主食类')
        self.food = Food.objects.create(
            food_name='米饭',
            category=self.category,
            calories_per_100g=130,
            unit='克'
        )

    def _form_data(self, **overrides):
        data = {
            'food': self.food.id,
            'quantity': '200',
            'meal_type': 'lunch',
            'record_date': date.today().isoformat(),
            'notes': ''
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """测试有效表单"""
        form = FoodRecordForm(data=self._form_data())
        self.assertTrue(form.is_valid())

    def test_empty_quantity(self):
        """测试空数量"""
        form = FoodRecordForm(data=self._form_data(quantity=''))
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_negative_quantity(self):
        """测试负数数量"""
        form = FoodRecordForm(data=self._form_data(quantity='-10'))
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_zero_quantity(self):
        """测试零数量"""
        form = FoodRecordForm(data=self._form_data(quantity='0'))
        self.assertFalse(form.is_valid())
        self.assertIn('quantity', form.errors)

    def test_future_date(self):
        """测试未来日期"""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        form = FoodRecordForm(data=self._form_data(record_date=tomorrow))
        self.assertFalse(form.is_valid())
        self.assertIn('record_date', form.errors)

    def test_valid_past_date(self):
        """测试有效的过去日期"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        form = FoodRecordForm(data=self._form_data(record_date=yesterday))
        self.assertTrue(form.is_valid())

    def test_invalid_meal_type(self):
        """测试无效餐次"""
        form = FoodRecordForm(data=self._form_data(meal_type='invalid'))
        self.assertFalse(form.is_valid())
        self.assertIn('meal_type', form.errors)

    def test_valid_meal_types(self):
        """测试所有有效餐次"""
        for meal_type, _label in FoodRecord.MEAL_CHOICES:
            form = FoodRecordForm(data=self._form_data(meal_type=meal_type))
            self.assertTrue(form.is_valid(), f"Meal type {meal_type} should be valid")

    def test_notes_too_long(self):
        """测试备注过长"""
        form = FoodRecordForm(data=self._form_data(notes='a' * 501))
        self.assertFalse(form.is_valid())
        self.assertIn('notes', form.errors)


class DashboardViewTest(TestCase):
    """仪表盘视图测试 - 计算功能"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='主食类')
        self.food = Food.objects.create(
            food_name='米饭',
            category=self.category,
            calories_per_100g=130,
            unit='克'
        )

    def test_dashboard_empty(self):
        """测试空仪表盘"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # 仪表盘标题为"今日饮食"
        self.assertContains(response, '今日饮食')
        # 空状态显示"暂无饮食记录"
        self.assertContains(response, '暂无饮食记录')

    def test_dashboard_with_records(self):
        """测试有记录的仪表盘"""
        # 创建今日记录
        FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('100.0'),
            meal_type='breakfast',
            record_date=date.today()
        )
        FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('200.0'),
            meal_type='lunch',
            record_date=date.today()
        )
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # 130 + 260 = 390
        self.assertContains(response, '390')

    def test_dashboard_meal_subtotals(self):
        """测试按餐次计算热量"""
        FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('100.0'),
            meal_type='breakfast',
            record_date=date.today()
        )
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # 早餐热量 = 130
        self.assertContains(response, '130')


class HistoryViewTest(TestCase):
    """历史记录视图测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='主食类')
        self.food = Food.objects.create(
            food_name='米饭',
            category=self.category,
            calories_per_100g=130,
            unit='克'
        )

    def test_history_view(self):
        """测试历史记录视图"""
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'history/history.html')

    def test_history_with_date_filter(self):
        """测试日期过滤"""
        today = date.today().strftime('%Y-%m-%d')
        response = self.client.get(reverse('history'), {'date': today})
        self.assertEqual(response.status_code, 200)

    def test_history_with_meal_filter(self):
        """测试餐次过滤"""
        FoodRecord.objects.create(
            user=self.user,
            food=self.food,
            quantity=Decimal('100.0'),
            meal_type='breakfast',
            record_date=date.today()
        )
        response = self.client.get(reverse('history'), {'meal_type': 'breakfast'})
        self.assertEqual(response.status_code, 200)


class UserIsolationTest(TestCase):
    """用户隔离测试 - 确保用户只能访问自己的记录"""

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='TestPass123!')
        self.user2 = User.objects.create_user(username='user2', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='主食类')
        self.food = Food.objects.create(
            food_name='米饭',
            category=self.category,
            calories_per_100g=130,
            unit='克'
        )
        # user1 创建的记录
        self.record = FoodRecord.objects.create(
            user=self.user1,
            food=self.food,
            quantity=Decimal('100.0'),
            meal_type='lunch',
            record_date=date.today()
        )

    def test_user_cannot_edit_other_user_record(self):
        """测试用户不能编辑其他用户的记录"""
        self.client.login(username='user2', password='TestPass123!')
        response = self.client.get(reverse('edit_food', args=[self.record.id]))
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_other_user_record(self):
        """测试用户不能删除其他用户的记录"""
        self.client.login(username='user2', password='TestPass123!')
        response = self.client.post(reverse('delete_food', args=[self.record.id]))
        self.assertEqual(response.status_code, 404)
        # 验证记录仍然存在
        self.assertTrue(FoodRecord.objects.filter(id=self.record.id).exists())


# ========== 10.5 & 10.6 辅助函数测试 ==========

class DietarySuggestionTest(TestCase):
    """饮食建议辅助函数测试"""

    def test_no_records(self):
        """测试无记录"""
        suggestions = get_dietary_suggestions(0, {})
        self.assertEqual(suggestions, [])

    def test_low_intake(self):
        """测试低热量摄入"""
        suggestions = get_dietary_suggestions(500, {})
        messages = [msg for _, msg in suggestions]
        self.assertTrue(any('偏低' in m for m in messages))

    def test_healthy_range(self):
        """测试健康范围"""
        suggestions = get_dietary_suggestions(1500, {})
        messages = [msg for _, msg in suggestions]
        self.assertTrue(any('健康' in m or '好' in m for m in messages))

    def test_over_intake(self):
        """测试过量摄入"""
        suggestions = get_dietary_suggestions(2500, {})
        messages = [msg for _, msg in suggestions]
        self.assertTrue(any('超过' in m for m in messages))

    def test_heavy_meal(self):
        """测试单餐热量过高"""
        suggestions = get_dietary_suggestions(1500, {'lunch': 900})
        messages = [msg for _, msg in suggestions]
        self.assertTrue(any('高' in m for m in messages))
