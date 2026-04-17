from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def time_remaining_display(auction):
    remaining = auction.time_remaining()
    if remaining is None:
        return "Ended"
    total_seconds = int(remaining.total_seconds())
    if total_seconds <= 0:
        return "Ending..."
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m {seconds}s"


@register.filter
def currency(value):
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return value


@register.simple_tag
def auction_status_badge(auction):
    badges = {
        'active': 'success',
        'ended': 'secondary',
        'draft': 'warning',
        'cancelled': 'danger',
    }
    color = badges.get(auction.status, 'secondary')
    return f'<span class="badge bg-{color}">{auction.get_status_display()}</span>'


@register.filter
def subtract(value, arg):
    try:
        return value - arg
    except Exception:
        return value


@register.filter
def percentage(value, total):
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ZeroDivisionError, TypeError, ValueError):
        return 0
