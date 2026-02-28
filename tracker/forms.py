from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import FoodCategory, Food, FoodRecord

class FoodSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)

        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"]["data-calories"] = instance.calories_per_100g  # ✅ 真实字段名
            option["attrs"]["data-food-name"] = instance.food_name        # ✅ 真实字段名（可选）

        return option

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='电子邮箱',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '电子邮件地址',
        }),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '用户名',
        })
        self.fields['username'].label = '用户名'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '密码',
        })
        self.fields['password1'].label = '密码'
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '确认密码',
        })
        self.fields['password2'].label = '确认密码'


class FoodCategoryForm(forms.ModelForm):
    """食物分类表单"""
    class Meta:
        model = FoodCategory
        fields = ['category_name', 'description']
        labels = {
            'category_name': '分类名称',
            'description': '描述',
        }
        widgets = {
            'category_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 主食类',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '分类描述',
                'rows': 3,
            }),
        }


class FoodForm(forms.ModelForm):
    """食物表单"""
    class Meta:
        model = Food
        fields = ['food_name', 'category', 'calories_per_100g', 'unit']
        labels = {
            'food_name': '食物名称',
            'category': '分类',
            'calories_per_100g': '卡路里 (每100克)',
            'unit': '单位',
        }
        widgets = {
            'food_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 米饭',
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'calories_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '每100克卡路里',
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '单位，如克',
            }),
        }

    def clean_food_name(self):
        food_name = self.cleaned_data.get('food_name')
        if food_name:
            food_name = food_name.strip()
            if len(food_name) > 100:
                raise ValidationError('食物名称不能超过100个字符。')
            if not food_name:
                raise ValidationError('食物名称是必填项。')
        return food_name

    def clean_calories_per_100g(self):
        calories = self.cleaned_data.get('calories_per_100g')
        if calories is not None and (calories < 1 or calories > 5000):
            raise ValidationError('每100克卡路里必须在1到5000之间。')
        if calories is None or calories == '':
            raise ValidationError('卡路里是必填项。')
        return calories

    def clean_unit(self):
        unit = self.cleaned_data.get('unit')
        if not unit or not unit.strip():
            raise ValidationError('单位是必填项。')
        if len(unit) > 20:
            raise ValidationError('单位不能超过20个字符。')
        return unit.strip()


class FoodRecordForm(forms.ModelForm):
    """饮食记录表单"""
    class Meta:
        model = FoodRecord
        fields = ['food', 'quantity', 'meal_type', 'record_date', 'notes']
        labels = {
            'food': '选择食物',
            'quantity': '数量 (克)',
            'meal_type': '餐次',
            'record_date': '记录日期',
            'notes': '备注',
        }
        widgets = {
            'food': FoodSelect(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '输入数量',
                'step': '0.1',
                'min': '0.1',
                'id': 'id_quantity',
            }),
            'meal_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_meal_type',
            }),
            'record_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_record_date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '备注（可选）',
                'rows': 2,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('record_date') and not self.instance.pk:
            self.initial['record_date'] = date.today().isoformat()

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise ValidationError('数量必须大于0。')
        if quantity is None or quantity == '':
            raise ValidationError('数量是必填项。')
        return quantity

    def clean_record_date(self):
        record_date = self.cleaned_data.get('record_date')
        if record_date and record_date > date.today():
            raise ValidationError('日期不能是未来日期。')
        if record_date is None:
            raise ValidationError('日期是必填项。')
        return record_date

    def clean_notes(self):
        notes = self.cleaned_data.get('notes')
        if notes and len(notes) > 500:
            raise ValidationError('备注不能超过500个字符。')
        return notes

    def clean_meal_type(self):
        meal_type = self.cleaned_data.get('meal_type')
        valid_choices = [choice[0] for choice in FoodRecord.MEAL_CHOICES]
        if meal_type not in valid_choices:
            raise ValidationError('请选择有效的餐次。')
        return meal_type


# 保留旧的 FoodEntryForm 以兼容旧代码（如果需要）
class FoodEntryForm(FoodRecordForm):
    """旧的饮食记录表单（兼容版本）"""
    pass
