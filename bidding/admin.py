from django.contrib import admin
from .models import Bid, BidLog, ProxyBid


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'bidder', 'amount', 'max_amount', 'bid_time', 'is_auto_bid', 'is_winning', 'status', 'ip_address')
    list_filter = ('status', 'is_auto_bid', 'is_winning')
    search_fields = ('bidder__username', 'auction__item__title')
    readonly_fields = ('bid_time', 'ip_address')
    date_hierarchy = 'bid_time'

    def has_delete_permission(self, request, obj=None):
        return False  # Bid history is immutable


@admin.register(BidLog)
class BidLogAdmin(admin.ModelAdmin):
    list_display = ('auction', 'event_type', 'description', 'timestamp')
    list_filter = ('event_type',)
    search_fields = ('auction__item__title', 'description')
    readonly_fields = ('timestamp',)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProxyBid)
class ProxyBidAdmin(admin.ModelAdmin):
    list_display = ('user', 'auction', 'max_amount', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'auction__item__title')
