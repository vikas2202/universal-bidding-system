from django.contrib import admin
from .models import Category, Item, Auction, AuctionImage, Watchlist


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'condition', 'created_at')
    list_filter = ('condition', 'category')
    search_fields = ('title', 'description')


class AuctionImageInline(admin.TabularInline):
    model = AuctionImage
    extra = 1


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'item', 'seller', 'status', 'start_price', 'current_price',
        'current_winner', 'start_time', 'end_time', 'view_count'
    )
    list_filter = ('status', 'item__category', 'auto_extend')
    search_fields = ('item__title', 'seller__username')
    readonly_fields = ('view_count', 'watchlist_count', 'created_at', 'updated_at')
    inlines = [AuctionImageInline]
    date_hierarchy = 'start_time'


@admin.register(AuctionImage)
class AuctionImageAdmin(admin.ModelAdmin):
    list_display = ('auction', 'is_primary', 'order')
    list_filter = ('is_primary',)


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'auction', 'added_at')
    search_fields = ('user__username',)
