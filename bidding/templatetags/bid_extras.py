from django import template

register = template.Library()


@register.filter
def mask_amount(amount, user_is_owner=False):
    """Show full amount to bid owner, masked to others."""
    if user_is_owner:
        return f"${float(amount):,.2f}"
    return "***"


@register.filter
def bid_status_badge(bid):
    badges = {
        'active': 'primary',
        'outbid': 'warning',
        'won': 'success',
        'cancelled': 'danger',
    }
    color = badges.get(bid.status, 'secondary')
    label = bid.get_status_display()
    return f'<span class="badge bg-{color}">{label}</span>'
