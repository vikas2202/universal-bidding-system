from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('auctions.urls', namespace='auctions')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('bidding/', include('bidding.urls', namespace='bidding')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('fraud/', include('fraud_detection.urls', namespace='fraud_detection')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'auctions.views.handler404'
handler500 = 'auctions.views.handler500'
