from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserRating


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'total_sales', 'total_purchases', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('user__username', 'user__email', 'phone')


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('rater', 'rated_user', 'score', 'created_at')
    list_filter = ('score',)
    search_fields = ('rater__username', 'rated_user__username')
