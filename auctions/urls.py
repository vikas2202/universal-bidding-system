from django.urls import path
from . import views

app_name = 'auctions'

urlpatterns = [
    path('', views.home, name='home'),
    path('auctions/', views.auction_list, name='list'),
    path('auctions/<int:pk>/', views.auction_detail, name='detail'),
    path('auctions/create/', views.create_auction, name='create'),
    path('auctions/<int:pk>/end/', views.end_auction, name='end_auction'),
    path('auctions/<int:pk>/buy-now/', views.buy_now, name='buy_now'),
    path('my-auctions/', views.my_auctions, name='my_auctions'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('watchlist/add/<int:pk>/', views.add_to_watchlist, name='add_watchlist'),
    path('watchlist/remove/<int:pk>/', views.remove_from_watchlist, name='remove_watchlist'),
]
