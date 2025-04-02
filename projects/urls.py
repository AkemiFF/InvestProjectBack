# projects/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet, SectorViewSet

router = DefaultRouter()
router.register(r'', ProjectViewSet)
router.register(r'sectors', SectorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]