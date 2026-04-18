from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from .models import FraudFlag, BidderRiskProfile


@staff_member_required
def fraud_dashboard(request):
    """Admin-only dashboard summarising recent fraud flags."""
    recent_flags = (
        FraudFlag.objects.select_related('user', 'auction', 'bid')
        .filter(is_reviewed=False)
        .order_by('-created_at')[:50]
    )

    flag_summary = (
        FraudFlag.objects.values('flag_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    high_risk_users = (
        BidderRiskProfile.objects.select_related('user')
        .filter(total_flags__gte=1)
        .order_by('-collusion_score', '-anomaly_score')[:20]
    )

    context = {
        'recent_flags': recent_flags,
        'flag_summary': flag_summary,
        'high_risk_users': high_risk_users,
    }
    return render(request, 'fraud_detection/dashboard.html', context)


@staff_member_required
def user_risk_profile(request, user_id):
    """Show the risk profile and all flags for a single user."""
    from django.contrib.auth.models import User
    user = get_object_or_404(User, pk=user_id)
    risk_profile = BidderRiskProfile.objects.filter(user=user).first()
    flags = FraudFlag.objects.filter(user=user).select_related('auction', 'bid').order_by('-created_at')
    context = {
        'profile_user': user,
        'risk_profile': risk_profile,
        'flags': flags,
    }
    return render(request, 'fraud_detection/user_risk.html', context)
