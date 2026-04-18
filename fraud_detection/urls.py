from django.urls import path
from . import views

app_name = 'fraud_detection'

urlpatterns = [
    path('dashboard/', views.fraud_dashboard, name='dashboard'),
    path('user/<int:user_id>/', views.user_risk_profile, name='user_risk'),
]
