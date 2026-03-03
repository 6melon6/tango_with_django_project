from django.db import models
from django.contrib.auth.models import User


class FoodCategory(models.Model):
    """Food Category Model"""
    category_name = models.CharField(max_length=100, unique=True, verbose_name='Category Name')
    description = models.TextField(blank=True, verbose_name='Description')

    class Meta:
        db_table = 'food_category'
        verbose_name = 'Food Category'
        verbose_name_plural = 'Food Categories'

    def __str__(self):
        return self.category_name


class Food(models.Model):
    """Food Model"""
    food_name = models.CharField(max_length=100, verbose_name='Food Name')
    category = models.ForeignKey(
        FoodCategory,
        on_delete=models.CASCADE,
        related_name='foods',
        verbose_name='Category'
    )
    calories_per_100g = models.PositiveIntegerField(verbose_name='Calories per 100g')
    unit = models.CharField(max_length=20, default='g', verbose_name='Unit')

    class Meta:
        db_table = 'food'
        verbose_name = 'Food'
        verbose_name_plural = 'Foods'
        indexes = [
            models.Index(fields=['food_name']),
            models.Index(fields=['category', 'food_name']),
        ]

    def __str__(self):
        return self.food_name


class FoodRecord(models.Model):
    """Food Record Model"""

    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='food_records',
        verbose_name='User'
    )
    food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='Food'
    )
    quantity = models.DecimalField(max_digits=6, decimal_places=1, verbose_name='Quantity (g)')
    meal_type = models.CharField(max_length=10, choices=MEAL_CHOICES, verbose_name='Meal Type')
    record_date = models.DateField(verbose_name='Record Date')
    notes = models.TextField(blank=True, verbose_name='Notes')

    class Meta:
        db_table = 'food_record'
        verbose_name = 'Food Record'
        verbose_name_plural = 'Food Records'
        indexes = [
            models.Index(fields=['user', 'record_date']),
            models.Index(fields=['user', 'record_date', 'meal_type']),
            models.Index(fields=['record_date']),
        ]
        ordering = ['-record_date', '-id']

    def __str__(self):
        return f"{self.user.username} - {self.food.food_name} ({self.record_date})"

    @property
    def total_calories(self):
        """Calculate total calories"""
        return (self.food.calories_per_100g * self.quantity) / 100