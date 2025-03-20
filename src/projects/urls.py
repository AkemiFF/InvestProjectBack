# projects/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, SectorViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'sectors', SectorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]