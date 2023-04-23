from django.urls import path
from . import views

app_name = "restaurant"

urlpatterns = [
    path('', views.RestaurantViewSet.as_view({'get': 'list', 'post': 'create'}), name='restaurant-list-create'),
    path('order_by_ratings/', views.RestaurantViewSet.as_view({'get': 'order_by_ratings'}), name='order-restaurant-list'),
    path('<uuid:pk>/', views.RestaurantViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='restaurant-retrieve-update-destroy'),
    path('vote/', views.VoteViewSet.as_view({'post': 'post'}), name='vote-create'),
]
