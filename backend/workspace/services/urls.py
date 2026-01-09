from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ServiceViewSet, BookingViewSet, ClientViewSet, InvoiceViewSet

app_name = 'services'

router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'bookings', BookingViewSet, basename='booking')  
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'invoices', InvoiceViewSet, basename='invoice')

urlpatterns = [
    path('', include(router.urls)),
    
    # Additional custom endpoints can be added here if needed
    # Example: path('reports/', views.generate_reports, name='reports'),
]