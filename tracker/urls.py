from django.urls import path
from django.shortcuts import redirect
from . import views

urlpatterns = [
    path('', lambda request: redirect('dashboard' if request.user.is_authenticated else 'login')),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('history/', views.history_view, name='history'),
    # Food Inventory Management
    path('foods/', views.food_list_view, name='food_list'),
    path('foods/add/', views.food_library_add_view, name='food_library_add'),
    path('foods/<int:id>/edit/', views.food_library_edit_view, name='food_library_edit'),
    path('foods/<int:id>/delete/', views.food_library_delete_view, name='food_library_delete'),
    # Dietary Record Management (New URL Structure)
    path('records/', views.record_list_view, name='record_list'),
    path('record/add/', views.add_food_view, name='add_food'),
    path('record/<int:id>/edit/', views.edit_food_view, name='edit_food'),
    path('record/<int:id>/delete/', views.delete_food_view, name='delete_food'),
    # Keep old URLs for compatibility
    path('food/add/', views.add_food_view, name='add_food_legacy'),
    path('food/<int:id>/edit/', views.edit_food_view, name='edit_food_legacy'),
    path('food/<int:id>/delete/', views.delete_food_view, name='delete_food_legacy'),
    # Food Classification Management
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/add/', views.category_add_view, name='category_add'),
    path('categories/<int:id>/edit/', views.category_edit_view, name='category_edit'),
    path('categories/<int:id>/delete/', views.category_delete_view, name='category_delete'),
]
