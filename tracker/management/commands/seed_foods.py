"""
Management command to pre-populate common foods into the database.
"""
from django.core.management.base import BaseCommand
from tracker.models import FoodCategory, Food


class Command(BaseCommand):
    help = 'Pre-populate common foods into the database'

    def handle(self, *args, **options):
        # Define food categories and food data
        categories_data = {
            'Staple Food': [
                {'name': 'Rice', 'calories': 130, 'unit': 'g'},
                {'name': 'Noodles', 'calories': 110, 'unit': 'g'},
                {'name': 'Steamed Bun', 'calories': 223, 'unit': 'g'},
                {'name': 'Bread', 'calories': 265, 'unit': 'g'},
                {'name': 'Dumplings', 'calories': 210, 'unit': 'g'},
                {'name': 'Stuffed Bun', 'calories': 227, 'unit': 'g'},
                {'name': 'Porridge', 'calories': 46, 'unit': 'g'},
                {'name': 'French Fries', 'calories': 312, 'unit': 'g'},
                {'name': 'Pizza', 'calories': 266, 'unit': 'g'},
            ],
            'Meat': [
                {'name': 'Chicken Leg', 'calories': 200, 'unit': 'g'},
                {'name': 'Chicken Breast', 'calories': 165, 'unit': 'g'},
                {'name': 'Pork', 'calories': 242, 'unit': 'g'},
                {'name': 'Beef', 'calories': 250, 'unit': 'g'},
                {'name': 'Mutton', 'calories': 294, 'unit': 'g'},
                {'name': 'Duck', 'calories': 337, 'unit': 'g'},
                {'name': 'Fish', 'calories': 136, 'unit': 'g'},
                {'name': 'Shrimp', 'calories': 85, 'unit': 'g'},
                {'name': 'Burger Patty', 'calories': 295, 'unit': 'g'},
            ],
            'Vegetables': [
                {'name': 'Broccoli', 'calories': 34, 'unit': 'g'},
                {'name': 'Carrot', 'calories': 41, 'unit': 'g'},
                {'name': 'Tomato', 'calories': 18, 'unit': 'g'},
                {'name': 'Cucumber', 'calories': 15, 'unit': 'g'},
                {'name': 'Spinach', 'calories': 23, 'unit': 'g'},
                {'name': 'Lettuce', 'calories': 15, 'unit': 'g'},
                {'name': 'Bell Pepper', 'calories': 31, 'unit': 'g'},
                {'name': 'Potato', 'calories': 77, 'unit': 'g'},
                {'name': 'Eggplant', 'calories': 25, 'unit': 'g'},
            ],
            'Fruits': [
                {'name': 'Apple', 'calories': 52, 'unit': 'g'},
                {'name': 'Banana', 'calories': 89, 'unit': 'g'},
                {'name': 'Orange', 'calories': 47, 'unit': 'g'},
                {'name': 'Grape', 'calories': 67, 'unit': 'g'},
                {'name': 'Watermelon', 'calories': 30, 'unit': 'g'},
                {'name': 'Strawberry', 'calories': 32, 'unit': 'g'},
                {'name': 'Mango', 'calories': 60, 'unit': 'g'},
                {'name': 'Pear', 'calories': 57, 'unit': 'g'},
                {'name': 'Peach', 'calories': 39, 'unit': 'g'},
            ],
            'Dairy': [
                {'name': 'Milk', 'calories': 61, 'unit': 'ml'},
                {'name': 'Yogurt', 'calories': 63, 'unit': 'g'},
                {'name': 'Cheese', 'calories': 402, 'unit': 'g'},
                {'name': 'Butter', 'calories': 717, 'unit': 'g'},
                {'name': 'Soy Milk', 'calories': 33, 'unit': 'ml'},
            ],
            'Snacks': [
                {'name': 'Potato Chips', 'calories': 536, 'unit': 'g'},
                {'name': 'Biscuits', 'calories': 488, 'unit': 'g'},
                {'name': 'Chocolate', 'calories': 546, 'unit': 'g'},
                {'name': 'Nuts', 'calories': 654, 'unit': 'g'},
                {'name': 'Candy', 'calories': 400, 'unit': 'g'},
                {'name': 'Popcorn', 'calories': 387, 'unit': 'g'},
            ],
            'Beverages': [
                {'name': 'Cola', 'calories': 38, 'unit': 'ml'},
                {'name': 'Orange Juice', 'calories': 45, 'unit': 'ml'},
                {'name': 'Coffee', 'calories': 2, 'unit': 'ml'},
                {'name': 'Tea', 'calories': 1, 'unit': 'ml'},
            ],
            'Fast Food': [
                {'name': 'Burger', 'calories': 295, 'unit': 'g'},
                {'name': 'Fried Chicken', 'calories': 307, 'unit': 'g'},
                {'name': 'Hot Dog', 'calories': 290, 'unit': 'g'},
                {'name': 'Sandwich', 'calories': 250, 'unit': 'g'},
                {'name': 'Burrito', 'calories': 226, 'unit': 'g'},
            ],
        }

        created_categories = 0
        created_foods = 0

        for category_name, foods in categories_data.items():
            # Create or get category
            category, created = FoodCategory.objects.get_or_create(
                category_name=category_name,
                defaults={'description': f'Category for {category_name} foods'}
            )
            if created:
                created_categories += 1

            # Create food
            for food_data in foods:
                food, created = Food.objects.get_or_create(
                    food_name=food_data['name'],
                    category=category,
                    defaults={
                        'calories_per_100g': food_data['calories'],
                        'unit': food_data['unit']
                    }
                )
                if created:
                    created_foods += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_categories} categories and {created_foods} foods'
            )
        )