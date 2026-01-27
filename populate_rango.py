import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tango_with_django_project.settings')

import django
django.setup()

from rango.models import Category, Page


def populate():
    python_pages = [
        {'title': 'Official Python Tutorial', 'url': 'https://docs.python.org/3/tutorial/'},
        {'title': 'Python Package Index', 'url': 'https://pypi.org/'},
        {'title': 'Real Python', 'url': 'https://realpython.com/'},
    ]

    django_pages = [
        {'title': 'Official Django Tutorial', 'url': 'https://docs.djangoproject.com/en/stable/intro/tutorial01/'},
        {'title': 'Django Documentation', 'url': 'https://docs.djangoproject.com/en/stable/'},
        {'title': 'Django Packages', 'url': 'https://djangopackages.org/'},
    ]

    other_pages = [
        {'title': 'Mozilla Developer Network', 'url': 'https://developer.mozilla.org/'},
        {'title': 'Stack Overflow', 'url': 'https://stackoverflow.com/'},
        {'title': 'GitHub', 'url': 'https://github.com/'},
    ]

    cats = {
        'Python': {'pages': python_pages, 'views': 128, 'likes': 64},
        'Django': {'pages': django_pages, 'views': 64, 'likes': 32},
        'Other Frameworks': {'pages': other_pages, 'views': 32, 'likes': 16},
    }

    for cat_name, cat_data in cats.items():
        c = add_category(cat_name, views=cat_data['views'], likes=cat_data['likes'])
        for p in cat_data['pages']:
            add_page(c, p['title'], p['url'])

    # 打印验证
    for c in Category.objects.all():
        for p in Page.objects.filter(category=c):
            print(f'- {c} -> {p} ({p.url})')


def add_category(name, views=0, likes=0):
    c, _ = Category.objects.get_or_create(name=name)
    c.views = views
    c.likes = likes
    c.save()
    return c


def add_page(category, title, url, views=0):
    p, _ = Page.objects.get_or_create(category=category, title=title)
    p.url = url
    p.views = views
    p.save()
    return p


if __name__ == '__main__':
    print('Starting Rango population script...')
    populate()
