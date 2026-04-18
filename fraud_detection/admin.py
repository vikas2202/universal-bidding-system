from django.contrib import admin
from .models import FraudFlag, BidderRiskProfile


@admin.register(FraudFlag)
class FraudFlagAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'flag_type', 'severity', 'auction', 'ip_address',
        'is_reviewed', 'created_at',
    )
    list_filter = ('flag_type', 'severity', 'is_reviewed')
    search_fields = ('user__username', 'description', 'ip_address')
    readonly_fields = ('created_at', 'ip_address')
    date_hierarchy = 'created_at'
    actions = ['mark_reviewed']

    @admin.action(description='Mark selected flags as reviewed')
    def mark_reviewed(self, request, queryset):
        updated = queryset.filter(is_reviewed=False).update(
            is_reviewed=True, reviewed_by=request.user
        )
        self.message_user(request, f"{updated} flag(s) marked as reviewed.")

    def has_delete_permission(self, request, obj=None):
        return False  # Fraud flags are part of the audit trail


@admin.register(BidderRiskProfile)
class BidderRiskProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'total_flags', 'get_overall_risk',
        'collusion_score', 'anomaly_score', 'shill_score',
        'last_flagged_at', 'updated_at',
    )
    search_fields = ('user__username',)
    readonly_fields = ('updated_at', 'last_flagged_at', 'get_overall_risk')
    ordering = ('-collusion_score',)

    @admin.display(description='Overall Risk')
    def get_overall_risk(self, obj):
        return obj.overall_risk
