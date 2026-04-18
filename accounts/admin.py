from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserRating


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = (
        'role', 'bio', 'phone', 'address', 'avatar',
        'is_verified', 'kyc_status', 'kyc_submitted_at',
        'trust_score', 'is_blacklisted', 'blacklist_reason',
        'total_sales', 'total_purchases',
    )
    readonly_fields = ('kyc_submitted_at', 'total_sales', 'total_purchases')


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'get_role', 'get_trust_score', 'get_kyc_status', 'date_joined'
    )

    @admin.display(description='Role')
    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except Exception:
            return '—'

    @admin.display(description='Trust')
    def get_trust_score(self, obj):
        try:
            return f"{obj.profile.trust_score:.0f}"
        except Exception:
            return '—'

    @admin.display(description='KYC')
    def get_kyc_status(self, obj):
        try:
            return obj.profile.get_kyc_status_display()
        except Exception:
            return '—'


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'role', 'kyc_status', 'trust_score', 'is_blacklisted',
        'is_verified', 'total_sales', 'total_purchases', 'created_at'
    )
    list_filter = ('role', 'is_verified', 'kyc_status', 'is_blacklisted')
    search_fields = ('user__username', 'user__email', 'phone')
    readonly_fields = ('created_at',)
    actions = ['approve_kyc', 'reject_kyc', 'blacklist_users', 'unblacklist_users']

    @admin.action(description='Approve KYC for selected users')
    def approve_kyc(self, request, queryset):
        updated = queryset.update(kyc_status='approved', is_verified=True)
        self.message_user(request, f"{updated} users KYC-approved.")

    @admin.action(description='Reject KYC for selected users')
    def reject_kyc(self, request, queryset):
        updated = queryset.update(kyc_status='rejected')
        self.message_user(request, f"{updated} users KYC-rejected.")

    @admin.action(description='Blacklist selected users')
    def blacklist_users(self, request, queryset):
        updated = queryset.update(is_blacklisted=True)
        self.message_user(request, f"{updated} users blacklisted.")

    @admin.action(description='Remove blacklist from selected users')
    def unblacklist_users(self, request, queryset):
        updated = queryset.update(is_blacklisted=False, blacklist_reason='')
        self.message_user(request, f"{updated} users un-blacklisted.")


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('rater', 'rated_user', 'score', 'created_at')
    list_filter = ('score',)
    search_fields = ('rater__username', 'rated_user__username')
