# admin_dashboard/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AdminLogViewSet, CommentModerationViewSet,
                    DashboardViewSet, ProjectDeletionViewSet,
                    ProjectManagementViewSet, StatisticViewSet,
                    SystemSettingViewSet, UserManagementViewSet)

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
    path('delete/project/<int:pk>/', ProjectDeletionViewSet.as_view({'delete': 'delete_project'}), name='delete-project'),
    path('approuve/project/<int:pk>/', ProjectDeletionViewSet.as_view({'post': 'approuve_project'}), name='approuve-project'),
]