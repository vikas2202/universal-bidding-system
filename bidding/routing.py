from django.urls import re_path

from .consumers import BidConsumer

websocket_urlpatterns = [
    re_path(r'^ws/auction/(?P<auction_id>\d+)/$', BidConsumer.as_asgi()),
]

