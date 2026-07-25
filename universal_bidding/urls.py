from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from bidding import views as bidding_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('auctions.urls', namespace='auctions')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('bidding/', include('bidding.urls', namespace='bidding')),
    path('api/auctions/<int:pk>/time/', bidding_views.auction_time_api, name='auction_time_api'),
    path('api/auctions/<int:pk>/min-bid/', bidding_views.auction_min_bid_api, name='auction_min_bid_api'),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('fraud/', include('fraud_detection.urls', namespace='fraud_detection')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'auctions.views.handler404'
handler500 = 'auctions.views.handler500'
