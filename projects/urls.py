# projects/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet, SectorViewSet

router = DefaultRouter()
router.register(r'', ProjectViewSet)


urlpatterns = [
    path('', include(router.urls)),
]