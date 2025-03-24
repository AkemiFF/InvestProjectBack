# admin_dashboard/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminLogViewSet, SystemSettingViewSet, StatisticViewSet,
    DashboardViewSet, UserManagementViewSet, ProjectManagementViewSet,
    CommentModerationViewSet
)

router = DefaultRouter()
router.register(r'logs', AdminLogViewSet)
router.register(r'settings', SystemSettingViewSet, basename='systemsetting')
router.register(r'statistics', StatisticViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'users', UserManagementViewSet, basename='usermanagement')
router.register(r'projects', ProjectManagementViewSet, basename='projectmanagement')
router.register(r'comments', CommentModerationViewSet, basename='commentmoderation')

urlpatterns = [
    path('', include(router.urls)),
]