from django import forms
from django.utils import timezone
from .models import Auction, Item, AuctionImage, Category


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ('title', 'description', 'category', 'condition')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class AuctionForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=True,
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=True,
    )

    class Meta:
        model = Auction
        fields = (
            'start_price', 'reserve_price', 'buy_now_price',
            'start_time', 'end_time', 'auto_extend',
        )
        widgets = {
            'start_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'reserve_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'buy_now_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def clean(self):
        cleaned = super().clean()
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')
        start_price = cleaned.get('start_price')
        buy_now_price = cleaned.get('buy_now_price')

        if start_time and end_time:
            if end_time <= start_time:
                raise forms.ValidationError("End time must be after start time.")
            if end_time - start_time < timezone.timedelta(minutes=5):
                raise forms.ValidationError("Auction must run for at least 5 minutes.")

        if start_price and buy_now_price:
            if buy_now_price <= start_price:
                raise forms.ValidationError("Buy-now price must be greater than start price.")

        return cleaned


class AuctionImageForm(forms.ModelForm):
    class Meta:
        model = AuctionImage
        fields = ('image', 'is_primary')


class AuctionSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Search')
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
    )
    condition = forms.ChoiceField(
        choices=[('', 'Any Condition')] + Item.CONDITION_CHOICES,
        required=False,
    )
    min_price = forms.DecimalField(required=False, min_value=0, decimal_places=2)
    max_price = forms.DecimalField(required=False, min_value=0, decimal_places=2)
    sort = forms.ChoiceField(
        choices=[
            ('ending_soon', 'Ending Soon'),
            ('newly_listed', 'Newly Listed'),
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low'),
            ('most_bids', 'Most Bids'),
        ],
        required=False,
        initial='ending_soon',
    )
