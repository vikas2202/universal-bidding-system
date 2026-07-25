from django.urls import path
from . import views

app_name = 'bidding'

urlpatterns = [
    path('place/<int:pk>/', views.place_bid, name='place_bid'),
    path('history/<int:pk>/', views.bid_history, name='bid_history'),
    path('api/status/<int:pk>/', views.auction_status_api, name='auction_status'),
    path('api/auctions/<int:pk>/time/', views.auction_time_api, name='auction_time'),
    path('api/auctions/<int:pk>/min-bid/', views.auction_min_bid_api, name='auction_min_bid'),
]
