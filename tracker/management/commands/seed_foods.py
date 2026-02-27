"""
Management command to pre-populate common foods into the database.
"""
from django.core.management.base import BaseCommand
from tracker.models import FoodCategory, Food


class Command(BaseCommand):
    help = 'Pre-populate common foods into the database'

    def handle(self, *args, **options):
        # 定义食物分类和食物数据
        categories_data = {
            '主食': [
                {'name': '米饭', 'calories': 130, 'unit': '克'},
                {'name': '面条', 'calories': 110, 'unit': '克'},
                {'name': '馒头', 'calories': 223, 'unit': '克'},
                {'name': '面包', 'calories': 265, 'unit': '克'},
                {'name': '饺子', 'calories': 210, 'unit': '克'},
                {'name': '包子', 'calories': 227, 'unit': '克'},
                {'name': '粥', 'calories': 46, 'unit': '克'},
                {'name': '薯条', 'calories': 312, 'unit': '克'},
                {'name': '披萨', 'calories': 266, 'unit': '克'},
            ],
            '肉类': [
                {'name': '鸡腿', 'calories': 200, 'unit': '克'},
                {'name': '鸡胸肉', 'calories': 165, 'unit': '克'},
                {'name': '猪肉', 'calories': 242, 'unit': '克'},
                {'name': '牛肉', 'calories': 250, 'unit': '克'},
                {'name': '羊肉', 'calories': 294, 'unit': '克'},
                {'name': '鸭肉', 'calories': 337, 'unit': '克'},
                {'name': '鱼', 'calories': 136, 'unit': '克'},
                {'name': '虾', 'calories': 85, 'unit': '克'},
                {'name': '汉堡肉饼', 'calories': 295, 'unit': '克'},
            ],
            '蔬菜': [
                {'name': '西兰花', 'calories': 34, 'unit': '克'},
                {'name': '胡萝卜', 'calories': 41, 'unit': '克'},
                {'name': '西红柿', 'calories': 18, 'unit': '克'},
                {'name': '黄瓜', 'calories': 15, 'unit': '克'},
                {'name': '菠菜', 'calories': 23, 'unit': '克'},
                {'name': '生菜', 'calories': 15, 'unit': '克'},
                {'name': '青椒', 'calories': 31, 'unit': '克'},
                {'name': '土豆', 'calories': 77, 'unit': '克'},
                {'name': '茄子', 'calories': 25, 'unit': '克'},
            ],
            '水果': [
                {'name': '苹果', 'calories': 52, 'unit': '克'},
                {'name': '香蕉', 'calories': 89, 'unit': '克'},
                {'name': '橙子', 'calories': 47, 'unit': '克'},
                {'name': '葡萄', 'calories': 67, 'unit': '克'},
                {'name': '西瓜', 'calories': 30, 'unit': '克'},
                {'name': '草莓', 'calories': 32, 'unit': '克'},
                {'name': '芒果', 'calories': 60, 'unit': '克'},
                {'name': '梨', 'calories': 57, 'unit': '克'},
                {'name': '桃子', 'calories': 39, 'unit': '克'},
            ],
            '奶制品': [
                {'name': '牛奶', 'calories': 61, 'unit': '毫升'},
                {'name': '酸奶', 'calories': 63, 'unit': '克'},
                {'name': '奶酪', 'calories': 402, 'unit': '克'},
                {'name': '黄油', 'calories': 717, 'unit': '克'},
                {'name': '豆浆', 'calories': 33, 'unit': '毫升'},
            ],
            '零食': [
                {'name': '薯片', 'calories': 536, 'unit': '克'},
                {'name': '饼干', 'calories': 488, 'unit': '克'},
                {'name': '巧克力', 'calories': 546, 'unit': '克'},
                {'name': '坚果', 'calories': 654, 'unit': '克'},
                {'name': '糖果', 'calories': 400, 'unit': '克'},
                {'name': '爆米花', 'calories': 387, 'unit': '克'},
            ],
            '饮料': [
                {'name': '可乐', 'calories': 38, 'unit': '毫升'},
                {'name': '橙汁', 'calories': 45, 'unit': '毫升'},
                {'name': '咖啡', 'calories': 2, 'unit': '毫升'},
                {'name': '茶', 'calories': 1, 'unit': '毫升'},
            ],
            '快餐': [
                {'name': '汉堡', 'calories': 295, 'unit': '克'},
                {'name': '炸鸡', 'calories': 307, 'unit': '克'},
                {'name': '热狗', 'calories': 290, 'unit': '克'},
                {'name': '三明治', 'calories': 250, 'unit': '克'},
                {'name': '墨西哥卷饼', 'calories': 226, 'unit': '克'},
            ],
        }

        created_categories = 0
        created_foods = 0

        for category_name, foods in categories_data.items():
            # 创建或获取分类
            category, created = FoodCategory.objects.get_or_create(
                category_name=category_name,
                defaults={'description': f'{category_name}类食品'}
            )
            if created:
                created_categories += 1

            # 创建食物
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
                f'成功创建 {created_categories} 个分类和 {created_foods} 个食物'
            )
        )
