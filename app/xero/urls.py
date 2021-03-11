from django.urls import path, include
from rest_framework.routers import DefaultRouter

from xero import views

router = DefaultRouter(trailing_slash=False)
router.register('xero', views.XeroViewSet)

app_name = 'xero'

urlpatterns = [
    path('', include(router.urls)),
    path('xero/auth/response', views.XeroAuthResponseView.as_view(), name="quickbooks_auth_response"),
    path('xero/auth/request', views.XeroAuthRequestView.as_view(), name="quickbooks_auth_request")
]