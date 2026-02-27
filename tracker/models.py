from django.db import models
from django.contrib.auth.models import User


class FoodCategory(models.Model):
    """食物分类模型"""
    category_name = models.CharField(max_length=100, unique=True, verbose_name='分类名称')
    description = models.TextField(blank=True, verbose_name='描述')

    class Meta:
        db_table = 'food_category'
        verbose_name = '食物分类'
        verbose_name_plural = '食物分类'

    def __str__(self):
        return self.category_name


class Food(models.Model):
    """食物模型"""
    food_name = models.CharField(max_length=100, verbose_name='食物名称')
    category = models.ForeignKey(
        FoodCategory,
        on_delete=models.CASCADE,
        related_name='foods',
        verbose_name='分类'
    )
    calories_per_100g = models.PositiveIntegerField(verbose_name='每100克卡路里')
    unit = models.CharField(max_length=20, default='克', verbose_name='单位')

    class Meta:
        db_table = 'food'
        verbose_name = '食物'
        verbose_name_plural = '食物'
        indexes = [
            models.Index(fields=['food_name']),
            models.Index(fields=['category', 'food_name']),
        ]

    def __str__(self):
        return self.food_name


class FoodRecord(models.Model):
    """饮食记录模型"""
    MEAL_CHOICES = [
        ('breakfast', '早餐'),
        ('lunch', '午餐'),
        ('dinner', '晚餐'),
        ('snack', '零食'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='food_records',
        verbose_name='用户'
    )
    food = models.ForeignKey(
        Food,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='食物'
    )
    quantity = models.DecimalField(max_digits=6, decimal_places=1, verbose_name='数量')
    meal_type = models.CharField(max_length=10, choices=MEAL_CHOICES, verbose_name='餐次')
    record_date = models.DateField(verbose_name='记录日期')
    notes = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'food_record'
        verbose_name = '饮食记录'
        verbose_name_plural = '饮食记录'
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
        """计算总卡路里"""
        return (self.food.calories_per_100g * self.quantity) / 100
