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
            option["attrs"]["data-calories"] = instance.calories_per_100g
            option["attrs"]["data-food-name"] = instance.food_name

        return option

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
        }),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username',
        })
        self.fields['username'].label = 'Username'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })
        self.fields['password1'].label = 'Password'
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })
        self.fields['password2'].label = 'Confirm password'


class FoodCategoryForm(forms.ModelForm):
    """Food Category Form"""
    class Meta:
        model = FoodCategory
        fields = ['category_name', 'description']
        labels = {
            'category_name': 'Category Name',
            'description': 'Description',
        }
        widgets = {
            'category_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Main Dishes',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Category description',
                'rows': 3,
            }),
        }


class FoodForm(forms.ModelForm):
    """Food Form"""
    class Meta:
        model = Food
        fields = ['food_name', 'category', 'calories_per_100g', 'unit']
        labels = {
            'food_name': 'Food Name',
            'category': 'Category',
            'calories_per_100g': 'Calories (per 100g)',
            'unit': 'Unit',
        }
        widgets = {
            'food_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Rice',
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
            'calories_per_100g': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Calories per 100g',
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unit (e.g. g)',
            }),
        }

    def clean_food_name(self):
        food_name = self.cleaned_data.get('food_name')
        if food_name:
            food_name = food_name.strip()
            if len(food_name) > 100:
                raise ValidationError('Food name cannot exceed 100 characters.')
            if not food_name:
                raise ValidationError('Food name is required.')
        return food_name

    def clean_calories_per_100g(self):
        calories = self.cleaned_data.get('calories_per_100g')
        if calories is not None and (calories < 1 or calories > 5000):
            raise ValidationError('Calories per 100g must be between 1 and 5000.')
        if calories is None or calories == '':
            raise ValidationError('Calories are required.')
        return calories

    def clean_unit(self):
        unit = self.cleaned_data.get('unit')
        if not unit or not unit.strip():
            raise ValidationError('Unit is required.')
        if len(unit) > 20:
            raise ValidationError('Unit cannot exceed 20 characters.')
        return unit.strip()


class FoodRecordForm(forms.ModelForm):
    """Food Record Form"""
    class Meta:
        model = FoodRecord
        fields = ['food', 'quantity', 'meal_type', 'record_date', 'notes']
        labels = {
            'food': 'Select Food',
            'quantity': 'Quantity (g)',
            'meal_type': 'Meal Type',
            'record_date': 'Record Date',
            'notes': 'Notes',
        }
        widgets = {
            'food': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_food',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter quantity',
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
                'placeholder': 'Notes (optional)',
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
            raise ValidationError('Quantity must be greater than 0.')
        if quantity is None or quantity == '':
            raise ValidationError('Quantity is required.')
        return quantity

    def clean_record_date(self):
        record_date = self.cleaned_data.get('record_date')
        if record_date and record_date > date.today():
            raise ValidationError('Record date cannot be in the future.')
        if record_date is None:
            raise ValidationError('Record date is required.')
        return record_date

    def clean_notes(self):
        notes = self.cleaned_data.get('notes')
        if notes and len(notes) > 500:
            raise ValidationError('Notes cannot exceed 500 characters.')
        return notes

    def clean_meal_type(self):
        meal_type = self.cleaned_data.get('meal_type')
        valid_choices = [choice[0] for choice in FoodRecord.MEAL_CHOICES]
        if meal_type not in valid_choices:
            raise ValidationError('Please select a valid meal type.')
        return meal_type


# Keep old FoodEntryForm for backward compatibility (if needed)
class FoodEntryForm(FoodRecordForm):
    """Legacy Food Record Form (compatible version)"""
    pass