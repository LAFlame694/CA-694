from django.urls import path
from . import views

urlpatterns = [
    path('<int:chama_id>/', views.payment_view, name='payment'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path('stk-status/', views.stk_status_view, name='stk_status'),
    path('receipt/<int:transaction_id>/download/', views.download_receipt, name='download_receipt'),
]
