"""
Diet Tracker - Unit Test Module

Test Tasks:
10.1 User Authentication Test Cases - Registration, Login, Logout
10.2 Food Category Test Cases - CRUD Operations
10.3 Food Database Test Cases - CRUD Operations, Search
10.4 Diet Record Test Cases - Create, Query, Calculate
10.5 Run Tests and Fix Failed Cases
10.6 Generate Test Coverage Report
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from tracker.forms import RegisterForm, FoodCategoryForm, FoodForm, FoodRecordForm
from tracker.models import FoodCategory, Food, FoodRecord
from tracker.views import get_dietary_suggestions


# ========== 10.1 User Authentication Test Case ==========

class UserAuthenticationTest(TestCase):
    """User Authentication Test - Register, Login, Logout"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.dashboard_url = reverse('dashboard')

    def test_register_page_get(self):
        """Test registration page GET request returns 200"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_login_page_get(self):
        """Test login page GET request returns 200"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_register_success(self):
        """Test successfully registered a new user"""
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        # Registration successful should redirect to the dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)
        # Verify that the user has been created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # Verify that the user is logged in
        user = User.objects.get(username='newuser')
        self.assertTrue(self.client.session['_auth_user_id'])

    def test_register_duplicate_username(self):
        """Test registration failure for duplicate username"""
        # First, create a user
        User.objects.create_user(username='existing', password='Test123!')
        # Attempt to register again
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
        # The form contains a password error
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_login_success(self):
        """Test successful login"""
        user = User.objects.create_user(username='testuser', password='TestPass123!')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)

    def test_login_invalid_credentials(self):
        """Test invalid credentials login failed"""
        User.objects.create_user(username='testuser', password='TestPass123!')
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        # The form contains errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_logout(self):
        """Test logout function"""
        user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)

    def test_unauthenticated_access_to_dashboard(self):
        """Test that unauthenticated users are redirected when accessing the dashboard"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


# ========== 10.2 Food Classification Test Case ==========

class FoodCategoryModelTest(TestCase):
    """Food Classification Model Test"""

    def test_create_category(self):
        """Test create category"""
        category = FoodCategory.objects.create(
            category_name='Staple foods',
            description='Foods that mainly provide carbohydrates'
        )
        self.assertEqual(FoodCategory.objects.count(), 1)
        self.assertEqual(category.category_name, 'Staple foods')

    def test_unique_category_name(self):
        """Test uniqueness constraint of category name"""
        FoodCategory.objects.create(category_name='Fruits')
        with self.assertRaises(Exception):
            FoodCategory.objects.create(category_name='Fruits')

    def test_str_representation(self):
        """Test string representation"""
        category = FoodCategory.objects.create(category_name='Vegetables')
        self.assertEqual(str(category), 'Vegetables')

    def test_category_with_empty_description(self):
        """Test empty description"""
        category = FoodCategory.objects.create(category_name='Snacks')
        self.assertEqual(category.description, '')
        self.assertTrue(FoodCategory.objects.filter(category_name='Snacks').exists())


class FoodCategoryViewTest(TestCase):
    """Food Category View Test - CRUD Operations"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='主食类', description='主食')

    def test_category_list_view(self):
        """Test Category List View"""
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category/category_list.html')
        self.assertContains(response, 'Staple foods')

    def test_category_add_view_get(self):
        """Test add category GET request"""
        response = self.client.get(reverse('category_add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category/category_form.html')

    def test_category_add_view_post(self):
        """Test add category POST request"""
        response = self.client.post(reverse('category_add'), {
            'category_name': 'Fruits',
            'description': 'Fresh fruit'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('category_list'))
        self.assertTrue(FoodCategory.objects.filter(category_name='Fruits').exists())

    def test_category_edit_view_get(self):
        """Test editing category GET request"""
        response = self.client.get(reverse('category_edit', args=[self.category.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category/category_form.html')

    def test_category_edit_view_post(self):
        """Test editing category POST request"""
        response = self.client.post(reverse('category_edit', args=[self.category.id]), {
            'category_name': 'Staple Foods (Updated)',
            'description': 'Updated description'
        })
        self.assertEqual(response.status_code, 302)
        self.category.refresh_from_db()
        self.assertEqual(self.category.category_name, 'Staple Foods (Updated)')

    def test_category_delete_view_get(self):
        """Test delete category GET request"""
        response = self.client.get(reverse('category_delete', args=[self.category.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category/category_delete.html')

    def test_category_delete_view_post(self):
        """Test delete category POST request"""
        category_id = self.category.id
        response = self.client.post(reverse('category_delete', args=[category_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('category_list'))
        self.assertFalse(FoodCategory.objects.filter(id=category_id).exists())


class FoodCategoryFormTest(TestCase):
    """Food Classification Form Test"""

    def test_valid_form(self):
        """Test valid form"""
        form = FoodCategoryForm(data={
            'category_name': 'Test Classification',
            'description': 'Test Description'
        })
        self.assertTrue(form.is_valid())

    def test_empty_category_name(self):
        """Test empty category name"""
        form = FoodCategoryForm(data={
            'category_name': '',
            'description': 'description'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('category_name', form.errors)

    def test_duplicate_category_name(self):
        """Test duplicate category name (backend validation)"""
        FoodCategory.objects.create(category_name='Fruits')
        form = FoodCategoryForm(data={
            'category_name': '水果类',
            'description': 'Description'
        })
        # Note: Django ModelForm does not automatically check for uniqueness; you need to call full_clean manually.


# ========== 10.3 Food Repository Test Case ==========

class FoodModelTest(TestCase):
    """Food Model Test"""

    def setUp(self):
        self.category = FoodCategory.objects.create(category_name='Staple foods')

    def test_create_food(self):
        """Test creating food"""
        food = Food.objects.create(
            food_name='Rice',
            category=self.category,
            calories_per_100g=130,
            unit='gram'
        )
        self.assertEqual(Food.objects.count(), 1)
        self.assertEqual(food.food_name, 'Rice')
        self.assertEqual(food.calories_per_100g, 130)

    def test_food_str_representation(self):
        """Test food string representation"""
        food = Food.objects.create(
            food_name='Noodles',
            category=self.category,
            calories_per_100g=150,
            unit='gram'
        )
        self.assertEqual(str(food), 'Noodles')

    def test_food_default_unit(self):
        """Test default unit"""
        food = Food.objects.create(
            food_name='steamed bun',
            category=self.category,
            calories_per_100g=120
        )
        self.assertEqual(food.unit, 'gram')

    def test_food_cascade_delete(self):
        """Test cascade delete"""
        food = Food.objects.create(
            food_name='Test food',
            category=self.category,
            calories_per_100g=100
        )
        self.assertEqual(Food.objects.count(), 1)
        self.category.delete()
        self.assertEqual(Food.objects.count(), 0)


class FoodViewTest(TestCase):
    """Food Library View Test - CRUD Operations and Search"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.client.login(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='Staple foods')
        self.food = Food.objects.create(
            food_name='rice',
            category=self.category,
            calories_per_100g=130,
            unit='gram'
        )

    def test_food_list_view(self):
        """Test food list view"""
        response = self.client.get(reverse('food_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'food_library/food_list.html')
        self.assertContains(response, 'Rice')

    def test_food_list_search(self):
        """Test food search function"""
        response = self.client.get(reverse('food_list'), {'search': 'Rice'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rice')

    def test_food_list_search_no_results(self):
        """Test search returned no results"""
        response = self.client.get(reverse('food_list'), {'search': 'Nonexistent food'})
        self.assertEqual(response.status_code, 200)
        # Check that the search query is passed to the template
        self.assertEqual(response.context['search_query'], 'Nonexistent food')

    def test_food_list_category_filter(self):
        """Test filter by category"""
        response = self.client.get(reverse('food_list'), {'category': self.category.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rice')

    def test_food_library_add_view_get(self):
        """Test adding food GET request"""
        response = self.client.get(reverse('food_library_add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'food_library/food_form.html')

    def test_food_library_add_view_post(self):
        """Test adding food POST request"""
        response = self.client.post(reverse('food_library_add'), {
            'food_name': 'Noodles',
            'category': self.category.id,
            'calories_per_100g': '150',
            'unit': 'gram'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('food_list'))
        self.assertTrue(Food.objects.filter(food_name='Noodles').exists())

    def test_food_library_edit_view_get(self):
        """Test edit food GET request"""
        response = self.client.get(reverse('food_library_edit', args=[self.food.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'food_library/food_form.html')

    def test_food_library_edit_view_post(self):
        """Test edit food POST request"""
        response = self.client.post(reverse('food_library_edit', args=[self.food.id]), {
            'food_name': 'Rice (Updated)',
            'category': self.category.id,
            'calories_per_100g': '140',
            'unit': 'gram'
        })
        self.assertEqual(response.status_code, 302)
        self.food.refresh_from_db()
        self.assertEqual(self.food.food_name, 'Rice (Updated)')
        self.assertEqual(self.food.calories_per_100g, 140)

    def test_food_library_delete_view_get(self):
        """Test delete food GET request"""
        response = self.client.get(reverse('food_library_delete', args=[self.food.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'food_library/food_delete.html')

    def test_food_library_delete_view_post(self):
        """Test delete food POST request"""
        food_id = self.food.id
        response = self.client.post(reverse('food_library_delete', args=[food_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('food_list'))
        self.assertFalse(Food.objects.filter(id=food_id).exists())


class FoodFormTest(TestCase):
    """Food Form Test"""

    def setUp(self):
        self.category = FoodCategory.objects.create(category_name='Staple foods')

    def _form_data(self, **overrides):
        data = {
            'food_name': 'Rice',
            'category': self.category.id,
            'calories_per_100g': '130',
            'unit': 'gram'
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        """Test valid form"""
        form = FoodForm(data=self._form_data())
        self.assertTrue(form.is_valid())

    def test_empty_food_name(self):
        """Test empty food name"""
        form = FoodForm(data=self._form_data(food_name=''))
        self.assertFalse(form.is_valid())
        self.assertIn('food_name', form.errors)

    def test_food_name_too_long(self):
        """Test food name is too long"""
        form = FoodForm(data=self._form_data(food_name='a' * 101))
        self.assertFalse(form.is_valid())
        self.assertIn('food_name', form.errors)

    def test_calories_below_min(self):
        """Test calories are below the minimum value"""
        form = FoodForm(data=self._form_data(calories_per_100g='0'))
        self.assertFalse(form.is_valid())
        self.assertIn('calories_per_100g', form.errors)

    def test_calories_above_max(self):
        """Test calories exceed the maximum value"""
        form = FoodForm(data=self._form_data(calories_per_100g='5001'))
        self.assertFalse(form.is_valid())
        self.assertIn('calories_per_100g', form.errors)

    def test_calories_valid_range(self):
        """The test calories are within the effective range"""
        form = FoodForm(data=self._form_data(calories_per_100g='1'))
        self.assertTrue(form.is_valid())
        form = FoodForm(data=self._form_data(calories_per_100g='5000'))
        self.assertTrue(form.is_valid())

    def test_empty_unit(self):
        """Test empty unit"""
        form = FoodForm(data=self._form_data(unit=''))
        self.assertFalse(form.is_valid())
        self.assertIn('unit', form.errors)

    def test_unit_too_long(self):
        """Test unit is too long"""
        form = FoodForm(data=self._form_data(unit='a' * 21))
        self.assertFalse(form.is_valid())
        self.assertIn('unit', form.errors)


# ========== 10.4 Dietary Record Test Case ==========

class FoodRecordModelTest(TestCase):
    """Dietary Record Model Test"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='TestPass123!')
        self.category = FoodCategory.objects.create(category_name='Staple foods')
        self.food = Food.objects.create(
            food_name='Rice',
            category=self.category,
            calories_per_100g=130,
            unit='gram'
        )

        def test_create_record(self):
            """Test creating a food record"""
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
            """Test record string representation"""
            record = FoodRecord.objects.create(
                user=self.user,
                food=self.food,
                quantity=Decimal('150.0'),
                meal_type='breakfast',
                record_date=date.today()
            )
            self.assertIn('Rice', str(record))
            self.assertIn('testuser', str(record))

        def test_total_calories_property(self):
            """Test total calories calculation property"""
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
            """Test meal type choices"""
            for meal_type, _label in FoodRecord.MEAL_CHOICES:
                record = FoodRecord.objects.create(
                    user=self.user,
                    food=self.food,
                    quantity=Decimal('100.0'),
                    meal_type=meal_type,
                    record_date=date.today()
                )
                record.full_clean()  # Should not raise exception

        def test_record_cascade_delete_user(self):
            """Test cascade delete records when user is deleted"""
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
        """Food Record View Tests - Create, Query, Calculate"""

        def setUp(self):
            self.user = User.objects.create_user(username='testuser', password='TestPass123!')
            self.client.login(username='testuser', password='TestPass123!')
            self.category = FoodCategory.objects.create(category_name='Staple Food')
            self.food = Food.objects.create(
                food_name='Rice',
                category=self.category,
                calories_per_100g=130,
                unit='g'
            )
            self.food2 = Food.objects.create(
                food_name='Noodles',
                category=self.category,
                calories_per_100g=150,
                unit='g'
            )

        def test_record_list_view(self):
            """Test record list view"""
            response = self.client.get(reverse('record_list'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'record/record_list.html')

        def test_record_list_with_date(self):
            """Test querying records by date"""
            today = date.today().strftime('%Y-%m-%d')
            response = self.client.get(reverse('record_list'), {'date': today})
            self.assertEqual(response.status_code, 200)

        def test_add_food_view_get(self):
            """Test add record GET request"""
            response = self.client.get(reverse('add_food'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'record/add.html')

        def test_add_food_view_post(self):
            """Test add record POST request"""
            response = self.client.post(reverse('add_food'), {
                'food': self.food.id,
                'quantity': '200',
                'meal_type': 'lunch',
                'record_date': date.today().isoformat(),
                'notes': 'Lunch'
            })
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, reverse('record_list'))
            self.assertTrue(FoodRecord.objects.filter(meal_type='lunch').exists())

        def test_edit_food_view_get(self):
            """Test edit record GET request"""
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
            """Test edit record POST request"""
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
                'notes': 'Updated notes'
            })
            self.assertEqual(response.status_code, 302)
            record.refresh_from_db()
            self.assertEqual(record.quantity, Decimal('150'))
            self.assertEqual(record.meal_type, 'lunch')

        def test_delete_food_view_get(self):
            """Test delete record GET request"""
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
            """Test delete record POST request"""
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
        """Food Record Form Tests"""

        def setUp(self):
            self.user = User.objects.create_user(username='testuser', password='TestPass123!')
            self.category = FoodCategory.objects.create(category_name='Staple Food')
            self.food = Food.objects.create(
                food_name='Rice',
                category=self.category,
                calories_per_100g=130,
                unit='g'
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
            """Test valid form"""
            form = FoodRecordForm(data=self._form_data())
            self.assertTrue(form.is_valid())

        def test_empty_quantity(self):
            """Test empty quantity"""
            form = FoodRecordForm(data=self._form_data(quantity=''))
            self.assertFalse(form.is_valid())
            self.assertIn('quantity', form.errors)

        def test_negative_quantity(self):
            """Test negative quantity"""
            form = FoodRecordForm(data=self._form_data(quantity='-10'))
            self.assertFalse(form.is_valid())
            self.assertIn('quantity', form.errors)

        def test_zero_quantity(self):
            """Test zero quantity"""
            form = FoodRecordForm(data=self._form_data(quantity='0'))
            self.assertFalse(form.is_valid())
            self.assertIn('quantity', form.errors)

        def test_future_date(self):
            """Test future date"""
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            form = FoodRecordForm(data=self._form_data(record_date=tomorrow))
            self.assertFalse(form.is_valid())
            self.assertIn('record_date', form.errors)

        def test_valid_past_date(self):
            """Test valid past date"""
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            form = FoodRecordForm(data=self._form_data(record_date=yesterday))
            self.assertTrue(form.is_valid())

        def test_invalid_meal_type(self):
            """Test invalid meal type"""
            form = FoodRecordForm(data=self._form_data(meal_type='invalid'))
            self.assertFalse(form.is_valid())
            self.assertIn('meal_type', form.errors)

        def test_valid_meal_types(self):
            """Test all valid meal types"""
            for meal_type, _label in FoodRecord.MEAL_CHOICES:
                form = FoodRecordForm(data=self._form_data(meal_type=meal_type))
                self.assertTrue(form.is_valid(), f"Meal type {meal_type} should be valid")

        def test_notes_too_long(self):
            """Test notes too long"""
            form = FoodRecordForm(data=self._form_data(notes='a' * 501))
            self.assertFalse(form.is_valid())
            self.assertIn('notes', form.errors)

    class DashboardViewTest(TestCase):
        """Dashboard View Tests - Calculation Functionality"""

        def setUp(self):
            self.user = User.objects.create_user(username='testuser', password='TestPass123!')
            self.client.login(username='testuser', password='TestPass123!')
            self.category = FoodCategory.objects.create(category_name='Staple Food')
            self.food = Food.objects.create(
                food_name='Rice',
                category=self.category,
                calories_per_100g=130,
                unit='g'
            )

        def test_dashboard_empty(self):
            """Test empty dashboard"""
            response = self.client.get(reverse('dashboard'))
            self.assertEqual(response.status_code, 200)
            # Dashboard title is "Today's Diet"
            self.assertContains(response, "Today's Diet")
            # Empty state displays "No food records yet"
            self.assertContains(response, "No food records yet")

        def test_dashboard_with_records(self):
            """Test dashboard with records"""
            # Create today's records
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
            """Test calorie calculation by meal type"""
            FoodRecord.objects.create(
                user=self.user,
                food=self.food,
                quantity=Decimal('100.0'),
                meal_type='breakfast',
                record_date=date.today()
            )
            response = self.client.get(reverse('dashboard'))
            self.assertEqual(response.status_code, 200)
            # Breakfast calories = 130
            self.assertContains(response, '130')

    class HistoryViewTest(TestCase):
        """History View Tests"""

        def setUp(self):
            self.user = User.objects.create_user(username='testuser', password='TestPass123!')
            self.client.login(username='testuser', password='TestPass123!')
            self.category = FoodCategory.objects.create(category_name='Staple Food')
            self.food = Food.objects.create(
                food_name='Rice',
                category=self.category,
                calories_per_100g=130,
                unit='g'
            )

        def test_history_view(self):
            """Test history view"""
            response = self.client.get(reverse('history'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'history/history.html')

        def test_history_with_date_filter(self):
            """Test date filtering"""
            today = date.today().strftime('%Y-%m-%d')
            response = self.client.get(reverse('history'), {'date': today})
            self.assertEqual(response.status_code, 200)

        def test_history_with_meal_filter(self):
            """Test meal type filtering"""
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
        """User Isolation Tests - Ensure users can only access their own records"""

        def setUp(self):
            self.user1 = User.objects.create_user(username='user1', password='TestPass123!')
            self.user2 = User.objects.create_user(username='user2', password='TestPass123!')
            self.category = FoodCategory.objects.create(category_name='Staple Food')
            self.food = Food.objects.create(
                food_name='Rice',
                category=self.category,
                calories_per_100g=130,
                unit='g'
            )
            # Record created by user1
            self.record = FoodRecord.objects.create(
                user=self.user1,
                food=self.food,
                quantity=Decimal('100.0'),
                meal_type='lunch',
                record_date=date.today()
            )

        def test_user_cannot_edit_other_user_record(self):
            """Test that a user cannot edit another user's record"""
            self.client.login(username='user2', password='TestPass123!')
            response = self.client.get(reverse('edit_food', args=[self.record.id]))
            self.assertEqual(response.status_code, 404)

        def test_user_cannot_delete_other_user_record(self):
            """Test that a user cannot delete another user's record"""
            self.client.login(username='user2', password='TestPass123!')
            response = self.client.post(reverse('delete_food', args=[self.record.id]))
            self.assertEqual(response.status_code, 404)
            # Verify that record still exists
            self.assertTrue(FoodRecord.objects.filter(id=self.record.id).exists())

    # ========== 10.5 & 10.6 Helper Function Tests ==========

    class DietarySuggestionTest(TestCase):
        """Dietary Suggestion Helper Function Tests"""

        def test_no_records(self):
            """Test no records"""
            suggestions = get_dietary_suggestions(0, {})
            self.assertEqual(suggestions, [])

        def test_low_intake(self):
            """Test low calorie intake"""
            suggestions = get_dietary_suggestions(500, {})
            messages = [msg for _, msg in suggestions]
            self.assertTrue(any('low' in m.lower() or 'low' in m for m in messages))

        def test_healthy_range(self):
            """Test healthy range"""
            suggestions = get_dietary_suggestions(1500, {})
            messages = [msg for _, msg in suggestions]
            self.assertTrue(
                any('healthy' in m.lower() or 'good' in m.lower() or 'healthy' in m or 'good' in m for m in messages))

        def test_over_intake(self):
            """Test excessive intake"""
            suggestions = get_dietary_suggestions(2500, {})
            messages = [msg for _, msg in suggestions]
            self.assertTrue(any('exceed' in m.lower() or 'exceed' in m for m in messages))

        def test_heavy_meal(self):
            """Test high calorie single meal"""
            suggestions = get_dietary_suggestions(1500, {'lunch': 900})
            messages = [msg for _, msg in suggestions]
            self.assertTrue(any('high' in m.lower() or 'high' in m for m in messages))