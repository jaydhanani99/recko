from django.urls import path, include
from rest_framework.routers import DefaultRouter

from quickbooks import views

router = DefaultRouter(trailing_slash=False)
router.register('quickbooks', views.QuickbooksViewSet)

app_name = 'quickbooks'

urlpatterns = [
    path('', include(router.urls)),
    path('quickbooks/auth/response', views.QuickbooksAuthResponseView.as_view(), name="quickbooks_auth_response"),
    path('quickbooks/auth/request', views.QuickbooksAuthRequestView.as_view(), name="quickbooks_auth_request")
]