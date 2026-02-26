"""URL configuration for expense management API."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExpenseReportViewSet, ReceiptViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'reports', ExpenseReportViewSet, basename='report')
router.register(r'receipts', ReceiptViewSet, basename='receipt')

urlpatterns = [
    # Health check endpoint
    path(
        'health/',
        lambda request: __import__('django.http', fromlist=['JsonResponse']).JsonResponse({'status': 'ok'}),
        name='health-check'
    ),
    # Include all router-generated URLs
    path('', include(router.urls)),
]
