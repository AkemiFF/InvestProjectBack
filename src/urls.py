from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from projects.views import SectorViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'api/sectors', SectorViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api/', include('users.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/comments/', include('comments.urls')),
    path('api/messaging/', include('messaging.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/investments/', include('investments.urls')),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/admin/', include('admin_dashboard.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)